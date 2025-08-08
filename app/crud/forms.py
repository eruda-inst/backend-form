from fastapi import Depends
from sqlalchemy.orm import Session, joinedload
from app import models, schemas
from uuid import uuid4, UUID
from app.dependencies.auth import get_current_user

def criar_formulario(db: Session, dados: schemas.FormularioCreate, usuario: models.Usuario = Depends(get_current_user)):
    formulario = models.Formulario(
        id=uuid4(),
        titulo=dados.titulo,
        descricao=dados.descricao,
        criado_por_id=usuario.id
    )
    db.add(formulario)
    db.flush()

    for ordem, pergunta_data in enumerate(dados.perguntas):
        pergunta = models.Pergunta(
            id=uuid4(),
            formulario_id=formulario.id,
            texto=pergunta_data.texto,
            tipo=pergunta_data.tipo,
            obrigatoria=pergunta_data.obrigatoria,
            ordem_exibicao=pergunta_data.ordem_exibicao or ordem,
            escala_min=pergunta_data.escala_min,
            escala_max=pergunta_data.escala_max
        )
        db.add(pergunta)

        if pergunta_data.tipo == "multipla_escolha":
            for idx, opcao in enumerate(pergunta_data.opcoes or []):
                db.add(models.Opcao(
                    id=uuid4(),
                    pergunta_id=pergunta.id,
                    texto=opcao.texto,
                    ordem=opcao.ordem or idx
                ))

    db.commit()
    db.refresh(formulario)
    return formulario


def listar_formularios(db: Session, incluir_inativos: bool = False):
    query = db.query(models.Formulario)
    if not incluir_inativos:
        query = query.filter(models.Formulario.ativo.is_(True))
    return query.all()

def buscar_formulario_por_id(db: Session, formulario_id: str):
    return (
        db.query(models.Formulario)
        .options(joinedload(models.Formulario.perguntas))
        .filter(models.Formulario.id == formulario_id)
        .first()
    )

def atualizar_formulario_parcial(db: Session, payload: dict):
    try:
        formulario_id = UUID(payload.get("formulario_id"))
        print("Formulário_id: ", formulario_id)
    except ValueError:
        import logging
        logging.exception("Erro ao converter UUID")
        return None
    formulario = db.query(models.Formulario).options(
        joinedload(models.Formulario.perguntas)
    ).filter(models.Formulario.id == formulario_id).first()
    if not formulario or not formulario.ativo:
        return None

    if payload.get("titulo"):
        formulario.titulo = payload["titulo"]
    if payload.get("descricao"):
        formulario.descricao = payload["descricao"]

    for p in payload.get("perguntas_adicionadas", []):
        nova = models.Pergunta(
            texto=p.get("texto"),
            tipo=p.get("tipo"),
            obrigatoria=p.get("obrigatoria", True),
            ordem_exibicao=p.get("ordem_exibicao"),
            escala_min=p.get("escala_min"),
            escala_max=p.get("escala_max"),
        )
        formulario.perguntas.append(nova)
        db.commit()
        db.refresh(formulario)


    for p in payload.get("perguntas_editadas", []):
        pergunta = db.query(models.Pergunta).filter(models.Pergunta.id == p["id"]).first()
        if pergunta:
            for campo in ["texto", "tipo", "obrigatoria", "ordem_exibicao", "escala_min", "escala_max"]:
                if campo in p:
                    setattr(pergunta, campo, p[campo])

    for pergunta_id in payload.get("perguntas_removidas", []):
        pergunta = db.query(models.Pergunta).filter(models.Pergunta.id == pergunta_id).first()
        if pergunta:
            pergunta.ativa = False

    db.commit()
    db.refresh(formulario)
    print("Perguntas após commit:", [p.texto for p in formulario.perguntas if p.ativa])
    from pprint import pprint

    formulario = db.query(models.Formulario).options(
        joinedload(models.Formulario.perguntas)
    ).filter(models.Formulario.id == formulario_id).first()

    pprint([p.texto for p in formulario.perguntas])

    return formulario

def adicionar_pergunta(db: Session, dados: dict) -> models.Pergunta:
    nova = models.Pergunta(**dados)
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova