from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.crud import permissao as facl
from typing import List, Literal, Optional
from app.dependencies.permissoes import require_permission
from uuid import UUID


router = APIRouter(prefix="/permissoes", tags=["Permissões"])

@router.get("/", response_model=List[schemas.PermissaoResponse], dependencies=[require_permission("permissoes:ver")])
def listar_permissoes(db: Session = Depends(get_db)):
    permissoes = db.query(models.Permissao).all()
    return permissoes


@router.get("/{formulario_id}/acl", response_model=list[schemas.FormularioPermissaoOut], dependencies=[require_permission("permissoes:configurar_acl")])
def get_acl(formulario_id: UUID, db: Session = Depends(get_db)):
    """Lista a ACL do formulário."""
    regs = facl.listar_acl(db, formulario_id)
    return [
        schemas.FormularioPermissaoOut(
            id=r.id,
            formulario_id=r.formulario_id,
            grupo_id=r.grupo_id,
            grupo_nome=r.grupo.nome if r.grupo else "",
            pode_ver=r.pode_ver,
            pode_editar=r.pode_editar,
            pode_apagar=r.pode_apagar,
        )
        for r in regs
    ]

@router.put("/{formulario_id}/acl", response_model=schemas.FormularioPermissaoOut, dependencies=[require_permission("permissoes:configurar_acl")])
def put_acl(formulario_id: UUID, payload: schemas.FormularioPermissaoIn, db: Session = Depends(get_db)):
    """Cria/atualiza a ACL de um grupo para o formulário."""
    try:
        reg = facl.upsert_acl(db, formulario_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return schemas.FormularioPermissaoOut(
        id=reg.id,
        formulario_id=reg.formulario_id,
        grupo_id=reg.grupo_id,
        grupo_nome=reg.grupo.nome if reg.grupo else "",
        pode_ver=reg.pode_ver,
        pode_editar=reg.pode_editar,
        pode_apagar=reg.pode_apagar,
    )

@router.put("/{formulario_id}/acl/batch", response_model=list[schemas.FormularioPermissaoOut], dependencies=[require_permission("permissoes:configurar_acl")])
def put_acl_batch(formulario_id: UUID, payload: schemas.FormularioPermissaoBatchIn, db: Session = Depends(get_db)):
    """Aplica várias ACLs de uma vez ao formulário."""
    saida = []
    for item in payload.itens:
        try:
            reg = facl.upsert_acl(db, formulario_id, item)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        saida.append(
            schemas.FormularioPermissaoOut(
                id=reg.id,
                formulario_id=reg.formulario_id,
                grupo_id=reg.grupo_id,
                grupo_nome=reg.grupo.nome if reg.grupo else "",
                pode_ver=reg.pode_ver,
                pode_editar=reg.pode_editar,
                pode_apagar=reg.pode_apagar,
            )
        )
    return saida

@router.delete("/{formulario_id}/acl/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[require_permission("permissoes:configurar_acl")])
def delete_acl(formulario_id: UUID, grupo_id: UUID, db: Session = Depends(get_db)):
    """Remove a ACL de um grupo no formulário."""
    ok = facl.remover_acl(db, formulario_id, grupo_id)
    if not ok:
        raise HTTPException(status_code=404, detail="registro não encontrado")