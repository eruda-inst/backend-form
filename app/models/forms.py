from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.user import Base

class Formulario(Base):
    __tablename__ = "formularios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    titulo = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    versao_atual = Column(Integer, default=1)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    criado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    perguntas = relationship("Pergunta", back_populates="formulario", cascade="all, delete-orphan")
    versoes = relationship("FormularioVersao", back_populates="formulario", cascade="all, delete-orphan")
    edicoes = relationship("EdicaoFormulario", back_populates="formulario", cascade="all, delete-orphan")


class FormularioVersao(Base):
    __tablename__ = "formularios_versoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    formulario_id = Column(UUID(as_uuid=True), ForeignKey("formularios.id"), nullable=False)
    versao = Column(Integer, nullable=False)
    nome = Column(String, nullable=False)
    perguntas_json = Column(JSON, nullable=False)
    criado_em = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    criado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)

    formulario = relationship("Formulario", back_populates="versoes")


class EdicaoFormulario(Base):
    __tablename__ = "edicoes_formulario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    formulario_id = Column(UUID(as_uuid=True), ForeignKey("formularios.id"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    campo = Column(String, nullable=False)
    valor_antigo = Column(String, nullable=True)
    valor_novo = Column(String, nullable=True)
    data_edicao = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    formulario = relationship("Formulario", back_populates="edicoes")