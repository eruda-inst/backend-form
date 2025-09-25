
# app/crud/respostas.py
import re
from collections import defaultdict
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app import models, schemas
from app.core.identidade import normalizar_email, normalizar_telefone, normalizar_cpf


TIPO_NPS = "nps"
TIPO_ME = "multipla_escolha"
TIPO_TX_SIM = "texto_simples"
TIPO_TX_LONG = "texto_longo"

IDENT_NORMALIZERS = {
    "email": lambda v: (v or "").strip().lower() or None,
    "telefone": lambda v: re.sub(r"\D+", "", v or "") or None,  # use a sua se já existir
    "cpf": normalizar_cpf,
}

MODE_PRIORITY = {
    "none": [],
    "email": ["email"],
    "phone": ["telefone"],
    "cpf": ["cpf"],
    "email_or_phone": ["email", "telefone"],
    "email_or_cpf": ["email", "cpf"],
    "phone_or_cpf": ["telefone", "cpf"],
    "email_or_phone_or_cpf": ["email", "telefone", "cpf"],
}

def resolver_identificador_unico(modo: str, raw: dict) -> dict:
    """
    Retorna {'email':..., 'telefone':..., 'cpf':...} com apenas 1 preenchido conforme prioridade do modo.
    """
    modo = (modo or "none").lower()
    priorities = MODE_PRIORITY.get(modo)
    if priorities is None:
        raise HTTPException(400, "Configuração inválida do formulário.")

    normalized = {k: IDENT_NORMALIZERS[k](raw.get(k)) for k in IDENT_NORMALIZERS}

    if modo == "none":
        return {"email": None, "telefone": None, "cpf": None}

    for key in priorities:
        if normalized.get(key):
            out = {"email": None, "telefone": None, "cpf": None}
            out[key] = normalized[key]
            return out

    raise HTTPException(400, "Informe o identificador requerido pelo formulário.")

def _extrair_identificadores_do_payload(perguntas_map, itens_por_pergunta):
    email = telefone = cpf = None
    for pid, grupo in itens_por_pergunta.items():
        p = perguntas_map.get(pid)
        if not p: 
            continue
        t = (getattr(p, "tipo", "") or "").lower()
        for it in grupo:
            v = getattr(it, "valor_texto", None)
            if email is None and t == "email": email = v
            if telefone is None and t == "telefone": telefone = v
            if cpf is None and t == "cpf": cpf = v
    return {"email": email, "telefone": telefone, "cpf": cpf}


def _one_value(i):
    presentes = [v is not None and (str(v).strip() != "") for v in
                 [i.valor_texto, i.valor_numero, i.valor_opcao_id, i.valor_opcao_texto, i.valor_data]]
    return sum(presentes) == 1

def _validar_item_por_tipo(pergunta: "models.Pergunta", item: schemas.RespostaItemCreate) -> None:
    if not _one_value(item):
        raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: envie exatamente 1 campo de valor")

    t = pergunta.tipo
    if t == models.TipoPergunta.nps:
        if item.valor_numero is None:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: NPS requer valor_numero")
        mn = pergunta.escala_min if pergunta.escala_min is not None else 0
        mx = pergunta.escala_max if pergunta.escala_max is not None else 10
        if not (mn <= item.valor_numero <= mx):
            raise HTTPException(status_code=422, detail=f"NPS fora da faixa [{mn},{mx}] na pergunta {pergunta.id}")

    elif t == models.TipoPergunta.multipla_escolha:
        if not item.valor_opcao_id and not item.valor_opcao_texto:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: múltipla escolha requer opção")
        if item.valor_opcao_id:
            ids_validos = {o.id for o in pergunta.opcoes}
            if item.valor_opcao_id not in ids_validos:
                raise HTTPException(status_code=422, detail=f"Opção não pertence à pergunta {pergunta.id}")

    elif t in {models.TipoPergunta.texto_simples, models.TipoPergunta.texto_longo}:
        if not item.valor_texto or not item.valor_texto.strip():
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: texto requerido")

    elif t == models.TipoPergunta.data:
        if item.valor_data is None:
          raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: data requerida")

    elif t == models.TipoPergunta.numero:
        if item.valor_numero is None:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: número requerido")

    elif t == models.TipoPergunta.caixa_selecao:
        if not item.valor_opcao_id and not item.valor_opcao_texto:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: caixa_selecao requer opção")
        if item.valor_opcao_id:
            ids_validos = {o.id for o in pergunta.opcoes}
            if item.valor_opcao_id not in ids_validos:
                raise HTTPException(status_code=422, detail=f"Opção não pertence à pergunta {pergunta.id}")
            
    elif t == models.TipoPergunta.telefone:
        if not item.valor_texto:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: telefone é obrigatório")
        v = item.valor_texto.strip()
        # digits = re.sub(r"\D+", "", v)
        if not normalizar_telefone(v):
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: telefone inválido")
    
    elif t == models.TipoPergunta.email:
        if not item.valor_texto:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: e-mail é obrigatório")
        v = item.valor_texto.strip().lower()
        if not normalizar_email(v):
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: e-mail inválido")
    
    elif t == models.TipoPergunta.cpf:
        if not item.valor_texto:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: CPF é obrigatório")
        v = item.valor_texto.strip()
        if not normalizar_cpf(v):
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: CPF inválido")

        
    else:
        raise HTTPException(status_code=422, detail=f"Tipo não suportado: {t}")

def _garantir_obrigatoria(pergunta: "models.Pergunta", item: schemas.RespostaItemCreate | None) -> None:
    """Garante que perguntas obrigatórias tenham item válido presente."""
    if not pergunta.obrigatoria:
        return
    if item is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Pergunta obrigatória ausente: {pergunta.id}")

def criar(db: Session, payload: schemas.RespostaCreate) -> models.Resposta:
    """Cria uma resposta completa de um formulário com validação por tipo de pergunta e unicidade por e-mail/telefone."""
    form = db.query(models.Formulario).filter(models.Formulario.id == payload.formulario_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    if not form.recebendo_respostas:
        raise HTTPException(status_code=403, detail="Formulário não está recebendo aceita respostas")

    perguntas = (
        db.query(models.Pergunta)
        .options(selectinload(models.Pergunta.opcoes))
        .filter(models.Pergunta.formulario_id == form.id, models.Pergunta.ativa == True)
        .all()
    )

    perguntas_map = {p.id: p for p in perguntas}
    itens_por_pergunta = defaultdict(list)
    for i in payload.itens:
        itens_por_pergunta[i.pergunta_id].append(i)

    for p in perguntas:
        grupo = itens_por_pergunta.get(p.id, [])
        _garantir_obrigatoria(p, grupo[0] if grupo else None)
        for item in grupo:
            _validar_item_por_tipo(p, item)

    raw_ids = _extrair_identificadores_do_payload(perguntas_map, itens_por_pergunta)
    ids = resolver_identificador_unico(getattr(form, "unico_por_chave_modo", "none"), raw_ids)


    resp = models.Resposta(
        formulario_id=form.id,
        origem_ip=payload.origem_ip,
        user_agent=payload.user_agent,
        meta=payload.meta,
        email=ids["email"],
        telefone=ids["telefone"],
        cpf=ids["cpf"],
    )
    db.add(resp)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        ident = resp.email or resp.telefone or resp.cpf
        raise HTTPException(status_code=409, detail= f"Este identificador já respondeu a este formulário: {ident}")

    itens_out: List[models.RespostaItem] = []
    for i in payload.itens:
        if i.pergunta_id not in perguntas_map:
            raise HTTPException(status_code=422, detail=f"Pergunta não pertence ao formulário: {i.pergunta_id}")
        itens_out.append(
            models.RespostaItem(
                resposta_id=resp.id,
                pergunta_id=i.pergunta_id,
                valor_texto=i.valor_texto,
                valor_numero=i.valor_numero,
                valor_opcao_id=i.valor_opcao_id,
                valor_opcao_texto=i.valor_opcao_texto,
                valor_data=i.valor_data,
            )
        )
    db.add_all(itens_out)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este identificador já respondeu a este formulário.")

    db.refresh(resp)
    created_resp = (
        db.query(models.Resposta)
        .options(selectinload(models.Resposta.itens).selectinload(models.RespostaItem.valor_opcao))
        .filter(models.Resposta.id == resp.id)
        .one()
    )
    return created_resp

def listar_por_formulario(db: Session, formulario_id: UUID, grupo_id: UUID) -> List[models.Resposta]:
    """Lista respostas de um formulário somente se o grupo do usuário tiver permissão de ver o formulário."""
    tem_perm = (
        db.query(models.FormularioPermissao.id)
        .filter(
            models.FormularioPermissao.formulario_id == formulario_id,
            models.FormularioPermissao.grupo_id == grupo_id,
            models.FormularioPermissao.pode_ver.is_(True),
        )
        .first()
    )
    if not tem_perm:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para ver as respostas deste formulário")

    return (
        db.query(models.Resposta)
        .options(selectinload(models.Resposta.itens).selectinload(models.RespostaItem.valor_opcao))
        .filter(models.Resposta.formulario_id == formulario_id)
        .order_by(models.Resposta.criado_em.desc())
        .all()
    )

def buscar_por_id(db: Session, resposta_id: UUID) -> models.Resposta | None:
    """Busca resposta pelo ID."""
    return db.query(models.Resposta).options(
        selectinload(models.Resposta.itens).selectinload(models.RespostaItem.valor_opcao)
    ).filter(models.Resposta.id == resposta_id).first()

def deletar(db: Session, resposta_id: UUID) -> bool:
    """Remove uma resposta e seus itens."""
    resp = db.query(models.Resposta).filter(models.Resposta.id == resposta_id).first()
    if not resp:
        return False
    db.delete(resp)
    db.commit()
    return True

