import os
import subprocess
from importlib.metadata import version as pkg_version, PackageNotFoundError

def get_app_version() -> str:
    """Retorna a versão da aplicação priorizando BACKEND_VERSION; fallback para versão do pacote ou git; senão 'dev'."""
    v = os.getenv("BACKEND_VERSION")
    if v:
        return v
    try:
        return pkg_version("backend-form")
    except PackageNotFoundError:
        pass
    try:
        return subprocess.check_output(["git", "describe", "--tags", "--always"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "dev"