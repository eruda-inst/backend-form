from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import RefreshRequest, LoginInput, LoginResponse
from app.schemas.user import UsuarioResponse
from app.security import verificar_senha, gerar_token, gerar_refresh_token, decode_jwt
from app.dependencies.auth import get_optional_user
from app.models.user import Usuario
from app.crud.user import existe_admin, buscar_usuario_por_username



router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=LoginResponse)
def login(dados: LoginInput, db: Session = Depends(get_db)):
    usuario = buscar_usuario_por_username(db, dados.username)

    if not usuario or not verificar_senha(dados.password, usuario.senha):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    access_token = gerar_token({"sub": str(usuario.id)})
    refresh_token = gerar_refresh_token({"sub": str(usuario.id)})


    return {
        "id": str(usuario.id),
        "username": usuario.username,
        "email": usuario.email,
        "firstName": usuario.nome.split(" ")[0] if usuario.nome else "",
        "lastName": " ".join(usuario.nome.split(" ")[1:]) if usuario.nome and len(usuario.nome.split(" ")) > 1 else "",
        "gender": usuario.genero if hasattr(usuario, "genero") else None,
        "image": usuario.imagem if hasattr(usuario, "imagem") else None,
        "grupo": usuario.grupo.nome if usuario.grupo else None,
        "accessToken": access_token,
        "refreshToken": refresh_token
    }

@router.get("/status")
def status(db: Session = Depends(get_db), user: Usuario | None = Depends(get_optional_user)):
    admin_existe = existe_admin(db)

    return {
        "admin_existe": admin_existe,
        "autenticado": user is not None,
        "usuario": {
            "id": str(user.id),
            "nome": user.nome,
            "email": user.email,
            "nivel": user.nivel
        } if user else None
    }

@router.post("/logout")
def logout():
    return {"mensagem": "Logout realizado com sucesso (token deve ser apagado no cliente)"}


@router.post("/refresh")
def refresh_token(dados: RefreshRequest):
    payload = decode_jwt(dados.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    novo_access_token = gerar_token({"sub": payload["sub"]})
    return {
        "access_token": novo_access_token,
        "token_type": "bearer"
    }



