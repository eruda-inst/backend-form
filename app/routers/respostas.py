# app/routers/respostas.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.database import get_db
from app import schemas, dependencies, crud
from app.websockets.conexoes import gerenciador
from app import models
import anyio


router = APIRouter(prefix="/respostas", tags=["Respostas"])

@router.post("/{form_slug}", response_model=schemas.RespostaOut, status_code=status.HTTP_201_CREATED)
async def criar_resposta(form_slug: str, payload: schemas.RespostaCreatePublico, request: Request, db: Session = Depends(get_db)):
    """Cria uma resposta para um formulário (acessado por slug) e publica o evento em tempo real."""
    form = crud.obter_formulario_publico_por_slug(db, slug=form_slug)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulário não encontrado ou não está recebendo respostas.")

    if not payload.origem_ip:
        payload.origem_ip = request.client.host if request and request.client else None
            
    def _item_tem_valor(i: dict) -> bool:
        return any(
            i.get(k) is not None
            for k in ("valor_texto", "valor_numero", "valor_opcao_id", "valor_opcao_texto", "valor_data")
        )

    itens_raw = [i.model_dump() for i in (payload.itens or [])]
    itens_filtrados = [i for i in itens_raw if _item_tem_valor(i)]
    
    full_payload = schemas.RespostaCreate(
        formulario_id=form.id,
        itens=itens_filtrados,
        origem_ip=payload.origem_ip,
        user_agent=payload.user_agent,
        meta=payload.meta,
    )
    
    resp = crud.criar(db, full_payload)
    sala_id = f"respostas:{resp.formulario_id}"
    out = jsonable_encoder(schemas.RespostaOut.model_validate(resp))
    await gerenciador.enviar_para_sala(sala_id, {"tipo": "resposta_criada", "dados": out})
    return resp


@router.get("/formulario/{formulario_id}", response_model=list[schemas.RespostaOut], dependencies=[dependencies.require_permission("respostas:ver")])
def listar_respostas_formulario(formulario_id: UUID, db: Session = Depends(get_db), current_user: models.Usuario = Depends(dependencies.get_current_user)):
    """Lista respostas de um formulário."""
    return crud.listar_por_formulario(db, formulario_id, current_user.grupo_id)

@router.get("/{resposta_id}", response_model=schemas.RespostaOut, dependencies=[dependencies.require_permission("respostas:ver")])
def obter_resposta(resposta_id: UUID, db: Session = Depends(get_db)):
    """Retorna uma resposta específica."""
    resposta = crud.buscar_por_id(db, resposta_id)
    if not resposta:
        raise HTTPException(status_code=404, detail="Resposta não encontrada")
    return resposta

@router.delete("/{resposta_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[dependencies.require_permission("respostas:apagar")])
def deletar_resposta(resposta_id: UUID, db: Session = Depends(get_db)):
    """Exclui uma resposta."""
    if not crud.deletar(db, resposta_id):
        raise HTTPException(status_code=404, detail="Resposta não encontrada")