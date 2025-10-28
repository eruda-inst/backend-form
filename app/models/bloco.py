import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base  # ajuste se seu Base estiver em outro módulo

class Bloco(Base):
    __tablename__ = "blocos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    ordem = Column(Integer, nullable=False)
    form_id = Column(
        UUID(as_uuid=True),
        ForeignKey("formularios.id", ondelete="CASCADE"),
        nullable=False,
    )

    form = relationship("Formulario", back_populates="blocos")
    perguntas = relationship("Pergunta", back_populates="bloco", cascade="all,delete-orphan")

    __table_args__ = (
        UniqueConstraint("form_id", "ordem", name="uq_blocos_form_ordem"),
    )