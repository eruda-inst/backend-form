from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app import models, schemas


router = APIRouter(tags=["Perfil"])

@router.get("/me", response_model=schemas.UsuarioResponse)
def perfil(current_user: models.Usuario = Depends(get_current_user)):
    return current_user