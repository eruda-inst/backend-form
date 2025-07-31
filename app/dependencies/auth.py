from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from app.crud.user import buscar_usuario_por_id
from app.security import decode_jwt
from typing import Optional
from app.models.user import Usuario
from uuid import UUID
from app.models.grupo import Grupo
from app.security import verificar_token


def _carregar_usuario_com_relacionamentos(db: Session, usuario_id: UUID) -> Usuario | None:
    return (
        db.query(Usuario)
        .options(selectinload(Usuario.grupo).selectinload(Grupo.permissoes))
        .filter(Usuario.id == usuario_id)
        .first()
    )

def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Usuario | None:
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return None

    token = token.removeprefix("Bearer ").strip()
    try:
        payload = verificar_token(token)
        usuario_id = payload.get("sub")
        if not usuario_id:
            return None
        return _carregar_usuario_com_relacionamentos(db, usuario_id)
    except Exception:
        return None

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Usuario:
    usuario = get_optional_user(request, db)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido ou ausente")
    return usuario


def is_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.grupo.nome != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


