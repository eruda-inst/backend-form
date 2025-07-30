from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional

class UsuarioBase(BaseModel):
    nome: str
    username: str
    genero: Optional[str] = None
    imagem: Optional[str] = None
    email: EmailStr
    nivel: str = "visualizador"
    ativo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioResponse(UsuarioBase):
    id: UUID
    criado_em: datetime

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

    model_config = {
        "from_attributes": True
    }
