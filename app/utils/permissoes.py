from app import models

def listar_permissoes_do_usuario(usuario: models.Usuario) -> list[str]:
    if not usuario.grupo or not usuario.grupo.permissoes:
        return []

    return [p.nome for p in usuario.grupo.permissoes]
