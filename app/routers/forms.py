from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import schemas, crud, models
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

@router.delete("/{formulario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_formulario_route(
    formulario_id: UUID,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    """Remove um formulário se o usuário tiver permissão global ou ACL para apagar."""
    if not crud.tem_permissao_formulario(db, usuario, formulario_id, "apagar"):
        raise HTTPException(status_code=403, detail="Sem permissão para apagar este formulário")
    ok = crud.deletar_formulario(db, formulario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
