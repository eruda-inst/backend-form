from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator, field_serializer


class TipoIntegracao(str, Enum):
    ixc = "ixc"
    opa_suite = "opa_suite"
    disparo_pro = "disparo_pro"
    smtp = "smtp"
    webhook = "webhook"


REQUIRED_BY_TIPO: Dict[TipoIntegracao, set[str]] = {
    TipoIntegracao.ixc: {"endereco", "porta", "usuario", "senha", "nome_banco"},
    TipoIntegracao.opa_suite: {"base_url", "token"},
    TipoIntegracao.disparo_pro: {"api_key"},
    TipoIntegracao.smtp: {"host", "porta", "usuario", "senha", "tls"},
    TipoIntegracao.webhook: {"url"},
}

SENSITIVE_KEYS = {"senha", "api_key", "token", "secret", "authorization"}


class IntegracaoCreate(BaseModel):
    """Define os campos de entrada para criar uma integração genérica."""

    tipo: TipoIntegracao = Field(...)
    config: Dict[str, Any] = Field(default_factory=dict)
    habilitada: bool = False

    @model_validator(mode="after")
    def _validate_required_by_tipo(self) -> "IntegracaoCreate":
        req = REQUIRED_BY_TIPO.get(self.tipo, set())
        missing = [k for k in req if k not in self.config]
        if missing:
            raise ValueError(f"Campos obrigatórios ausentes para '{self.tipo}': {', '.join(sorted(missing))}")
        return self


class IntegracaoEdit(BaseModel):
    """Define os campos permitidos para editar a integração genérica."""

    tipo: Optional[TipoIntegracao] = None
    config: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def _validate_if_tipo_and_config(self) -> "IntegracaoEdit":
        if self.tipo is not None and self.config is not None:
            req = REQUIRED_BY_TIPO.get(self.tipo, set())
            missing = [k for k in req if k not in self.config]
            if missing:
                raise ValueError(
                    f"Campos obrigatórios ausentes para '{self.tipo}' ao editar: {', '.join(sorted(missing))}"
                )
        return self


class IntegracaoOut(BaseModel):
    """Define o formato de saída da integração genérica."""

    id: int
    tipo: TipoIntegracao
    config: Dict[str, Any]
    habilitada: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("config")
    def _redact_config(self, v: Dict[str, Any]) -> Dict[str, Any]:
        redacted = {}
        for k, val in v.items():
            if k.lower() in SENSITIVE_KEYS and val is not None:
                redacted[k] = "***"
            else:
                redacted[k] = val
        return redacted


class IntegracaoHabilitacao(BaseModel):
    """Define o payload para habilitar ou desabilitar a integração genérica."""

    habilitada: bool = Field(...)


class IntegracaoStatusOut(IntegracaoOut):
    """Define o formato de saída com o status da conexão ao aplicar habilitação."""

    conexao_ok: bool