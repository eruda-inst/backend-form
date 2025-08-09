
from sqlalchemy.orm import Session
from app import models, schemas
from typing import Literal, Optional, List
from uuid import UUID


Acao = Literal["ver", "editar", "apagar"]

def buscar_acl(db: Session, formulario_id, grupo_id) -> Optional[models.FormularioPermissao]:
    """Retorna a ACL de um grupo para um formulário, se existir."""
    return (
        db.query(models.FormularioPermissao)
        .filter(
            models.FormularioPermissao.formulario_id == formulario_id,
            models.FormularioPermissao.grupo_id == grupo_id,
        )
        .first()
    )

def tem_permissao_formulario(db: Session, usuario, formulario_id, acao: Acao) -> bool:
    """Avalia se o usuário tem permissão global ou ACL para executar a ação no formulário."""
    permissoes = getattr(usuario, "permissoes_codigos", []) or []
    if "formularios:gerenciar_todos" in permissoes:
        return True
    if acao == "ver" and "formularios:ver" in permissoes:
        return True
    if acao == "editar" and "formularios:editar" in permissoes:
        return True
    if acao == "apagar" and "formularios:apagar" in permissoes:
        return True

    acl = buscar_acl(db, formulario_id, getattr(usuario, "grupo_id", None))
    if not acl:
        return False
    if acao == "ver":
        return bool(acl.pode_ver)
    if acao == "editar":
        return bool(acl.pode_editar)
    if acao == "apagar":
        return bool(acl.pode_apagar)
    return False


def _resolver_grupo(db: Session, grupo_id: Optional[UUID], grupo_nome: Optional[str]) -> models.Grupo | None:
    if grupo_id:
        return db.query(models.Grupo).filter(models.Grupo.id == grupo_id).first()
    if grupo_nome:
        return db.query(models.Grupo).filter(models.Grupo.nome == grupo_nome).first()
    return None

def upsert_acl(db: Session, formulario_id: UUID, data: schemas.FormularioPermissaoIn) -> models.FormularioPermissao:
    """Cria ou atualiza a ACL de um grupo para um formulário."""
    grupo = _resolver_grupo(db, data.grupo_id, data.grupo_nome)
    if not grupo:
        raise ValueError("grupo não encontrado")

    registro = (
        db.query(models.FormularioPermissao)
        .filter(
            models.FormularioPermissao.formulario_id == formulario_id,
            models.FormularioPermissao.grupo_id == grupo.id,
        )
        .first()
    )
    if not registro:
        registro = models.FormularioPermissao(
            formulario_id=formulario_id,
            grupo_id=grupo.id,
            pode_ver=data.pode_ver,
            pode_editar=data.pode_editar,
            pode_apagar=data.pode_apagar,
        )
        db.add(registro)
    else:
        registro.pode_ver = data.pode_ver
        registro.pode_editar = data.pode_editar
        registro.pode_apagar = data.pode_apagar

    db.commit()
    db.refresh(registro)
    return registro

def remover_acl(db: Session, formulario_id: UUID, grupo_id: UUID) -> bool:
    """Remove a ACL de um grupo para um formulário."""
    q = (
        db.query(models.FormularioPermissao)
        .filter(
            models.FormularioPermissao.formulario_id == formulario_id,
            models.FormularioPermissao.grupo_id == grupo_id,
        )
    )
    if not q.first():
        return False
    q.delete()
    db.commit()
    return True

def listar_acl(db: Session, formulario_id: UUID) -> List[models.FormularioPermissao]:
    """Lista todas as ACLs de um formulário."""
    return (
        db.query(models.FormularioPermissao)
        .filter(models.FormularioPermissao.formulario_id == formulario_id)
        .all()
    )


def grant_all(db, formulario_id, grupo_id):
    """Concede todas as permissões de ACL para um grupo em um formulário."""
    payload = schemas.FormularioPermissaoIn(grupo_id=grupo_id, pode_ver=True, pode_editar=True, pode_apagar=True)
    return upsert_acl(db, formulario_id, payload)