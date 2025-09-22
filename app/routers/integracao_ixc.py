from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.integracao_ixc import IntegracaoIXCCreate, IntegracaoIXCOut, IntegracaoIXCEdit, IntegracaoIXCStatusOut, IntegracaoIXCHabilitacao
from app.crud.integracao_ixc import create_integracao_ixc, list_integracoes_ixc, get_integracao_ixc, edit_integracao_ixc, set_habilitacao_integracao_ixc
from app.dependencies.permissoes import require_permission

router = APIRouter(prefix="/integracoes/ixc", tags=["Integracoes IXC"])


@router.post("/", response_model=IntegracaoIXCOut, status_code=status.HTTP_201_CREATED, dependencies=[require_permission("integracoes:criar")])
def criar_integracao_ixc(payload: IntegracaoIXCCreate, db: Session = Depends(get_db)):
    """Cria a integração IXC a partir dos dados enviados pelo cliente."""
    return create_integracao_ixc(db, payload)

@router.get("/", response_model=list[IntegracaoIXCOut], dependencies=[require_permission("integracoes:ver")])
def listar_integracoes_ixc(db: Session = Depends(get_db)):
    """Lista todas as integrações IXC cadastradas."""
    return list_integracoes_ixc(db)


@router.get("/{integracao_id}", response_model=IntegracaoIXCOut, dependencies=[require_permission("integracoes:ver")])
def obter_integracao_ixc(integracao_id: int, db: Session = Depends(get_db)):
    """Obtém os dados de uma integração IXC específica pelo id."""
    integracao = get_integracao_ixc(db, integracao_id)
    if not integracao:
        raise HTTPException(status_code=404, detail="Integração IXC não encontrada")
    return integracao

@router.put("/{integracao_id}/editar", response_model=IntegracaoIXCOut, dependencies=[require_permission("integracoes:editar")])
def editar_integracao_ixc(integracao_id: int, payload: IntegracaoIXCEdit, db: Session = Depends(get_db)):
    """Edita a integração IXC sem permitir alteração do status de habilitação."""
    return edit_integracao_ixc(db, integracao_id, payload)


@router.patch("/{integracao_id}/habilitacao", response_model=IntegracaoIXCStatusOut, dependencies=[require_permission("integracoes:editar")])
def atualizar_habilitacao_integracao_ixc(integracao_id: int, payload: IntegracaoIXCHabilitacao, db: Session = Depends(get_db)):
    """Atualiza o status de habilitação da integração IXC e retorna o resultado de conexão."""
    item, conexao_ok = set_habilitacao_integracao_ixc(db, integracao_id, payload.habilitada)
    return {
        "id": item.id,
        "endereco": item.endereco,
        "porta": item.porta,
        "usuario": item.usuario,
        "nome_banco": item.nome_banco,
        "habilitada": item.habilitada,
        "endereco_completo": item.endereco_completo,
        "criado_em": item.criado_em,
        "atualizado_em": item.atualizado_em,
        "conexao_ok": conexao_ok,
    }