
# app/crud/respostas.py
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import models, schemas

TIPO_NPS = "nps"
TIPO_ME = "multipla_escolha"
TIPO_TX_SIM = "texto_simples"
TIPO_TX_LONG = "texto_longo"

def _validar_item_por_tipo(pergunta: "models.Pergunta", item: schemas.RespostaItemCreate) -> None:
    """Valida um item de resposta conforme o tipo da pergunta."""
    tipo = (pergunta.tipo or "").lower()
    if tipo == TIPO_NPS:
        if item.valor_numero is None or not (0 <= item.valor_numero <= 10):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Pergunta {pergunta.id}: NPS requer valor_numero entre 0 e 10")
    elif tipo == TIPO_ME:
        if not item.valor_opcao_id and not item.valor_opcao_texto:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Pergunta {pergunta.id}: múltipla escolha requer valor_opcao_id ou valor_opcao_texto")
    elif tipo in {TIPO_TX_SIM, TIPO_TX_LONG}:
        if not item.valor_texto or not item.valor_texto.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Pergunta {pergunta.id}: texto requerido")
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Tipo de pergunta não suportado: {tipo}")

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

    perguntas = db.query(models.Pergunta).filter(models.Pergunta.formulario_id == form.id).all()
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
