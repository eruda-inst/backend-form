from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional
from .grupo import GrupoResponse


class UsuarioBase(BaseModel):
    nome: str
    username: str
    genero: Optional[str] = None
    imagem: Optional[str] = None
    email: EmailStr
    ativo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    senha: str
    grupo_id: UUID


class UsuarioResponse(UsuarioBase):
    id: UUID
    criado_em: datetime
    grupo: GrupoResponse


    model_config = {
        "from_attributes": True
    }


class AlterarSenhaRequest(BaseModel):
    senha: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    nivel: Optional[str] = None
    ativo: Optional[bool] = None
    genero: Optional[str] = None
    imagem: Optional[str] = None
    grupo_id: Optional[UUID] = None


    model_config = {
        "from_attributes": True
    }
