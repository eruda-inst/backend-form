import anyio
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload, with_loader_criteria
from app import models, schemas, crud
from uuid import uuid4, UUID
from app.dependencies.auth import get_current_user
from app.websockets.notificadores_forms import notificar_formulario_criado, notificar_formulario_apagado, notificar_formulario_atualizado


def criar_formulario(db: Session, dados: schemas.FormularioCreate, usuario: models.Usuario = Depends(get_current_user)):
    """Cria um formulário com perguntas e garante ACL total para o grupo do criador e para o grupo admin."""
    formulario = models.Formulario(
        id=uuid4(),
        titulo=dados.titulo,
        descricao=dados.descricao,
        criado_por_id=usuario.id
    )
    db.add(formulario)
    db.flush()

    for ordem, pergunta_data in enumerate(dados.perguntas):
        pergunta = models.Pergunta(
            id=uuid4(),
            formulario_id=formulario.id,
            texto=pergunta_data.texto,
            tipo=pergunta_data.tipo,
            obrigatoria=pergunta_data.obrigatoria,
            ordem_exibicao=pergunta_data.ordem_exibicao or ordem,
            escala_min=pergunta_data.escala_min,
            escala_max=pergunta_data.escala_max
        )
        db.add(pergunta)

        if pergunta_data.tipo == "multipla_escolha":
            for idx, opcao in enumerate(pergunta_data.opcoes or []):
                db.add(models.Opcao(
                    id=uuid4(),
                    pergunta_id=pergunta.id,
                    texto=opcao.texto,
                    ordem=opcao.ordem or idx
                ))

    if getattr(usuario, "grupo_id", None):
        crud.grant_all(db, formulario.id, usuario.grupo_id)

    grupo_admin = db.query(models.Grupo).filter(models.Grupo.nome == "admin").first()
    if grupo_admin and grupo_admin.id != getattr(usuario, "grupo_id", None):
        crud.grant_all(db, formulario.id, grupo_admin.id)

    db.commit()
    db.refresh(formulario)
    anyio.from_thread.run(notificar_formulario_criado, str(formulario.id))
    return formulario


def listar_formularios(db: Session, incluir_inativos: bool = False):
    query = db.query(models.Formulario)
    if not incluir_inativos:
        query = query.filter(models.Formulario.ativo.is_(True))
    return query.all()

def obter_formulario_por_id(db: Session, formulario_id: str):
    return (
        db.query(models.Formulario)
        .filter(models.Formulario.id == formulario_id)
        .first()
    )

def buscar_formulario_por_id(db: Session, formulario_id: str):
    return (
        db.query(models.Formulario)
        .options(selectinload(models.Formulario.perguntas)
                 .selectinload(models.Pergunta.opcoes))
        .filter(models.Formulario.id == formulario_id, models.Pergunta.ativa==True)
        .first()
    )

BOOL_TRUE = {"true", "1", "t", "yes", "y"}
def _to_bool(v):
    if isinstance(v, bool): return v
    if isinstance(v, int): return v != 0
    if isinstance(v, str): return v.strip().lower() in BOOL_TRUE
    return bool(v)

def _parse_tipo(valor):
    try:
        return models.TipoPergunta(valor) if valor is not None else None
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tipo de pergunta inválido")

def atualizar_formulario_parcial(db, payload: dict):
    """Aplica alterações parciais em formulário, cria/edita perguntas e suas opções."""
    payload.pop("ativo", None)
    try:
        formulario_id = UUID(payload.get("formulario_id"))
    except Exception:
        return None

    formulario = (
        db.query(models.Formulario)
        .options(
            selectinload(models.Formulario.perguntas)
            .selectinload(models.Pergunta.opcoes)
        )
        .filter(models.Formulario.id == formulario_id)
        .first()
    )
    if not formulario or not formulario.ativo:
        return None

    if "titulo" in payload:
        formulario.titulo = payload["titulo"]
    if "descricao" in payload:
        formulario.descricao = payload["descricao"]
    if "recebendo_respostas" in payload:
        formulario.recebendo_respostas = _to_bool(payload["recebendo_respostas"])
    if "ativo" in payload:
        formulario.ativo = _to_bool(payload["ativo"])

    for p in payload.get("perguntas_adicionadas", []):
        nova = models.Pergunta(
            formulario_id=formulario_id,
            texto=p.get("texto"),
            tipo=models.TipoPergunta(p.get("tipo")),
            obrigatoria=p.get("obrigatoria", True),
            ordem_exibicao=p.get("ordem_exibicao"),
            escala_min=p.get("escala_min"),
            escala_max=p.get("escala_max"),
        )
        if nova.tipo == models.TipoPergunta.multipla_escolha and p.get("opcoes"):
            nova.opcoes = [
                models.Opcao(
                    texto=o["texto"],
                    ordem=(o.get("ordem") if o.get("ordem") is not None else i + 1)
                )
                for i, o in enumerate(p["opcoes"])
    ]
        db.add(nova)

    for p in payload.get("perguntas_editadas", []):
        pergunta = db.query(models.Pergunta).filter(models.Pergunta.id == p["id"]).first()
        if not pergunta:
            continue
        for campo in ["texto", "obrigatoria", "ordem_exibicao", "escala_min", "escala_max"]:
            if campo in p:
                setattr(pergunta, campo, p[campo])
        if "tipo" in p:
            pergunta.tipo = models.TipoPergunta(p["tipo"])
        if "opcoes" in p and pergunta.tipo == models.TipoPergunta.multipla_escolha:
            pergunta.opcoes.clear()
            for i, o in enumerate(p["opcoes"] or []):
                pergunta.opcoes.append(
                    models.Opcao(
                        texto=o["texto"],
                        ordem=(o.get("ordem") if o.get("ordem") is not None else i + 1)
                    )
                )

    for pergunta_id in payload.get("perguntas_removidas", []):
        try:
            pid = UUID(pergunta_id)
        except Exception:
            continue
        pergunta = (
            db.query(models.Pergunta)
                .filter(models.Pergunta.id == pid,
                        models.Pergunta.formulario_id == formulario_id
                )
                .first())
        if pergunta:
            pergunta.ativa = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    else:
        anyio.from_thread.run(notificar_formulario_atualizado, str(formulario_id))


    formulario = (
        db.query(models.Formulario)
        .options(
            with_loader_criteria(models.Pergunta, models.Pergunta.ativa == True),
            selectinload(models.Formulario.perguntas)
            .selectinload(models.Pergunta.opcoes)
        )
        .filter(models.Formulario.id == formulario_id)
        .first()
    )
    return formulario

def adicionar_pergunta(db: Session, dados: dict) -> models.Pergunta:
    nova = models.Pergunta(**dados)
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova



def deletar_formulario(db: Session, formulario_id: UUID) -> bool:
    """Remove um formulário pelo id e confirma a operação."""
    form = db.query(models.Formulario).filter(models.Formulario.id == formulario_id).first()
    if not form or not form.ativo:
        return False
    form.ativo = False
    db.commit()
    anyio.from_thread.run(notificar_formulario_apagado, str(formulario_id))

    return True


def restaurar_formulario(db: Session, formulario_id: UUID) -> bool:
    """Restaura um formulário desativado, marcando 'ativo=True'."""
    form = db.query(models.Formulario).filter(models.Formulario.id == formulario_id).first()
    if not form or form.ativo:
        return False
    form.ativo = True
    db.commit()
    return True

def obter_formulario_publico_por_slug(db: Session, slug: str) -> models.Formulario | None:
    """Retorna um formulário publicado com perguntas ativas e ordenadas pelo slug público."""
    return(
        db.query(models.Formulario)
        .options(selectinload(models.Formulario.perguntas)
                 .selectinload(models.Pergunta.opcoes))
        .filter(models.Formulario.slug_publico == slug, models.Pergunta.ativa==True)
        .first()
    )
