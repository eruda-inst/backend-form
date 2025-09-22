from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class IntegracaoIXCCreate(BaseModel):
    """Define os campos de entrada para criar a integração IXC."""
    endereco: str = Field(..., min_length=1, max_length=255)
    porta: int = Field(3306, ge=1, le=65535)
    usuario: str = Field(..., min_length=1, max_length=128)
    senha: str = Field(..., min_length=1, max_length=128)
    nome_banco: str = Field(..., min_length=1, max_length=128)
    habilitada: bool = False

class IntegracaoIXCEdit(BaseModel):
    """Define os campos permitidos para editar a integração IXC (sem alterar habilitação)."""
    endereco: Optional[str] = Field(None, min_length=1, max_length=255)
    porta: Optional[int] = Field(None, ge=1, le=65535)
    usuario: Optional[str] = Field(None, min_length=1, max_length=128)
    senha: Optional[str] = Field(None, min_length=1, max_length=128)
    nome_banco: Optional[str] = Field(None, min_length=1, max_length=128)

class IntegracaoIXCOut(BaseModel):
    """Define o formato de saída da integração IXC."""
    id: int
    endereco: str
    porta: int
    usuario: str
    nome_banco: str
    habilitada: bool
    endereco_completo: str
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)

class IntegracaoIXCHabilitacao(BaseModel):
    """Define o payload para habilitar ou desabilitar a integração IXC."""
    habilitada: bool = Field(...)


class IntegracaoIXCStatusOut(IntegracaoIXCOut):
    """Define o formato de saída com o status da conexão ao aplicar habilitação."""
    conexao_ok: bool