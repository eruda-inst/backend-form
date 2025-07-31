from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from app import models, schemas, crud
from app.database import get_db
from uuid import UUID
from app.models.permissao import Permissao
from typing import List
from app.dependencies.permissoes import require_permission




router = APIRouter(prefix="/grupos", tags=["Grupos"])
# 
@router.get("/", response_model=List[schemas.GrupoComPermissoesResponse], dependencies=[require_permission('grupos:ver')])
def listar_grupos_com_permissoes(db: Session = Depends(get_db)):
    grupos = db.query(models.Grupo).options(selectinload(models.Grupo.permissoes)).all()
    return grupos

@router.get("/grupo-admin-id")
def grupo_admin_id(db: Session = Depends(get_db)):
    grupo_id = crud.get_grupo_admin_id(db)
    return {"grupo_id": str(grupo_id)}


@router.post("/", response_model=schemas.GrupoResponse, status_code=status.HTTP_201_CREATED)
def criar_grupo(grupo: schemas.GrupoCreate, db: Session = Depends(get_db)):
    novo_grupo = crud.criar_grupo(db, grupo)
    return novo_grupo


@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[require_permission('grupos:deletar')])
def deletar_grupo(grupo_id: UUID, db: Session = Depends(get_db)):
    grupo = db.query(models.Grupo).filter(models.Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    if grupo.nome == "admin":
        raise HTTPException(status_code=403, detail="O grupo admin não pode ser deletado")

    usuarios_vinculados = db.query(models.Usuario).filter(models.Usuario.grupo_id == grupo.id).all()
    if usuarios_vinculados:
        usuarios_data = [
            {"id": u.id, "nome": u.nome, "email": u.email}
            for u in usuarios_vinculados
        ]
        raise HTTPException(
            status_code=400,
            detail=schemas.GrupoErroResponse(
                mensagem="Existem usuários vinculados a este grupo",
                usuarios=usuarios_data
            ).model_dump()
        )
    db.delete(grupo)
    db.commit()

@router.put("/{grupo_id}", status_code=status.HTTP_200_OK, dependencies=[require_permission('grupos:editar')])
def atualizar_grupo(
    grupo_id: UUID,
    dados: schemas.GrupoUpdate,
    db: Session = Depends(get_db)
):
    grupo = db.query(models.Grupo).filter(models.Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    if dados.nome:
        grupo.nome = dados.nome

    grupo.permissoes.clear()

    permissoes = (
        db.query(models.Permissao)
        .filter(models.Permissao.codigo.in_(dados.permissoes_codigos))
        .all()
    )

    if len(permissoes) != len(dados.permissoes_codigos):
        codigos_existentes = {p.codigo for p in permissoes}
        codigos_invalidos = set(dados.permissoes_codigos) - codigos_existentes
        raise HTTPException(status_code=400, detail=f"Permissões inválidas: {', '.join(codigos_invalidos)}")

    grupo.permissoes = permissoes
    db.commit()

    return {"mensagem": "Grupo atualizado com sucesso"}
