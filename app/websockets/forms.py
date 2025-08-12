from fastapi import APIRouter 
from fastapi import WebSocket, WebSocketDisconnect
from app import crud, schemas
from .conexoes import gerenciador
from app.database import SessionLocal
from app.dependencies.auth import get_current_user_ws
import anyio


router = APIRouter(prefix="/ws", tags=["Websocket - Formulários"])

@router.websocket("/formularios/{formulario_id}")
async def socket_formulario(websocket: WebSocket, formulario_id: str):
    """Gerencia colaboração em tempo real com estado inicial e updates restritos ao formulário do path."""
    usuario = await get_current_user_ws(websocket)
    if usuario is None:
        await websocket.close(code=4401)
        return

    await gerenciador.conectar(
        formulario_id,
        websocket,
        {"id": str(usuario.id), "nome": usuario.nome, "username": usuario.username}
    )

    db = SessionLocal()
    try:
        def _carregar_estado():
            return crud.buscar_formulario_por_id(db, formulario_id)

        estado = await anyio.to_thread.run_sync(_carregar_estado)
        if estado:
            payload = schemas.FormularioOut.model_validate(estado).model_dump(mode="json")
            await gerenciador.enviar_para_usuario(websocket, {"tipo": "estado_inicial", "conteudo": payload})

        await gerenciador.enviar_para_sala(
            formulario_id,
            {"tipo": "usuarios_na_sala", "usuarios": gerenciador.lista_usuarios_na_sala(formulario_id)}
        )

        while True:
            data = await websocket.receive_json()
            tipo = data.get("tipo")
            conteudo = data.get("conteudo") or {}

            if tipo == "update_formulario":
                conteudo["formulario_id"] = formulario_id

                def _atualizar():
                    return crud.atualizar_formulario_parcial(db, conteudo)

                resultado = await anyio.to_thread.run_sync(_atualizar)
                if resultado:
                    payload = schemas.FormularioOut.model_validate(resultado).model_dump(mode="json")
                    await gerenciador.enviar_para_sala(
                        formulario_id,
                        {"tipo": "formulario_atualizado", "conteudo": payload}
                    )
                else:
                    await gerenciador.enviar_para_usuario(websocket, {"tipo": "erro", "mensagem": "falha ao atualizar"})
            else:
                await gerenciador.enviar_para_usuario(websocket, {"tipo": "erro", "mensagem": "tipo não suportado"})
    except WebSocketDisconnect:
        await gerenciador.desconectar(formulario_id, websocket)
        await gerenciador.enviar_para_sala(
            formulario_id,
            {"tipo": "usuario_desconectado", "usuarios": gerenciador.lista_usuarios_na_sala(formulario_id)}
        )
    finally:
        db.close()