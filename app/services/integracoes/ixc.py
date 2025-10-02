from typing import Any, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from .utils import mysql_dsn

def testar(cfg: Dict[str, Any]) -> bool:
    """Executa um teste SELECT 1 no banco de dados IXC."""
    dsn = mysql_dsn(cfg)
    engine: Engine = create_engine(dsn, pool_pre_ping=True, connect_args={"connect_timeout": 4})
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()