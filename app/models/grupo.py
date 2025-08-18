from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .user import Base
from app.models.permissao import grupo_permissoes

class Grupo(Base):
    __tablename__ = "grupos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String, unique=True, nullable=False)

    usuarios = relationship("Usuario", back_populates="grupo")

    permissoes = relationship("Permissao", secondary=grupo_permissoes, back_populates="grupos")
    formularios_permissoes = relationship( 
        "FormularioPermissao",
        back_populates="grupo",
        cascade="all, delete-orphan",
    )
