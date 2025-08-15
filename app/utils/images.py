from fastapi import UploadFile
from app.core.config import settings
from uuid import uuid4
import os

def _ext_from_filename(filename: str) -> str:
    return os.path.splitext(filename)[1].lower() or ""

def _subdir_user(user_id: str) -> str:
    return os.path.join("users", user_id)

def save_user_image(file: UploadFile, user_id: str) -> str:
    """Valida e salva a imagem do usuário e retorna o caminho relativo dentro do MEDIA_ROOT."""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise ValueError("Tipo de arquivo não suportado")
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    subdir = _subdir_user(user_id)
    abs_subdir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(abs_subdir, exist_ok=True)
    ext = _ext_from_filename(file.filename or "")
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    name = f"{uuid4().hex}{ext}"
    abs_path = os.path.join(abs_subdir, name)
    size = 0
    with open(abs_path, "wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                try:
                    os.remove(abs_path)
                except FileNotFoundError:
                    pass
                raise ValueError("Arquivo excede o tamanho máximo")
            out.write(chunk)
    rel_path = os.path.join(subdir, name).replace("\\", "/")
    return rel_path

def remove_media_file(rel_path: str) -> None:
    """Remove um arquivo de mídia a partir do caminho relativo no MEDIA_ROOT."""
    if not rel_path:
        return
    abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
    try:
        os.remove(abs_path)
    except FileNotFoundError:
        pass


def save_company_logo(file: UploadFile, empresa_id: str) -> str:
    """Valida e salva a logo da empresa e retorna o caminho relativo dentro do MEDIA_ROOT."""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise ValueError("Tipo de arquivo não suportado")
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    subdir = os.path.join("companies", empresa_id)
    abs_subdir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(abs_subdir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    name = f"{uuid4().hex}{ext}"
    abs_path = os.path.join(abs_subdir, name)
    size = 0
    with open(abs_path, "wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                try:
                    os.remove(abs_path)
                except FileNotFoundError:
                    pass
                raise ValueError("Arquivo excede o tamanho máximo")
            out.write(chunk)
    rel_path = os.path.join(subdir, name).replace("\\", "/")
    return rel_path