from uuid import UUID
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from app.models.perguntas import TipoPergunta
from .opcoes import OpcaoBase, OpcaoOut


class PerguntaBase(BaseModel):
    texto: str
    tipo: str  # "nps", "multipla_escolha", "texto_simples", "texto_longo"
    obrigatoria: bool = True
    ordem_exibicao: Optional[int] = None
    escala_min: Optional[int] = None
    escala_max: Optional[int] = None
    opcoes: Optional[List[OpcaoBase]] = None


class PerguntaCreate(PerguntaBase):
    formulario_id: UUID
    bloco_id: UUID

    @model_validator(mode="after")
    def validar_por_tipo(self):
        if self.tipo == TipoPergunta.nps:
            if self.escala_min is None or self.escala_max is None:
                raise ValueError("NPS exige escala_min e escala_max")
        if self.tipo == TipoPergunta.multipla_escolha:
            if not self.opcoes:
                raise ValueError("Múltipla escolha exige lista de opções")
        return self



class PerguntaOut(BaseModel):
    id: UUID
    formulario_id: UUID
    bloco_id: UUID
    texto: str
    tipo: str
    obrigatoria: bool
    ativa: bool
    ordem_exibicao: int | None = None
    escala_min: Optional[int] | None = None
    escala_max: Optional[int] | None = None
    opcoes: list[OpcaoOut] = []

    model_config = {
        "from_attributes": True
    }

class PerguntaUpdatePayload(BaseModel):
    id: Optional[UUID] = None
    texto: Optional[str] = None
    tipo: Optional[str] = None
    obrigatoria: Optional[bool] = None
    ordem_exibicao: Optional[int] = None
    escala_min: Optional[int] = None
    escala_max: Optional[int] = None


class RespostaBase(BaseModel):
    resposta: str

class RespostaCreate(RespostaBase):
    question_id: UUID

class RespostaOut(RespostaBase):
    id: UUID
    question_id: UUID

    class Config:
        from_attributes = True
