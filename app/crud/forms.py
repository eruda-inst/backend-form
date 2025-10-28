import anyio
from fastapi import Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload, with_loader_criteria
from app import models, schemas, crud
from uuid import uuid4, UUID
from app.dependencies.auth import get_current_user
from app.websockets.notificadores_forms import notificar_formulario_criado, notificar_formulario_apagado, notificar_formulario_atualizado


TIPOS_COM_OPCOES = {
    models.TipoPergunta.multipla_escolha,
    models.TipoPergunta.caixa_selecao,
}

def criar_formulario(db: Session, dados: schemas.FormularioCreate, usuario: models.Usuario = Depends(get_current_user)):
    """Cria um formulário com perguntas e garante ACL total para o grupo do criador e para o grupo admin."""
    formulario = models.Formulario(
        id=uuid4(),
        titulo=dados.titulo,
        descricao=dados.descricao,
        unico_por_chave_modo=dados.unico_por_chave_modo,
        criado_por_id=usuario.id
    )
    db.add(formulario)
    db.flush()

    bloco_padrao = models.Bloco(
        id=uuid4(),
        form_id=formulario.id,
        ordem=1,
        titulo="Bloco Padrão",
        descricao=None,
    )
    db.add(bloco_padrao)

    for ordem, pergunta_data in enumerate(dados.perguntas):
        bloco = db.query(models.Bloco).filter(models.Bloco.id == pergunta_data.bloco_id).first()
        if not bloco:
            raise HTTPException(status_code=400, detail="Bloco informado não existe")
        if bloco.form_id != formulario.id:
            raise HTTPException(status_code=400, detail="O bloco informado não pertence a este formulário")
        pergunta = models.Pergunta(
            id=uuid4(),
            formulario_id=formulario.id,
            bloco_id=pergunta_data.bloco_id,
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


def listar_formularios(db: Session, grupo_id: UUID, incluir_inativos: bool = False):
    query = (
        db.query(models.Formulario)
        .join(models.FormularioPermissao, models.Formulario.id == models.FormularioPermissao.formulario_id)
        .filter(
            models.FormularioPermissao.grupo_id == grupo_id,
            models.FormularioPermissao.pode_ver.is_(True),
        )
    )
    if not incluir_inativos:
        query = query.filter(models.Formulario.ativo == True)
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
                 .selectinload(models.Pergunta.opcoes),
                 selectinload(models.Formulario.blocos)
        )
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
            .selectinload(models.Pergunta.opcoes),
            selectinload(models.Formulario.blocos)
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
    if "unico_por_chave_modo" in payload:
        formulario.unico_por_chave_modo = payload["unico_por_chave_modo"]
    if "recebendo_respostas" in payload:
        formulario.recebendo_respostas = _to_bool(payload["recebendo_respostas"])
    if "ativo" in payload:
        formulario.ativo = _to_bool(payload["ativo"])
    for b in payload.get("blocos_adicionados", []):
        ordem = b.get("ordem")
        if ordem is None:
            max_ordem = db.query(func.coalesce(func.max(models.Bloco.ordem), 0)).filter(models.Bloco.form_id == formulario_id).scalar()
            ordem = int(max_ordem) + 1
        novo_bloco = models.Bloco(
            id=uuid4(),
            form_id=formulario_id,
            ordem=ordem,
            titulo=b.get("titulo") or "Novo bloco",
            descricao=b.get("descricao"),
        )
        db.add(novo_bloco)
    
    for b in payload.get("blocos_editados", []):
        bid = b.get("id")
        if not bid:
            continue
        bloco = db.query(models.Bloco).filter(models.Bloco.id == bid, models.Bloco.form_id == formulario_id).first()
        if not bloco:
            raise HTTPException(status_code=400, detail="Bloco não encontrado para este formulário")
        if "titulo" in b:
            bloco.titulo = b["titulo"]
        if "descricao" in b:
            bloco.descricao = b["descricao"]
        if "ordem" in b and b["ordem"] is not None:
            bloco.ordem = int(b["ordem"])

    for bloco_id in payload.get("blocos_removidos", []):
        try:
            bid = UUID(bloco_id)
        except Exception:
            continue
        bloco = db.query(models.Bloco).filter(models.Bloco.id == bid, models.Bloco.form_id == formulario_id).first()
        if not bloco:
            continue
        tem_perguntas = db.query(models.Pergunta.id)\
            .filter(models.Pergunta.bloco_id == bid, models.Pergunta.ativa == True)\
            .limit(1).first()
        if tem_perguntas:
            raise HTTPException(status_code=400, detail="Não é possível remover bloco com perguntas ativas")
        db.delete(bloco)

    for p in payload.get("perguntas_adicionadas", []):
        bloco_id = p.get("bloco_id")
        if not bloco_id:
            raise HTTPException(status_code=400, detail="bloco_id é obrigatório para adicionar perguntas")
        bloco = db.query(models.Bloco).filter(models.Bloco.id == bloco_id).first()
        if not bloco:
            raise HTTPException(status_code=400, detail="Bloco informado não existe")
        if str(bloco.form_id) != str(formulario_id):
            raise HTTPException(status_code=400, detail="O bloco informado não pertence a este formulário")
        
        nova = models.Pergunta(
            formulario_id=formulario_id,
            bloco_id=bloco_id,
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
        if "bloco_id" in p and p["bloco_id"] and str(p["bloco_id"]) != str(pergunta.bloco_id):
            novo_bloco = db.query(models.Bloco).filter(models.Bloco.id == p["bloco_id"]).first()
            if not novo_bloco:
                raise HTTPException(status_code=400, detail="Bloco informado não existe")
            if str(novo_bloco.form_id) != str(pergunta.formulario_id):
                raise HTTPException(status_code=400, detail="O bloco informado não pertence a este formulário")
            pergunta.bloco_id = p["bloco_id"]

        for campo in ["texto", "obrigatoria", "ordem_exibicao", "escala_min", "escala_max"]:
            if campo in p:
                setattr(pergunta, campo, p[campo])
        if "tipo" in p:
            pergunta.tipo = models.TipoPergunta(p["tipo"])
        if ("opcoes" in p) and (pergunta.tipo in TIPOS_COM_OPCOES):
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
            .selectinload(models.Pergunta.opcoes),
            selectinload(models.Formulario.blocos)
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
                 .selectinload(models.Pergunta.opcoes),
                 selectinload(models.Formulario.blocos)
        )
        .filter(models.Formulario.slug_publico == slug, models.Pergunta.ativa==True)
        .first()
    )
