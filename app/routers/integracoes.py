from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.integracoes import IntegracaoCreate, IntegracaoEdit, IntegracaoOut, IntegracaoHabilitacao, IntegracaoStatusOut
from app.crud.integracoes import create_integracao, list_integracoes, get_integracao, edit_integracao, set_habilitacao_integracao
from app.dependencies.permissoes import require_permission

router = APIRouter(prefix="/integracoes", tags=["Integracoes"])

@router.post("", response_model=IntegracaoOut, dependencies=[require_permission("integracoes:criar")])
def criar(payload: IntegracaoCreate, db: Session = Depends(get_db)):
    """Cria uma integração genérica."""
    return create_integracao(db, payload)

@router.get("", response_model=list[IntegracaoOut], dependencies=[require_permission("integracoes:ver")])
def listar(db: Session = Depends(get_db)):
    """Lista integrações."""
    return list_integracoes(db)

@router.get("/{integracao_id}", response_model=IntegracaoOut, dependencies=[require_permission("integracoes:ver")])
def obter(integracao_id: int, db: Session = Depends(get_db)):
    """Obtém integração por id."""
    item = get_integracao(db, integracao_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integração não encontrada")
    return item

@router.patch("/{integracao_id}", response_model=IntegracaoOut, dependencies=[require_permission("integracoes:editar")])
def editar(integracao_id: int, payload: IntegracaoEdit, db: Session = Depends(get_db)):
    """Atualiza tipo e/ou configuração."""
    return edit_integracao(db, integracao_id, payload)

@router.patch("/{integracao_id}/habilitacao", response_model=IntegracaoStatusOut, dependencies=[require_permission("integracoes:editar")])
def habilitar(integracao_id: int, payload: IntegracaoHabilitacao, db: Session = Depends(get_db)):
    """Habilita/desabilita e retorna status de conexão."""
    item, conexao_ok = set_habilitacao_integracao(db, integracao_id, payload.habilitada)
    return {
        "id": item.id,
        "tipo": item.tipo,
        "config": item.config,
        "habilitada": item.habilitada,
        "criado_em": item.criado_em,
        "atualizado_em": item.atualizado_em,
        "conexao_ok": conexao_ok,
    }