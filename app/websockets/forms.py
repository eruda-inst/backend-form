from fastapi import APIRouter 
from fastapi import WebSocket, WebSocketDisconnect
from app import crud, schemas
from .conexoes import GerenciadorConexoes
from app.database import SessionLocal
from app.dependencies.permissoes import require_permission
from app.dependencies.auth import get_current_user_ws


router = APIRouter(prefix="/ws", tags=["Websocket - Formulários"])
gerenciador = GerenciadorConexoes()

@router.websocket("/formularios/{formulario_id}")
async def socket_formulario(websocket: WebSocket, formulario_id: str):
    usuario = await get_current_user_ws(websocket)
    if usuario is None:
        return  

    await websocket.accept()

    await gerenciador.conectar(
        formulario_id,
        websocket,
        {
            "id": str(usuario.id),
            "nome": usuario.nome,
            "username": usuario.username
        }
    )
    await gerenciador.enviar_para_sala(
        formulario_id,
        {
            "tipo": "usuarios_na_sala",
            "usuarios": gerenciador.lista_usuarios_na_sala(formulario_id)
        }
    )
    db = SessionLocal()
    try:
        while True:
            data = await websocket.receive_json()
            tipo = data.get("tipo")
            conteudo = data.get("conteudo")

            if tipo == "update_formulario":
                resultado = crud.atualizar_formulario_parcial(db, conteudo)
                if resultado:
                    await gerenciador.enviar_para_sala(
                        formulario_id,
                        {
                            "tipo": "formulario_atualizado",
                            "conteudo": schemas.FormularioOut.model_validate(resultado).model_dump(mode="json")
                        }
                    )
    except WebSocketDisconnect:
        gerenciador.desconectar(formulario_id, websocket)
        await gerenciador.enviar_para_sala(
            formulario_id,
            {
                "tipo": "usuario_desconectado",
                "usuarios": gerenciador.lista_usuarios_na_sala(formulario_id)
            }
        )
    finally:
        db.close()