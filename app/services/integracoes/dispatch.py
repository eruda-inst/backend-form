from typing import Any, Dict, Callable
from app.models.integracoes import Integracao
from . import ixc, smtp, webhook

TESTADORES: Dict[str, Callable[[Dict[str, Any]], bool]] = {
    "ixc": ixc.testar,
    "smtp": smtp.testar,
    "webhook": webhook.testar,
}

def testar_conexao(item: Integracao) -> bool:
    """Executa o teste de conexão conforme o tipo da integração."""
    tester = TESTADORES.get((item.tipo or "").lower())
    return tester(item.config or {}) if tester else True