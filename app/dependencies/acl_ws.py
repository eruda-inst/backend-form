# dependencies/acl_ws.py
from typing import Optional
from uuid import UUID
from fastapi import WebSocket
from sqlalchemy.orm import Session, joinedload
from app.db.database import SessionLocal
from app import models
from .auth import get_current_user_ws

async def deny_with_message(ws: WebSocket, code: int, msg: str):
    """Aceita, envia um JSON de erro e fecha a conexão com o código informado."""
    try: await ws.accept()
    except RuntimeError: ...
    try: await ws.send_json({"tipo":"erro","codigo":code,"mensagem":msg})
    except RuntimeError: ...
    try: await ws.close(code=code, reason=msg[:120])
    except RuntimeError: ...
    return None

async def require_acl_formulario_ws(websocket: WebSocket, formulario_id: UUID, needed: str):
    """Valida ACL de formulário no WS para 'ver', 'editar' ou 'apagar' e retorna o usuário autorizado."""
    user = await get_current_user_ws(websocket)
    if not user:
        return await deny_with_message(websocket, 4401, "Não autenticado")

    db: Session = SessionLocal()
    try:
        user_db: Optional[models.Usuario] = (
            db.query(models.Usuario)
              .options(joinedload(models.Usuario.grupo).joinedload(models.Grupo.permissoes))
              .filter(models.Usuario.id == user.id)
              .first()
        )
        if not user_db or not user_db.grupo:
            return await deny_with_message(websocket, 4401, "Usuário inválido")

        codigos = {p.codigo for p in (user_db.grupo.permissoes or [])}
        if "formularios:gerenciar_todos" in codigos:
            return user_db

        q = (
            db.query(models.FormularioPermissao)
              .filter(
                  models.FormularioPermissao.formulario_id == formulario_id,
                  models.FormularioPermissao.grupo_id == user_db.grupo.id,
              )
        )
        row = q.first()
        if not row:
            return await deny_with_message(websocket, 4403, f"Sem ACL para '{needed}' neste formulário")

        granted = (
            (needed == "ver" and bool(row.pode_ver)) or
            (needed == "editar" and bool(row.pode_editar)) or
            (needed == "apagar" and bool(row.pode_apagar))
        )
        if not granted:
            return await deny_with_message(websocket, 4403, f"Sem permissão para {needed} este formulário")

        return user_db
    finally:
        db.close()
