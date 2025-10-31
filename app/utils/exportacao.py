from datetime import datetime
from typing import Dict, Any
from app.schemas import ExportRow


def _flatten(obj: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Achata um dicionário aninhado em chaves com notação pontilhada."""
    items = []
    for k, v in obj.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)


def resposta_para_export_row(resposta) -> ExportRow:
    """Transforma um objeto Resposta do banco em um ExportRow com campos achatados."""
    dados = resposta.dados or {}
    if not isinstance(dados, dict):
        dados = {"valor": dados}

    dados_achatados = _flatten(dados)
    return ExportRow(
        id=str(resposta.id),
        criado_em=resposta.criado_em if isinstance(resposta.criado_em, datetime) else datetime.fromisoformat(resposta.criado_em),
        dados=dados_achatados,
    )