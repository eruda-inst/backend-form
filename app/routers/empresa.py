from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database import get_db
from app.schemas.empresa import EmpresaUpdate, EmpresaResponse
from app.crud import empresa as crud_empresa
from app.dependencies import require_permission

router = APIRouter(prefix="/empresa", tags=["Empresas"])

@router.get("/", response_model=EmpresaResponse, dependencies=[require_permission("empresa:ver")])
def listar_empresas_route(db: Session = Depends(get_db)):
    """Lista empresas."""
    return crud_empresa.buscar_empresa(db)

@router.put("/", response_model=EmpresaResponse, dependencies=[require_permission("empresa:editar")])
def atualizar_empresa_route(payload: EmpresaUpdate, db: Session = Depends(get_db)):
    """Atualiza uma empresa por id."""
    try:
        emp = crud_empresa.atualizar_empresa(db, payload)
        if not emp:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        return emp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
