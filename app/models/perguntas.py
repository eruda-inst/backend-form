from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import Base

class Pergunta(Base):
    __tablename__ = "perguntas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    formulario_id = Column(UUID(as_uuid=True), ForeignKey("formularios.id"), nullable=False)
    texto = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # "nps", "multipla_escolha", "texto_simples", "texto_longo"
    obrigatoria = Column(Boolean, default=True)
    ordem_exibicao = Column(Integer, nullable=True)
    ativa = Column(Boolean, default=True)
    escala_min = Column(Integer, nullable=True)
    escala_max = Column(Integer, nullable=True)

    formulario = relationship("Formulario", back_populates="perguntas")
    opcoes = relationship(
        "Opcao",
        back_populates="pergunta",
        cascade="all, delete-orphan",
        passive_deletes=True,    
    )
    respostas = relationship("Resposta", back_populates="pergunta", cascade="all, delete-orphan")


class Opcao(Base):
    __tablename__ = "opcoes_pergunta"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    pergunta_id = Column(UUID(as_uuid=True), ForeignKey("perguntas.id"), nullable=False)
    texto = Column(String, nullable=False)
    ordem = Column(Integer, nullable=True)

    pergunta = relationship("Pergunta", back_populates="opcoes")


class Resposta(Base):
    __tablename__ = "respostas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("perguntas.id"), nullable=False)
    resposta = Column(String, nullable=False)

    pergunta = relationship("Pergunta", back_populates="respostas")