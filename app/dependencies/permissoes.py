from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app import models

def require_permission(codigo_permissao: str):
    def checker(current_user: models.Usuario = Depends(get_current_user)):
        codigos_permissoes = {p.codigo for p in current_user.grupo.permissoes}
        if codigo_permissao not in codigos_permissoes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{codigo_permissao}' é requerida"
            )
        return True
    return Depends(checker)
