import os
import mimetypes
from fastapi import Request
from app.core.config import settings

def public_media_url(rel_path: str, request: Request) -> str:
    """Retorna a URL pública absoluta para um caminho relativo em MEDIA_ROOT."""
    if not rel_path:
        return ""
    base = (str(settings.BASE_URL).rstrip("/") if settings.BASE_URL else str(request.base_url).rstrip("/"))
    return f"{base}{settings.MEDIA_URL}/{rel_path}"

def absolute_media_path(rel_path: str) -> str:
    """Retorna o caminho absoluto no filesystem para um caminho relativo salvo no banco."""
    return os.path.join(settings.MEDIA_ROOT, rel_path)

def guess_mime_type(rel_path: str) -> str:
    """Retorna o MIME type estimado a partir da extensão do arquivo."""
    mime, _ = mimetypes.guess_type(rel_path)
    return mime or "application/octet-stream"
