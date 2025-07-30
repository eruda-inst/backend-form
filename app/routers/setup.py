from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UsuarioCreate, UsuarioResponse
from app.crud.user import existe_admin, criar_usuario
from app.models.grupo import Grupo
from app.models.user import Usuario

router = APIRouter(prefix="/setup", tags=["Setup"])

@router.post("/", response_model=UsuarioResponse)
def setup(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    grupo_admin = db.query(Grupo).filter(Grupo.nome == "admin").first()
    if not grupo_admin:
        grupo_admin = Grupo(nome="admin")
        db.add(grupo_admin)
        db.commit()
        db.refresh(grupo_admin) 
    admin_existe = db.query(Usuario).filter(Usuario.grupo_id == grupo_admin.id).first()
    if admin_existe:
        raise HTTPException(status_code=403, detail="Setup já foi realizado")
    
    dados = usuario.model_dump()
    dados["grupo_id"] = grupo_admin.id
    usuario_corrigido = UsuarioCreate(**dados)

    return criar_usuario(db, usuario_corrigido)
