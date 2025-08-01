from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import schemas, crud
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissoes import require_permission



router = APIRouter(prefix="/formularios", tags=["Formulários"])

@router.post("/", response_model=schemas.FormularioOut, status_code=status.HTTP_201_CREATED, dependencies=[require_permission("formularios:criar")])
def criar_formulario(
    dados: schemas.FormularioCreate,
    db: Session = Depends(get_db),
    usuario_id: UUID = Depends(get_current_user)
):
    return crud.forms.criar_formulario(db, dados, usuario_id)


@router.get("/", response_model=list[schemas.FormularioOut], dependencies=[require_permission("formularios:ver")])
def listar_formularios(incluir_inativos: bool = False, db: Session = Depends(get_db)):
    return crud.forms.listar_formularios(db, incluir_inativos)

@router.get("/{formulario_id}", response_model=schemas.FormularioOut)
def buscar_formulario(formulario_id: UUID, db: Session = Depends(get_db)):
    formulario = crud.buscar_formulario_por_id(db, formulario_id)
    if not formulario or not formulario.ativo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulário não encontrado")
    return formulario
