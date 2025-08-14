from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from uuid import UUID



class EmpresaCreate(BaseModel):
    nome: str = Field(..., max_length=180)
    cnpj: str
    logo_url: Optional[HttpUrl] = None


class EmpresaUpdate(BaseModel):
    nome: Optional[str] = Field(None, max_length=180)
    cnpj: Optional[str] = None
    logo_url: Optional[HttpUrl] = None 

class EmpresaResponse(BaseModel):
    id: UUID
    nome: str
    cnpj: str
    logo_url: Optional[HttpUrl] = None
    class Config:
        from_attributes = True

