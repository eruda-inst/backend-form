from sqlalchemy import Column, ForeignKey, Text, Integer, JSON, DateTime, String, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timezone
from app.models.user import Base

class Resposta(Base):
    __tablename__ = "respostas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    formulario_id = Column(UUID(as_uuid=True), ForeignKey("formularios.id", ondelete="CASCADE"), nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    origem_ip = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    meta = Column(JSON, nullable=True)

    itens = relationship("RespostaItem", back_populates="resposta", cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        Index("ix_respostas_formulario_id", "formulario_id"),
        Index("ix_respostas_criado_em", "criado_em"),
    )

class RespostaItem(Base):
    __tablename__ = "respostas_itens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    resposta_id = Column(UUID(as_uuid=True), ForeignKey("respostas.id", ondelete="CASCADE"), nullable=False)
    pergunta_id = Column(UUID(as_uuid=True), ForeignKey("perguntas.id", ondelete="CASCADE"), nullable=False)

    valor_texto = Column(Text, nullable=True)
    valor_numero = Column(Integer, nullable=True)
    valor_opcao_id = Column(UUID(as_uuid=True), nullable=True)
    valor_opcao_texto = Column(Text, nullable=True)

    resposta = relationship("Resposta", back_populates="itens")
    pergunta = relationship("Pergunta", back_populates="itens_resposta")
