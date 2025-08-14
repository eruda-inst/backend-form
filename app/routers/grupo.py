from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from fastapi.responses import Response
from app import models, schemas, crud, dependencies
from app.database import get_db
from uuid import UUID
from app.models.permissao import Permissao
from typing import List
from app.dependencies.permissoes import require_permission




router = APIRouter(prefix="/grupos", tags=["Grupos"])
# 
@router.get("/", response_model=List[schemas.GrupoComPermissoesResponse], response_model_exclude_none=True, dependencies=[require_permission('grupos:ver')])
def listar_grupos_com_permissoes(db: Session = Depends(get_db), usuario: models.Usuario = Depends(dependencies.get_current_user)):
    pode_ver_permissoes = crud.tem_permissao(db, usuario, "permissoes:ver")
    
    if pode_ver_permissoes:
        grupos = (
        db.query(models.Grupo).options(selectinload(models.Grupo.permissoes)).all()
        )    
        return grupos

    grupos = (
        db.query(models.Grupo)
        .options(selectinload(models.Grupo.permissoes))
        .all()
    )
    return [{"id": g.id, "nome": g.nome} for g in grupos]

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
    """Exclui um grupo apenas se não for 'admin' e sem usuários vinculados; retorna 409 com lista de usuários."""
    grupo = db.query(models.Grupo).filter(models.Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    if grupo.nome.strip().lower() == "admin":
        raise HTTPException(status_code=403, detail="O grupo admin não pode ser deletado")

    usuarios = (
        db.query(models.Usuario.id, models.Usuario.nome, models.Usuario.email)
        .filter(models.Usuario.grupo_id == grupo.id)
        .all()
    )

    if usuarios:
        detalhe = {
            "mensagem": "Existem usuários vinculados a este grupo",
            "quantidade": len(usuarios),
            "usuarios": [{"id": str(u.id), "nome": u.nome, "email": u.email} for u in usuarios]
        }
        raise HTTPException(status_code=409, detail=jsonable_encoder(detalhe))

    db.delete(grupo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{grupo_id}", status_code=status.HTTP_200_OK, dependencies=[require_permission('grupos:editar')])
def atualizar_grupo(
    grupo_id: UUID,
    dados: schemas.GrupoUpdate,
    db: Session = Depends(get_db)
):
    grupo = db.query(models.Grupo).filter(models.Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    
    if grupo.nome == "admin":
        raise HTTPException(status_code=403, detail="O grupo admin não pode ser editado")

    if dados.nome is not None:
        if dados.nome.strip().lower() == "admin":
            raise HTTPException(status_code=400, detail="Não é possível renomear um grupo para 'admin'")
        grupo.nome = dados.nome.strip()

    if dados.permissoes_codigos is not None:
        permissoes = (
            db.query(models.Permissao)
            .filter(models.Permissao.codigo.in_(dados.permissoes_codigos))
            .all()
        )
        if len(permissoes) != len(dados.permissoes_codigos):
            codigos_existentes = {p.codigo for p in permissoes}
            codigos_invalidos = set(dados.permissoes_codigos) - codigos_existentes
            raise HTTPException(status_code=400, detail=f"Permissões inválidas: {', '.join(sorted(codigos_invalidos))}")
        grupo.permissoes = permissoes

    db.commit()
    return {"mensagem": "Grupo atualizado com sucesso"}
