from pydantic import BaseModel
from uuid import UUID


class PermissaoResponse(BaseModel):
    id: UUID
    codigo: str
    nome: str

    model_config = {
        "from_attributes": True
    }


