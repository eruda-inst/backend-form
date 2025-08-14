from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UsuarioCreate, UsuarioResponse
from app.schemas.setup import SetupPayload
from app.crud.user import existe_admin, criar_usuario, get_usuario_admin
from app.dependencies.auth import get_optional_user
from app.models.grupo import Grupo
from app.models.user import Usuario
from app.crud.grupo import existe_grupo_admin
from app.crud.empresa import buscar_empresa, criar_empresa

router = APIRouter(prefix="/setup", tags=["Setup"])

@router.post("/", response_model=UsuarioResponse)
def setup(payload: SetupPayload, db: Session = Depends(get_db)):
    grupo_admin = db.query(Grupo).filter(Grupo.nome == "admin").first()
    if not grupo_admin:
        grupo_admin = Grupo(nome="admin")
        db.add(grupo_admin)
        db.commit()
        db.refresh(grupo_admin) 
    admin_existe = db.query(Usuario).filter(Usuario.grupo_id == grupo_admin.id).first()
    if admin_existe:
        raise HTTPException(status_code=403, detail="Setup já foi realizado")
    empresa_existente = buscar_empresa(db)
    if not empresa_existente:
        try:
            criar_empresa(db, payload.empresa)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        if (payload.empresa.nome and payload.empresa.nome != empresa_existente.nome) or \
           (payload.empresa.cnpj and payload.empresa.cnpj != empresa_existente.cnpj):
            raise HTTPException(
                status_code=409,
                detail="Empresa já existe com dados diferentes. Atualize via PUT /empresa."
            )

    dados = payload.usuario.model_dump()
    dados["grupo_id"] = grupo_admin.id
    usuario_corrigido = UsuarioCreate(**dados)

    return criar_usuario(db, usuario_corrigido)



@router.get("/status")
def status(db: Session = Depends(get_db), user: Usuario | None = Depends(get_optional_user)):
    admin_existe = existe_admin(db)
    grupo_admin_existe = existe_grupo_admin(db)
    usuario_admin = get_usuario_admin(db)

    return {
        "grupo_admin_existe": grupo_admin_existe,
        "admin_existe": admin_existe,
        "autenticado": user is not None,
        "usuario": {
            "id": str(user.id),
            "nome": user.nome,
            "email": user.email,
            "grupo": user.grupo.nome if user.grupo else None,
        } if user else None,
        "usuario_admin": {
            "id": str(usuario_admin.id),
            "nome": usuario_admin.nome,
            "email": usuario_admin.email,
            "grupo": usuario_admin.grupo.nome if usuario_admin.grupo else None,
        } if usuario_admin else None
    }

