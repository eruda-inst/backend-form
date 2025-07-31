from fastapi import HTTPException
from uuid import UUID
from sqlalchemy.orm import Session
from app import models, schemas

def existe_grupo_admin(db: Session) -> bool:
    return db.query(models.Grupo).filter(models.Grupo.nome == "admin").first() is not None

def get_grupo_admin_id(db: Session) -> UUID:
    grupo = db.query(models.Grupo).filter(models.Grupo.nome == "admin").first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo admin não encontrado")
    return grupo.id

def criar_grupo(db: Session, grupo: schemas.GrupoCreate) -> models.Grupo:
    grupo_existente = db.query(models.Grupo).filter(models.Grupo.nome == grupo.nome).first()
    if grupo_existente:
        raise HTTPException(status_code=400, detail="Nome de grupo já cadastrado")

    novo_grupo = models.Grupo(nome=grupo.nome)
    db.add(novo_grupo)
    db.commit()
    db.refresh(novo_grupo)
    return novo_grupo
