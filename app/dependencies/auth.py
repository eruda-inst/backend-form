from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.user import buscar_usuario_por_id
from app.security import decode_jwt
from typing import Optional
from app.models.user import Usuario

def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[Usuario]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    payload = decode_jwt(token)
    if not payload or "sub" not in payload:
        return None

    return buscar_usuario_por_id(db, payload["sub"])

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Usuario:
    usuario = get_optional_user(request, db)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido ou ausente")
    return usuario


def is_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.nivel != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


