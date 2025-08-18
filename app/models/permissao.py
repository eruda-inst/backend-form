from sqlalchemy import Column, String, Table, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
import uuid
from .user import Base

grupo_permissoes = Table(
    "grupos_permissoes",
    Base.metadata,
    Column("grupo_id", UUID(as_uuid=True), ForeignKey("grupos.id"), primary_key=True),
    Column("permissao_id", UUID(as_uuid=True), ForeignKey("permissoes.id"), primary_key=True),
)

class Permissao(Base):
    __tablename__ = "permissoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String, unique=True, nullable=False)
    nome = Column(String, unique=True, nullable=False)

    grupos = relationship("Grupo", secondary=grupo_permissoes, back_populates="permissoes")


class FormularioPermissao(Base):
    __tablename__ = "formularios_permissoes"
    __table_args__ = (UniqueConstraint("formulario_id", "grupo_id", name="uq_formulario_grupo"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    formulario_id = Column(UUID(as_uuid=True), ForeignKey("formularios.id", ondelete="CASCADE"), nullable=False)
    grupo_id = Column(UUID(as_uuid=True), ForeignKey("grupos.id", ondelete="CASCADE"), nullable=False)
    pode_ver = Column(Boolean, default=False, nullable=False)
    pode_editar = Column(Boolean, default=False, nullable=False)
    pode_apagar = Column(Boolean, default=False, nullable=False)

    formulario = relationship("Formulario", back_populates="permissoes")
    grupo = relationship("Grupo", back_populates="formulario_permissoes")