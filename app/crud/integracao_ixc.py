from fastapi import HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from typing import Tuple
from app.models.integracao_ixc import IntegracaoIXC
from app.schemas.integracao_ixc import IntegracaoIXCCreate, IntegracaoIXCEdit


def create_integracao_ixc(db: Session, data: IntegracaoIXCCreate) -> IntegracaoIXC:
    """Cria a integração IXC garantindo que exista no máximo um registro na tabela."""
    existing = db.query(IntegracaoIXC).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma integração IXC cadastrada"
        )
    item = IntegracaoIXC(
        endereco=data.endereco.strip(),
        porta=data.porta,
        usuario=data.usuario.strip(),
        senha=data.senha.strip(),
        nome_banco=data.nome_banco.strip(),
        habilitada=bool(data.habilitada),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def list_integracoes_ixc(db: Session) -> list[IntegracaoIXC]:
    """Lista todas as integrações IXC cadastradas."""
    return db.query(IntegracaoIXC).order_by(IntegracaoIXC.id.asc()).all()


def get_integracao_ixc(db: Session, integracao_id: int) -> IntegracaoIXC | None:
    """Obtém uma integração IXC pelo id."""
    return db.query(IntegracaoIXC).filter(IntegracaoIXC.id == integracao_id).first()

def edit_integracao_ixc(db: Session, integracao_id: int, data: IntegracaoIXCEdit) -> IntegracaoIXC:
    """Edita campos de conexão da integração IXC sem modificar o status de habilitação."""
    item = db.query(IntegracaoIXC).filter(IntegracaoIXC.id == integracao_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integração IXC não encontrada")

    if data.endereco is not None:
        item.endereco = data.endereco.strip()
    if data.porta is not None:
        item.porta = data.porta
    if data.usuario is not None:
        item.usuario = data.usuario.strip()
    if data.senha is not None:
        item.senha = data.senha.strip()
    if data.nome_banco is not None:
        item.nome_banco = data.nome_banco.strip()

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _montar_dsn_mysql(item: IntegracaoIXC) -> str:
    """Monta a DSN de conexão para MariaDB/MySQL usando pymysql."""
    usuario = item.usuario
    senha = item.senha
    host = item.endereco
    porta = item.porta
    banco = item.nome_banco
    return f"mysql+pymysql://{usuario}:{senha}@{host}:{porta}/{banco}"


def _testar_conexao(item: IntegracaoIXC) -> bool:
    """Tenta abrir uma conexão rápida com o banco e retorna o resultado."""
    dsn = _montar_dsn_mysql(item)
    engine: Engine = create_engine(
        dsn,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 4},
    )
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


def set_habilitacao_integracao_ixc(db: Session, integracao_id: int, habilitada: bool) -> Tuple[IntegracaoIXC, bool]:
    """Altera o campo de habilitação da integração IXC e informa se a conexão foi bem-sucedida."""
    item = db.query(IntegracaoIXC).filter(IntegracaoIXC.id == integracao_id).first()
    if not item:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integração IXC não encontrada")

    item.habilitada = bool(habilitada)
    db.add(item)
    db.commit()
    db.refresh(item)

    conexao_ok = _testar_conexao(item)
    return item, conexao_ok


