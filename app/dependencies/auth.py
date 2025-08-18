from fastapi import Request, Depends, HTTPException, WebSocket, WebSocketException
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from app.crud.user import buscar_usuario_por_id
from typing import Optional, Union
from jose import jwt, JWTError
from app.database import SessionLocal
from app.models.user import Usuario
from uuid import UUID
from app.models.grupo import Grupo
from app.security import verificar_token
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "padrão-inseguro")
ALGORITHM = "HS256"



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

async def get_current_user_ws(websocket: WebSocket) -> Usuario | None:
    token = websocket.query_params.get("access_token")

    if not token:
        token = websocket.cookies.get("access_token")

    if not token:
        proto = websocket.headers.get("sec-websocket-protocol")
        if proto and proto.startswith("Bearer "):
            token = proto.removeprefix("Bearer ").strip()

    if not token and "authorization" in websocket.headers:
        auth = websocket.headers["authorization"]
        if auth.startswith("Bearer "):
            token = auth.split(" ")[1]

    if not token:
        raise WebSocketException(code=1008, reason="Missing token")
        await websocket.close(code=1008)
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise WebSocketException(code=1008, reason="Invalid subject")
            return None

        db = SessionLocal()
        usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
        db.close()

        if usuario is None:
            raise WebSocketException(code=1008, reason="Invalid subject")
            return None

        return usuario

    except JWTError:
        raise WebSocketException(code=1008, reason="Invalid subject")
        return None


def is_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.grupo.nome != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


