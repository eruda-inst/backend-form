# app/schemas/resposta.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class RespostaItemCreate(BaseModel):
    pergunta_id: UUID
    valor_texto: Optional[str] = None
    valor_numero: Optional[int] = None
    valor_opcao_id: Optional[UUID] = None
    valor_opcao_texto: Optional[str] = None

class RespostaCreate(BaseModel):
    formulario_id: UUID
    itens: List[RespostaItemCreate]
    origem_ip: Optional[str] = None
    user_agent: Optional[str] = None
    meta: Optional[dict] = None

class RespostaItemOut(BaseModel):
    id: UUID
    pergunta_id: UUID
    valor_texto: Optional[str] = None
    valor_numero: Optional[int] = None
    valor_opcao_id: Optional[UUID] = None
    valor_opcao_texto: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RespostaOut(BaseModel):
    id: UUID
    formulario_id: UUID
    criado_em: datetime
    origem_ip: Optional[str] = None
    user_agent: Optional[str] = None
    meta: Optional[dict] = None
    itens: List[RespostaItemOut]

    model_config = ConfigDict(from_attributes=True)
