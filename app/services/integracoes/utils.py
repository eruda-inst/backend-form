from typing import Any, Dict

def mysql_dsn(cfg: Dict[str, Any]) -> str:
    """Monta DSN MySQL/MariaDB compatível com SQLAlchemy+pymysql."""
    usuario = cfg.get("usuario", "")
    senha = cfg.get("senha", "")
    host = cfg.get("endereco", "")
    porta = cfg.get("porta", 3306)
    banco = cfg.get("nome_banco", "")
    return f"mysql+pymysql://{usuario}:{senha}@{host}:{porta}/{banco}"