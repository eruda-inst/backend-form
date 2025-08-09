from pydantic import BaseModel
from uuid import UUID
from typing import List


class PermissaoResponse(BaseModel):
    id: UUID
    codigo: str
    nome: str

    model_config = {
        "from_attributes": True
    }


class FormularioPermissaoIn(BaseModel):
    grupo_id: UUID | None = None
    grupo_nome: str | None = None
    pode_ver: bool = False
    pode_editar: bool = False
    pode_apagar: bool = False

class FormularioPermissaoOut(BaseModel):
    id: UUID
    formulario_id: UUID
    grupo_id: UUID
    grupo_nome: str
    pode_ver: bool
    pode_editar: bool
    pode_apagar: bool

    model_config = {"from_attributes": True}

class FormularioPermissaoBatchIn(BaseModel):
    itens: List[FormularioPermissaoIn]
