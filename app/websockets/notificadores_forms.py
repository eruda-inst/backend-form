# app/ws/notificadores_formularios.py
from sqlalchemy.orm import joinedload
from app.db.database import SessionLocal
from app import models, schemas
from .conexoes import gerenciador

SALA_LISTA_FORMULARIOS = "formularios"

def _filtrar_perguntas_ativas(payload: dict) -> dict:
    """Remove perguntas inativas do payload."""
    payload["perguntas"] = [p for p in payload.get("perguntas", []) if p.get("ativa")]
    return payload

async def notificar_formulario_criado(formulario_id: str) -> None:
    """Envia evento de criação para a sala geral de formulários."""
    db = SessionLocal()
    try:
        f = (
            db.query(models.Formulario)
              .options(joinedload(models.Formulario.perguntas))
              .filter(models.Formulario.id == formulario_id)
              .first()
        )
        if not f:
            return
        out = schemas.FormularioOut.model_validate(f).model_dump(mode="json")
        out = _filtrar_perguntas_ativas(out)
        await gerenciador.enviar_para_sala(SALA_LISTA_FORMULARIOS, {"tipo": "formulario_criado", "conteudo": out})
    finally:
        db.close()

async def notificar_formulario_atualizado(formulario_id: str) -> None:
    """Envia evento de atualização para a sala geral de formulários."""
    db = SessionLocal()
    try:
        f = (
            db.query(models.Formulario)
              .options(joinedload(models.Formulario.perguntas))
              .filter(models.Formulario.id == formulario_id)
              .first()
        )
        if not f:
            return
        out = schemas.FormularioOut.model_validate(f).model_dump(mode="json")
        out = _filtrar_perguntas_ativas(out)
        await gerenciador.enviar_para_sala(SALA_LISTA_FORMULARIOS, {"tipo": "formulario_atualizado", "conteudo": out})
    finally:
        db.close()

async def notificar_formulario_apagado(formulario_id: str) -> None:
    """Envia evento de exclusão (soft delete) para a sala geral de formulários."""
    await gerenciador.enviar_para_sala(SALA_LISTA_FORMULARIOS, {"tipo": "formulario_apagado", "conteudo": {"id": str(formulario_id)}})
