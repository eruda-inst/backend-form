from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class OpcaoBase(BaseModel):
    texto: str
    ordem: Optional[int] = None

class OpcaoCreate(OpcaoBase):
    pergunta_id: UUID

class OpcaoOut(OpcaoBase):
    id: UUID
    pergunta_id: UUID
    model_config = {
        "from_attributes": True
    }