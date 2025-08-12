from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user_ws, get_current_user
from app import models

def require_permission_callable_ws(codigo_permissao: str):
    """Retorna um callable que valida a permissão e devolve o usuário autenticado."""
    def dependency(current_user: models.Usuario = Depends(get_current_user_ws)):
        """Valida a permissão informada e retorna o usuário autenticado."""
        codigos = {p.codigo for p in (current_user.grupo.permissoes or [])} if current_user and current_user.grupo else set()
        if codigo_permissao not in codigos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{codigo_permissao}' é requerida"
            )
        return current_user
    return dependency

def require_permission_callable(codigo_permissao: str):
    """Retorna um callable que valida a permissão e devolve o usuário autenticado."""
    def dependency(current_user: models.Usuario = Depends(get_current_user)):
        """Valida a permissão informada e retorna o usuário autenticado."""
        codigos = {p.codigo for p in (current_user.grupo.permissoes or [])} if current_user and current_user.grupo else set()
        if codigo_permissao not in codigos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{codigo_permissao}' é requerida"
            )
        return current_user
    return dependency

def require_permission(codigo_permissao: str):
    """Retorna um objeto Depends para uso direto no decorator dependencies=[...]."""
    return Depends(require_permission_callable(codigo_permissao))
