from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List

class PerguntaBase(BaseModel):
    texto: str
    tipo: str  # "nps", "multipla_escolha", "texto_simples", "texto_longo"
    obrigatoria: bool = True
    ordem_exibicao: Optional[int] = None
    escala_min: Optional[int] = None
    escala_max: Optional[int] = None

class PerguntaCreate(PerguntaBase):
    formulario_id: UUID

class PerguntaOut(BaseModel):
    id: UUID
    texto: str
    tipo: str
    obrigatoria: bool
    ordem_exibicao: int
    escala_min: Optional[int]
    escala_max: Optional[int]

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

class OpcaoBase(BaseModel):
    texto: str
    ordem: Optional[int] = None

class OpcaoCreate(OpcaoBase):
    pergunta_id: UUID

class OpcaoOut(OpcaoBase):
    id: UUID
    pergunta_id: UUID

    class Config:
        from_attributes = True

class RespostaBase(BaseModel):
    resposta: str

class RespostaCreate(RespostaBase):
    question_id: UUID

class RespostaOut(RespostaBase):
    id: UUID
    question_id: UUID

    class Config:
        from_attributes = True
