import anyio
from fastapi import Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload, with_loader_criteria
from app import models, schemas, crud
from uuid import uuid4, UUID
from app.dependencies.auth import get_current_user
from app.websockets.notificadores_forms import notificar_formulario_criado, notificar_formulario_apagado, notificar_formulario_atualizado
from datetime import datetime
from typing import Optional, Iterable, Dict, Any, Set
import io, csv, json
import pytz
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from app.schemas.exportacao import ExportRow
from app.utils.exportacao import resposta_para_export_row


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
            descricao=getattr(pergunta_data, "descricao", None),
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
            descricao=p.get("descricao"),
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

        for campo in ["texto", "descricao", "obrigatoria", "ordem_exibicao", "escala_min", "escala_max"]:
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

def _iter_export_rows(
    db: Session,
    formulario_id: UUID,
    inicio: Optional[datetime],
    fim: Optional[datetime],
    perguntas_ids_permitidas: Optional[Set[str]] = None,
) -> Iterable[ExportRow]:
    """Itera respostas do formulário aplicando filtros temporais e (opcionalmente) filtra colunas por IDs de perguntas permitidas."""
    q = (
        db.query(models.Resposta)
        .filter(models.Resposta.formulario_id == formulario_id)
        .order_by(models.Resposta.criado_em.asc())
    )
    if inicio:
        q = q.filter(models.Resposta.criado_em >= inicio)
    if fim:
        q = q.filter(models.Resposta.criado_em < fim)
    for resp in q.yield_per(500):
        row = resposta_para_export_row(resp)
        if perguntas_ids_permitidas is not None:
            row.dados = {k: v for k, v in row.dados.items() if k in perguntas_ids_permitidas}
        yield row

def _csv_header_from_row(row: ExportRow) -> list[str]:
    """Constrói cabeçalho padronizado para CSV/XLSX a partir de um ExportRow."""
    cols = ["id", "criado_em"]
    cols.extend(sorted(row.dados.keys()))
    return cols

async def _stream_csv(rows: Iterable[ExportRow], sep: str) -> Iterable[bytes]:
    """Gera CSV em streaming a partir de ExportRow."""
    it = iter(rows)
    try:
        first = next(it)
    except StopIteration:
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=sep, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["id", "criado_em"])
        yield buffer.getvalue().encode("utf-8")
        return

    header = _csv_header_from_row(first)
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=sep, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)
    writer.writerow([first.id, first.criado_em.isoformat(), *[first.dados.get(k, "") for k in header[2:]]])
    yield buffer.getvalue().encode("utf-8")
    buffer.seek(0)
    buffer.truncate(0)

    for row in it:
        writer.writerow([row.id, row.criado_em.isoformat(), *[row.dados.get(k, "") for k in header[2:]]])
        yield buffer.getvalue().encode("utf-8")
        buffer.seek(0)
        buffer.truncate(0)

async def _stream_ndjson(rows: Iterable[ExportRow]) -> Iterable[bytes]:
    """Gera NDJSON em streaming a partir de ExportRow."""
    for row in rows:
        payload = {"id": row.id, "criado_em": row.criado_em.isoformat(), **row.dados}
        yield (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

def _gerar_xlsx(rows: Iterable[ExportRow]) -> io.BytesIO:
    """Gera planilha XLSX em memória com base em ExportRow."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Respostas"

    rows_list = list(rows)
    if not rows_list:
        ws.append(["id", "criado_em"])
    else:
        header = _csv_header_from_row(rows_list[0])
        ws.append(header)
        for r in rows_list:
            ws.append([r.id, r.criado_em.isoformat(), *[r.dados.get(k, "") for k in header[2:]]])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

# app/crud/forms.py

def exportar_respostas(
    db: Session,
    formulario_id: UUID,
    inicio: Optional[datetime],
    fim: Optional[datetime],
    formato: str,
    fuso: str,
    separador: str,
    apenas_ativas: bool = False,
):
    """Exporta respostas de um formulário nos formatos CSV, NDJSON ou XLSX."""
    try:
        tz = pytz.timezone(fuso)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fuso horário inválido")

    if inicio and inicio.tzinfo is None:
        inicio = tz.localize(inicio)
    if fim and fim.tzinfo is None:
        fim = tz.localize(fim)

    existe = (
        db.query(models.Resposta.id)
        .filter(models.Resposta.formulario_id == formulario_id)
        .limit(1)
        .first()
    )
    if not existe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulário não encontrado ou sem respostas")

    perguntas_ativas_ids: Optional[Set[str]] = None
    if apenas_ativas:
        perguntas_ativas_ids = {
            str(pid)
            for (pid,) in db.query(models.Pergunta.id)
            .filter(models.Pergunta.formulario_id == formulario_id, models.Pergunta.ativa.is_(True))
            .all()
        }

    rows = _iter_export_rows(db, formulario_id, inicio, fim, perguntas_ids_permitidas=perguntas_ativas_ids)

    formato = (formato or "").lower()  # robustez
    if formato == "csv":
        filename = f"form_{formulario_id}_respostas.csv"
        generator = _stream_csv(rows, separador)
        return StreamingResponse(generator, media_type="text/csv",
                                 headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    if formato == "ndjson":
        filename = f"form_{formulario_id}_respostas.ndjson"
        generator = _stream_ndjson(rows)
        return StreamingResponse(generator, media_type="application/x-ndjson",
                                 headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    if formato == "xlsx":
        filename = f"form_{formulario_id}_respostas.xlsx"
        buf = _gerar_xlsx(rows)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato inválido; use csv, ndjson ou xlsx")
