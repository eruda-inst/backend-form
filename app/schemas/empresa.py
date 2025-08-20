from pydantic import BaseModel, Field, HttpUrl, AnyUrl
from typing import Optional
from uuid import UUID



class EmpresaCreate(BaseModel):
    nome: str = Field(..., max_length=180)
    cnpj: str

class EmpresaUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=180)
    cnpj: Optional[str] = None
    logo_url: Optional[HttpUrl] = None 

from app.core.config import settings
from pydantic import field_validator

class EmpresaResponse(BaseModel):
    id: UUID
    nome: str
    cnpj: str
    logo_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

    @field_validator("logo_url", mode="before")
    @classmethod
    def make_full_url(cls, v: Optional[str]) -> Optional[str]:
        if v and settings.BASE_URL:
            return f"{settings.BASE_URL}{v}"
        return v

