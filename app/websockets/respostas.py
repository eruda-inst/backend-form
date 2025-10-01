# app/routers/ws_respostas.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from .conexoes import gerenciador
from app import schemas, crud
from app.dependencies.auth import get_current_user_ws
from app.dependencies.permissoes import require_permission_ws

router = APIRouter(prefix="/ws/respostas", tags=["WebSocket Respostas"])

@router.websocket("/formulario/{formulario_id}")
async def ws_respostas_formulario(websocket: WebSocket, formulario_id: str):
    print("[WS] import gerenciador no WS:", hex(id(gerenciador)))
    """Entrega respostas em tempo real de um formulário com bootstrap inicial e presença por sala dedicada."""
    usuario = await get_current_user_ws(websocket)
    # usuario = await require_permission_ws(websocket, "formularios:ver", None, "pode_ver")
    if not usuario:
        return

    sala_id = f"respostas:{formulario_id}"
    await gerenciador.conectar(
        sala_id,
        websocket,
        {"id": str(usuario.id), "nome": usuario.nome, "username": usuario.username}
    )

    db: Session = SessionLocal()
    try:
        try:
            form_uuid = UUID(formulario_id)
        except ValueError:
            await gerenciador.enviar_para_usuario(websocket, {"tipo": "erro", "mensagem": "formulario_id inválido"})
            await gerenciador.desconectar(sala_id, websocket)
            return

        historico = crud.listar_por_formulario_ws(db, form_uuid)[:50]
        payload = [schemas.RespostaOut.model_validate(r).model_dump(mode="json") for r in historico]
        await gerenciador.enviar_para_usuario(websocket, {"tipo": "bootstrap_respostas", "dados": payload})
        await gerenciador.enviar_para_sala(
            sala_id,
            {"tipo": "usuarios_na_sala_respostas", "usuarios": gerenciador.lista_usuarios_na_sala(sala_id)}
        )

        while True:
            msg = await websocket.receive_json()
            await gerenciador.enviar_para_usuario(websocket, {"tipo": "ack", "dados": msg})

    except WebSocketDisconnect:
        await gerenciador.desconectar(sala_id, websocket)
        await gerenciador.enviar_para_sala(
            sala_id,
            {"tipo": "usuario_desconectado_respostas", "usuarios": gerenciador.lista_usuarios_na_sala(sala_id)}
        )
    finally:
        db.close()
