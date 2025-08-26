
# app/crud/respostas.py
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status
from app import models, schemas

TIPO_NPS = "nps"
TIPO_ME = "multipla_escolha"
TIPO_TX_SIM = "texto_simples"
TIPO_TX_LONG = "texto_longo"

def _one_value(i):
    presentes = [v is not None and (str(v).strip() != "") for v in
                 [i.valor_texto, i.valor_numero, i.valor_opcao_id, i.valor_opcao_texto]]
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

    elif t in {models.TipoPergunta.texto_simples, models.TipoPergunta.texto_longo, models.TipoPergunta.data}:
        if not item.valor_texto or not item.valor_texto.strip():
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: texto requerido")

    elif t == models.TipoPergunta.numero:
        if item.valor_numero is None:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: número requerido")

    elif t == models.TipoPergunta.caixa_selecao:
        if not item.valor_opcao_id and not item.valor_opcao_texto:
            raise HTTPException(status_code=422, detail=f"Pergunta {pergunta.id}: caixa_selecao requer ao menos uma opção")
        if item.valor_opcao_id:
            ids_validos = {o.id for o in pergunta.opcoes}
            if item.valor_opcao_id not in ids_validos:
                raise HTTPException(status_code=422, detail=f"Opção não pertence à pergunta {pergunta.id}")

    else:
        raise HTTPException(status_code=422, detail=f"Tipo não suportado: {t}")

def _garantir_obrigatoria(pergunta: "models.Pergunta", item: schemas.RespostaItemCreate | None) -> None:
    """Garante que perguntas obrigatórias tenham item válido presente."""
    if not pergunta.obrigatoria:
        return
    if item is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Pergunta obrigatória ausente: {pergunta.id}")

def criar(db: Session, payload: schemas.RespostaCreate) -> models.Resposta:
    """Cria uma resposta completa de um formulário com validação por tipo de pergunta."""
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

    itens_in = {i.pergunta_id: i for i in payload.itens}
    for p in perguntas:
        item = itens_in.get(p.id)
        _garantir_obrigatoria(p, item)
        if item:
            _validar_item_por_tipo(p, item)

    resp = models.Resposta(
        formulario_id=form.id,
        origem_ip=payload.origem_ip,
        user_agent=payload.user_agent,
        meta=payload.meta,
    )
    db.add(resp)
    db.flush()

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
            )
        )
    db.add_all(itens_out)
    db.commit()
    db.refresh(resp)
    return resp

def listar_por_formulario(db: Session, formulario_id: UUID) -> List[models.Resposta]:
    """Lista respostas de um formulário."""
    return (
        db.query(models.Resposta)
        .filter(models.Resposta.formulario_id == formulario_id)
        .order_by(models.Resposta.criado_em.desc())
        .all()
    )

def buscar_por_id(db: Session, resposta_id: UUID) -> models.Resposta | None:
    """Busca resposta pelo ID."""
    return db.query(models.Resposta).filter(models.Resposta.id == resposta_id).first()

def deletar(db: Session, resposta_id: UUID) -> bool:
    """Remove uma resposta e seus itens."""
    resp = db.query(models.Resposta).filter(models.Resposta.id == resposta_id).first()
    if not resp:
        return False
    db.delete(resp)
    db.commit()
    return True
