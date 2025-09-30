from fastapi import Depends, HTTPException, status, WebSocket, WebSocketException
from app.dependencies.auth import get_current_user_ws, get_current_user
from app import models, crud
from uuid import UUID
from sqlalchemy.orm import joinedload
from app.db.database import SessionLocal


def require_permission_callable_ws(codigo_permissao: str):
    """Retorna um callable que valida a permissão e devolve o usuário autenticado."""
    def dependency(current_user: models.Usuario = Depends(get_current_user_ws)):
        """Valida a permissão informada e retorna o usuário autenticado."""
        codigos = {p.codigo for p in (current_user.grupo.permissoes or [])} if current_user and current_user.grupo else set()
        if codigo_permissao not in codigos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{codigo_permissao}' é requerida"
            )
        return current_user
    return dependency

def require_permission_callable(codigo_permissao: str):
    """Retorna um callable que valida a permissão e devolve o usuário autenticado."""
    def dependency(current_user: models.Usuario = Depends(get_current_user)):
        """Valida a permissão informada e retorna o usuário autenticado."""
        codigos = {p.codigo for p in (current_user.grupo.permissoes or [])} if current_user and current_user.grupo else set()
        if codigo_permissao not in codigos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{codigo_permissao}' é requerida"
            )
        return current_user
    return dependency

def require_permission(codigo_permissao: str):
    """Retorna um objeto Depends para uso direto no decorator dependencies=[...]."""
    return Depends(require_permission_callable(codigo_permissao))

async def deny_with_message(ws: WebSocket, code: int, msg: str):
    try:
        await ws.accept()
    except RuntimeError:
        pass
    try:
        await ws.send_json({"tipo": "erro", "codigo": code, "mensagem": msg})
    except RuntimeError:
        pass
    try:
        await ws.close(code=code, reason=msg[:120])
    except RuntimeError:
        pass
    return None

async def require_permission_ws(websocket: WebSocket, codigo_permissao: str, formulario_id: str = UUID | None, permissao: str = None):
    """Valida a permissão global no WS e retorna o usuário autenticado (ou fecha com mensagem)."""
    user = await get_current_user_ws(websocket)
    grupo_id = [user.grupo_id]
    # formulario = crud.buscar_formulario_por_id(db, formulario_id)
    db = SessionLocal()
    tem_perm = (
                db.query(models.FormularioPermissao) \
                .filter(models.FormularioPermissao.formulario_id == formulario_id,
                        models.FormularioPermissao.grupo_id.in_(grupo_id),
                        getattr(models.FormularioPermissao, permissao).is_(True),
                )
                .first()
    )
    if not user:
        return await deny_with_message(websocket, 4401, "Não autenticado")

    try:
        user_db = (
            db.query(models.Usuario)
              .options(
                  joinedload(models.Usuario.grupo)
                  .joinedload(models.Grupo.permissoes)
              )
              .filter(models.Usuario.id == user.id)
              .first()
        )
        if not user_db:
            return await deny_with_message(websocket, 4401, "Usuário inválido")

        codigos = set()
        if getattr(user_db, "grupo", None):
            codigos |= {p.codigo for p in (user_db.grupo.permissoes or [])}

        if codigo_permissao not in codigos:
            return await deny_with_message(
                websocket, 4403, f"Permissão '{codigo_permissao}' é requerida"
            )
        
        if not tem_perm:
            return await deny_with_message(
                websocket, 4403, "Sem permissão para editar este formulário"
            )

        return user_db
    finally:
        db.close()

