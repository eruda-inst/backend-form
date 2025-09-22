from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from app.database import Base


class IntegracaoIXC(Base):
    __tablename__ = "ixc_integracoes"
    __table_args__ = (
        UniqueConstraint("endereco", "nome_banco", name="uix_endereco_nome_banco"),
    )

    id = Column(Integer, primary_key=True, index=True)
    endereco = Column(String(255), nullable=False)
    porta = Column(Integer, nullable=False, default=3306)
    usuario = Column(String(128), nullable=False)
    senha = Column(String(128), nullable=False)
    nome_banco = Column(String(128), nullable=False)
    habilitada = Column(Boolean, default=False, nullable=False)
    criado_em = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    atualizado_em = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def endereco_completo(self) -> str:
        return f"{self.endereco}:{self.porta}"