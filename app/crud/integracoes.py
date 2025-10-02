from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.integracoes import Integracao
from app.schemas.integracoes import IntegracaoCreate, IntegracaoEdit
from app.services.integracoes.dispatch import testar_conexao

def create_integracao(db: Session, data: IntegracaoCreate) -> Integracao:
    """Cria uma integração genérica."""
    item = Integracao(
        tipo=data.tipo.value if hasattr(data.tipo, "value") else str(data.tipo),
        config=data.config or {},
        habilitada=bool(data.habilitada),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def list_integracoes(db: Session) -> list[Integracao]:
    """Lista integrações."""
    return db.query(Integracao).order_by(Integracao.id.asc()).all()

def get_integracao(db: Session, integracao_id: int) -> Integracao | None:
    """Obtém integração por id."""
    return db.query(Integracao).filter(Integracao.id == integracao_id).first()

def edit_integracao(db: Session, integracao_id: int, data: IntegracaoEdit) -> Integracao:
    """Atualiza tipo e/ou configuração."""
    item = db.query(Integracao).filter(Integracao.id == integracao_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integração não encontrada")
    if data.tipo is not None:
        item.tipo = data.tipo.value if hasattr(data.tipo, "value") else str(data.tipo)
    if data.config is not None:
        item.config = data.config
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def set_habilitacao_integracao(db: Session, integracao_id: int, habilitada: bool) -> Tuple[Integracao, bool]:
    """Habilita/desabilita a integração e testa a conexão."""
    item = db.query(Integracao).filter(Integracao.id == integracao_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integração não encontrada")
    item.habilitada = bool(habilitada)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item, testar_conexao(item)