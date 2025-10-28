from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class BlocoOut(BaseModel):
    id: UUID
    titulo: str
    descricao: Optional[str] = None
    ordem: int
    form_id: UUID

    class Config:
        from_attributes = True