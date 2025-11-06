from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, CheckConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class TipoPergunta(str, Enum):
    nps = "nps"
    multipla_escolha = "multipla_escolha"
    texto_simples = "texto_simples"
    texto_longo = "texto_longo"
    numero = "numero"
    data = "data"
    caixa_selecao = "caixa_selecao"
    email = "email"
    telefone = "telefone"
    cnpj = "cnpj"
    multipla_escolha_personalizada = "multipla_escolha_personalizada"

class Pergunta(Base):
    __tablename__ = "perguntas"
    __table_args__ = (
        CheckConstraint(
            "(tipo <> 'nps') OR (escala_min IS NOT NULL AND escala_max IS NOT NULL AND escala_min < escala_max)",
            name="chk_nps_escala"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    formulario_id = Column(UUID(as_uuid=True), ForeignKey("formularios.id"), nullable=False)
    bloco_id = Column(UUID(as_uuid=True), ForeignKey("blocos.id", ondelete="RESTRICT"), nullable=False)
    texto = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    tipo = Column(SAEnum(TipoPergunta, name="tipo_pergunta"), nullable=False)
    obrigatoria = Column(Boolean, default=True)
    ordem_exibicao = Column(Integer, nullable=True)
    ativa = Column(Boolean, default=True)
    escala_min = Column(Integer, nullable=True)
    escala_max = Column(Integer, nullable=True)

    formulario = relationship("Formulario", back_populates="perguntas")
    bloco = relationship("Bloco", back_populates="perguntas")
    opcoes = relationship(
        "Opcao",
        back_populates="pergunta",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    itens_resposta = relationship("RespostaItem", back_populates="pergunta", cascade="all, delete-orphan")
