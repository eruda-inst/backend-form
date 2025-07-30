from pydantic import BaseModel
from typing import List
from uuid import UUID

class GrupoBase(BaseModel):
    nome: str

class GrupoCreate(GrupoBase):
    pass

class GrupoResponse(GrupoBase):
    id: UUID

    model_config = {
        "from_attributes": True
    }

class UsuarioVinculado(BaseModel):
    id: UUID
    nome: str
    email: str

class GrupoErroResponse(BaseModel):
    mensagem: str
    usuarios: List[UsuarioVinculado]

class PermissaoGrupoInput(BaseModel):
    permissoes: List[str]