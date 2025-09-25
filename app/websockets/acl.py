# app/ws/acl_ws.py
from typing import Iterable, Set
from uuid import UUID
from sqlalchemy.orm import Session
from app import models

def _ids_grupos(usuario) -> Set[UUID]:
    """Retorna os IDs dos grupos do usuário."""
    grupos = getattr(usuario, "grupos", None) or []
    return {g.id for g in grupos if getattr(g, "id", None)}

def _permissoes_globais(usuario) -> Set[str]:
    """Retorna os códigos de permissões globais agregados via grupos do usuário."""
    grupos = getattr(usuario, "grupos", None) or []
    codigos: Set[str] = set()
    for g in grupos:
        for p in getattr(g, "permissoes", []) or []:
            c = getattr(p, "codigo", None)
            if c:
                codigos.add(c)
    return codigos

def usuario_pode_editar_formulario(db: Session, usuario, formulario_id: UUID) -> bool:
    """Indica se o usuário pode editar o formulário informado."""
    if "formularios:editar" in _permissoes_globais(usuario):
        return True
    grupos_ids = _ids_grupos(usuario)
    if not grupos_ids:
        return False
    q = (
        db.query(models.FormularioPermissao)
          .filter(models.FormularioPermissao.formulario_id == formulario_id)
          .filter(models.FormularioPermissao.grupo_id.in_(list(grupos_ids)))
    )
    return any(bool(r.pode_editar) for r in q.all())

def usuario_pode_ver_respostas(db: Session, usuario, formulario_id: UUID) -> bool:
    """Indica se o usuário pode ver as respostas do formulário informado."""
    perms = _permissoes_globais(usuario)
    if "formularios:gerenciar_todos" in perms:
        return True
    if "respostas:ver" not in perms:
        return False
    grupos_ids = _ids_grupos(usuario)
    if not grupos_ids:
        return False
    q = (
        db.query(models.FormularioPermissao)
          .filter(models.FormularioPermissao.formulario_id == formulario_id)
          .filter(models.FormularioPermissao.grupo_id.in_(list(grupos_ids)))
    )
    return any(bool(r.pode_ver) for r in q.all())
