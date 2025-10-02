from typing import Any, Dict
import smtplib

def testar(cfg: Dict[str, Any]) -> bool:
    """Executa EHLO/STARTTLS e login opcional para validar SMTP."""
    host = cfg.get("host")
    porta = int(cfg.get("porta", 587))
    usuario = cfg.get("usuario")
    senha = cfg.get("senha")
    usar_tls = bool(cfg.get("tls", True))
    if not host:
        return False
    try:
        with smtplib.SMTP(host=host, port=porta, timeout=4) as server:
            server.ehlo()
            if usar_tls:
                server.starttls()
                server.ehlo()
            if usuario and senha:
                server.login(usuario, senha)
        return True
    except Exception:
        return False