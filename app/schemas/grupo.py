from pydantic import BaseModel
from typing import List
from uuid import UUID
from .permissao import PermissaoResponse
from typing import Optional




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

class GrupoComPermissoesResponse(BaseModel):
    id: UUID
    nome: str
    permissoes: List[PermissaoResponse]

    model_config = {
        "from_attributes": True
    }


class GrupoUpdate(BaseModel):
    nome: Optional[str] = None
    permissoes_codigos: List[str]

    model_config = {
        "from_attributes": True
    }
