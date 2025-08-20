from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional
from .grupo import GrupoResponse
from app.core.config import settings


class UsuarioBase(BaseModel):
    nome: str
    username: str
    genero: Optional[str] = None
    email: EmailStr
    ativo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    senha: str
    grupo_id: UUID


class UsuarioResponse(UsuarioBase):
    id: UUID
    criado_em: datetime
    grupo: GrupoResponse
    imagem: Optional[str] = None


    model_config = {
        "from_attributes": True
    }

    @field_validator("imagem", mode="before")
    @classmethod
    def make_full_url(cls, v: Optional[str]) -> Optional[str]:
        if v and settings.BASE_URL:
            return f"{settings.BASE_URL}{v}"
        return v


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


    model_config = {
        "from_attributes": True,
        "extra":"forbid"
    }

class UsuarioGrupoUpdate(BaseModel):
    grupo_id: UUID
