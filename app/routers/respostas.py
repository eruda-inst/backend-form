# app/routers/respostas.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app import schemas, dependencies, crud
from app.websockets import respostas as manager
import anyio

router = APIRouter(prefix="/respostas", tags=["Respostas"])

@router.post("/", response_model=schemas.RespostaOut, status_code=status.HTTP_201_CREATED)
async def criar_resposta(payload: schemas.RespostaCreate, request: Request, db: Session = Depends(get_db)):
    """Cria uma resposta para um formulário e publica o evento em tempo real."""
    if not payload.origem_ip:
        payload.origem_ip = request.client.host if request and request.client else None
    resp = crud.criar(db, payload)
    out = schemas.RespostaOut.model_validate(resp).model_dump()
    await manager.enviar_para_sala(resp.formulario_id, {"tipo": "resposta_criada", "dados": out})
    return resp


@router.get("/formulario/{formulario_id}", response_model=list[schemas.RespostaOut], dependencies=[dependencies.require_permission("respostas:ver")])
def listar_respostas_formulario(formulario_id: UUID, db: Session = Depends(get_db)):
    """Lista respostas de um formulário."""
    return crud.listar_por_formulario(db, formulario_id)

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
