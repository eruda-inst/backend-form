from datetime import datetime
from typing import Dict, Any, Optional, Set
from app.schemas import ExportRow
import json


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


def resposta_para_export_row(resposta, perguntas_ids_permitidas: Optional[Set[str]] = None, label_attr: str = "texto") -> ExportRow:
    """Transforma Resposta em ExportRow.
    - Usa o texto da pergunta como chave (ex.: `Pergunta.texto`).
    - Se `perguntas_ids_permitidas` for fornecido, só inclui itens cujo `pergunta_id` esteja no conjunto.
    """
    dados: Dict[str, Any] = {}
    itens = getattr(resposta, "itens", []) or []
    for item in itens:
        pid = getattr(item, "pergunta_id", None)
        if perguntas_ids_permitidas is not None and (pid is None or str(pid) not in perguntas_ids_permitidas):
            continue
        label = None
        if hasattr(item, "pergunta") and item.pergunta is not None:
            # tenta usar atributo de rótulo (por padrão, `texto`), senão cai para o id
            if hasattr(item.pergunta, label_attr) and getattr(item.pergunta, label_attr):
                label = str(getattr(item.pergunta, label_attr))
            elif hasattr(item.pergunta, "id") and item.pergunta.id is not None:
                label = str(item.pergunta.id)
        if label is None:
            label = str(pid) if pid is not None else ""
        valor = getattr(item, "valor", None)
        if valor is None and hasattr(item, "conteudo"):
            valor = getattr(item, "conteudo")
        if isinstance(valor, (dict, list)):
            valor = json.dumps(valor, ensure_ascii=False)
        dados[label] = valor
    criado = getattr(resposta, "criado_em", None)
    if isinstance(criado, datetime):
        criado_dt = criado
    else:
        criado_dt = datetime.fromisoformat(str(criado)) if criado else datetime.utcnow()
    rid = getattr(resposta, "id", None)
    rid_str = str(rid) if rid is not None else ""
    return ExportRow(
        id=rid_str,
        criado_em=criado_dt,
        dados=dados,
    )