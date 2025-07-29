from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UsuarioCreate, UsuarioResponse
from app.crud.user import existe_admin, criar_usuario

router = APIRouter(prefix="/setup", tags=["Setup"])

@router.post("/", response_model=UsuarioResponse)
def setup(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    if existe_admin(db):
        raise HTTPException(status_code=403, detail="Setup já foi realizado")
    
    if usuario.nivel != "admin":
        raise HTTPException(status_code=403, detail="Somente administradores podem ser criados no setup")

    return criar_usuario(db, usuario)
