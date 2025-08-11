# app/routers/ws_respostas.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from app.database import get_db
import app.websockets.respostas as manager
from app import schemas, dependencies, crud

router = APIRouter(prefix="/ws/respostas", tags=["WebSocket Respostas"])


@router.websocket("/formulario/{formulario_id}")
async def ws_respostas_formulario(
    websocket: WebSocket,
    formulario_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(dependencies.require_permission_callable("respostas:ver"))
):
    """Abre um canal WebSocket para receber respostas em tempo real de um formulário e envia um histórico inicial."""
    await manager.connect(formulario_id, websocket)
    try:
        historico = crud.listar_por_formulario(db, formulario_id)[:50]
        payload = [schemas.RespostaOut.model_validate(r).model_dump() for r in historico]
        await manager.enviar_para_sala(formulario_id, {"tipo": "bootstrap", "dados": payload})
        while True:
            msg = await websocket.receive_text()
            await websocket.send_json({"tipo": "ack", "dados": msg})
    except WebSocketDisconnect:
        await manager.disconnect(formulario_id, websocket)
