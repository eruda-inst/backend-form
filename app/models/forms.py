from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, JSON, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
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
    recebendo_respostas: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    slug_publico = Column(String(64), nullable=True, unique=True, index=True)

    unico_por_chave_modo: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        server_default=text("'none'")
    )

    permissoes = relationship(
        "FormularioPermissao",
        back_populates="formulario",
        cascade="all, delete-orphan",
        passive_deletes=True,        
    )

    perguntas = relationship(
        "Pergunta",
        back_populates="formulario",
        lazy="joined",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
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