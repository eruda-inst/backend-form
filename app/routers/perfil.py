from fastapi import APIRouter, Depends,status
from sqlalchemy.orm import Session
from app import crud, database
from app.dependencies.auth import get_current_user
from app import models, schemas


router = APIRouter(tags=["Perfil"])

@router.get("/me", response_model=schemas.UsuarioResponse)
def perfil(current_user: models.Usuario = Depends(get_current_user)):
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def deletar_me(db: Session = Depends(database.get_db), usuario: models.Usuario = Depends(get_current_user)):
    crud.deletar_me(db, usuario.id)