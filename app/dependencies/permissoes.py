from fastapi import Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app import models

def require_permission(nome_permissao: str):
    def checker(current_user: models.Usuario = Depends(get_current_user)):
        permissoes_do_grupo = {p.nome for p in current_user.grupo.permissoes}
        if nome_permissao not in permissoes_do_grupo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão '{nome_permissao}' é requerida"
            )
        return True
    return Depends(checker)
