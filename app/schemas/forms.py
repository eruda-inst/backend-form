from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from .perguntas import PerguntaCreate, PerguntaUpdatePayload, PerguntaOut


class FormularioBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    unico_por_chave_modo: str = "none"
    recebendo_respostas: Optional[bool] = True


class FormularioCreate(FormularioBase):
    perguntas: Optional[List[PerguntaCreate]] = []

class FormularioOut(FormularioBase):
    id: UUID
    criado_em: Optional[datetime] = None
    perguntas: list[PerguntaOut] = []
    ativo: bool
    slug_publico: Optional[str] = None
    unico_por_chave_modo: str



    model_config = {
        "from_attributes": True
    }

class FormularioSlug(BaseModel):
    slug_publico: str


class FormularioPublicoResponse(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    perguntas: List[PerguntaOut]

    model_config = {
        "from_attributes": True
    }

class FormularioUpdatePayload(BaseModel):
    formulario_id: UUID
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    recebendo_respostas: Optional[bool] = None
    ativo: Optional[bool] = None
    perguntas_adicionadas: Optional[List[PerguntaUpdatePayload]] = []
    perguntas_editadas: Optional[List[PerguntaUpdatePayload]] = []
    perguntas_removidas: Optional[List[UUID]] = []
    model_config = ConfigDict(extra='forbid')

class FormularioVersaoBase(BaseModel):
    versao: int
    nome: str
    perguntas_json: Any 

class FormularioVersaoCreate(FormularioVersaoBase):
    formulario_id: UUID
    criado_por_id: UUID

class FormularioVersaoOut(FormularioVersaoBase):
    id: UUID
    formulario_id: UUID
    criado_em: datetime
    criado_por_id: UUID

    class Config:
        from_attributes = True

class EdicaoFormularioBase(BaseModel):
    campo: str
    valor_antigo: str | None = None
    valor_novo: str | None = None

class EdicaoFormularioCreate(EdicaoFormularioBase):
    formulario_id: UUID
    usuario_id: UUID

class EdicaoFormularioOut(EdicaoFormularioBase):
    id: UUID
    formulario_id: UUID
    usuario_id: UUID
    data_edicao: datetime

    class Config:
        from_attributes = True


    

