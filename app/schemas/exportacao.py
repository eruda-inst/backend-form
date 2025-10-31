from datetime import datetime
from typing import Any, Dict, Optional, Literal
from pydantic import BaseModel, Field


class ExportQuery(BaseModel):
    """Parâmetros de exportação de respostas de um formulário."""
    inicio: Optional[datetime] = Field(default=None)
    fim: Optional[datetime] = Field(default=None)
    formato: Literal["csv", "ndjson", "xlsx"] = "csv"
    fuso: str = "America/Bahia"
    separador: str = ","


class ExportRow(BaseModel):
    """Linha lógica de exportação contendo metadados e campos achatados da resposta."""
    id: str
    criado_em: datetime
    dados: Dict[str, Any]