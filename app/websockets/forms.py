from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import joinedload
from app import crud, schemas, models
from .conexoes import gerenciador
from app.database import SessionLocal, get_db
from app.dependencies.auth import get_current_user_ws
import anyio

SALA_LISTA_FORMULARIOS = "formularios"

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
            payload["perguntas"] = [p for p in payload.get("perguntas", []) if p.get("ativa")]
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

                def _atualizar(c: dict):
                    db2 = SessionLocal()
                    try:
                        return crud.atualizar_formulario_parcial(db2, c)
                    finally:
                        db2.close()

                resultado = await anyio.to_thread.run_sync(_atualizar, conteudo)
                if resultado:
                    payload = schemas.FormularioOut.model_validate(resultado).model_dump(mode="json")
                    payload["perguntas"] = [p for p in payload.get("perguntas", []) if p.get("ativa")]
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


@router.websocket("/formularios/")
async def ws_formularios(websocket: WebSocket):
    """Entrega a lista geral de formulários em tempo real via snapshot e assinaturas."""
    usuario = await get_current_user_ws(websocket)
    if usuario is None:
        await websocket.close(code=4401)
        return

    await gerenciador.conectar(
        SALA_LISTA_FORMULARIOS,
        websocket,
        {"id": str(usuario.id), "nome": usuario.nome, "username": usuario.username}
    )

    try:
        def _filtrar_perguntas_ativas(form_out: dict) -> dict:
            """Remove perguntas inativas do payload de saída."""
            form_out["perguntas"] = [p for p in form_out.get("perguntas", []) if p.get("ativa")]
            return form_out

        async def enviar_lista(incluir_inativos: bool = False):
            """Consulta e envia snapshot da lista de formulários."""
            def _carregar(incluir: bool):
                db = SessionLocal()
                try:
                    q = db.query(models.Formulario).options(joinedload(models.Formulario.perguntas))
                    if not incluir:
                        q = q.filter(models.Formulario.ativo.is_(True))
                    itens = q.all()
                    payload = [
                        _filtrar_perguntas_ativas(
                            schemas.FormularioOut.model_validate(i).model_dump(mode="json")
                        )
                        for i in itens
                    ]
                    return payload
                finally:
                    db.close()

            lista = await anyio.to_thread.run_sync(_carregar, incluir_inativos)
            await gerenciador.enviar_para_usuario(
                websocket,
                {"tipo": "lista_inicial", "conteudo": {"itens": lista}}
            )

        await enviar_lista(incluir_inativos=False)

        while True:
            data = await websocket.receive_json()
            tipo = data.get("tipo")
            conteudo = data.get("conteudo") or {}

            if tipo == "ping":
                await gerenciador.enviar_para_usuario(websocket, {"tipo": "pong"})
                continue

            if tipo == "subscribe_formularios":
                incluir_inativos = bool(conteudo.get("incluir_inativos", False))
                await enviar_lista(incluir_inativos=incluir_inativos)
                continue

            await gerenciador.enviar_para_usuario(websocket, {"tipo": "erro", "mensagem": "tipo não suportado"})
    except WebSocketDisconnect:
        await gerenciador.desconectar(SALA_LISTA_FORMULARIOS, websocket)

