from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from app.db.base import Base
from sqlalchemy.dialects.postgresql import JSONB


class Integracao(Base):
    __tablename__ = "integracoes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False) 
    config = Column(JSONB, nullable=False, default=dict) 
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