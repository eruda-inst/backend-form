from sqlalchemy import ForeignKey, Column, String, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from uuid import uuid4

class Opcao(Base):
    __tablename__ = "opcoes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pergunta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("perguntas.id", ondelete="CASCADE"),
        nullable=False,
    )
    texto = Column(String, nullable=False)
    personalizavel = Column(Boolean, nullable=False, default=False)
    ordem = Column(Integer, nullable=False)

    pergunta = relationship("Pergunta", back_populates="opcoes")
