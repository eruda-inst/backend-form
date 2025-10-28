from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import schemas, crud, models
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissoes import require_permission
from app.utils.slugs import gerar_slug_publico

router = APIRouter(prefix="/formularios", tags=["Formulários"])

@router.post("/", response_model=schemas.FormularioOut, status_code=status.HTTP_201_CREATED, dependencies=[require_permission("formularios:criar")])
def criar_formulario(
    dados: schemas.FormularioCreate,
    db: Session = Depends(get_db),
    usuario_id: UUID = Depends(get_current_user)
):
    return crud.forms.criar_formulario(db, dados, usuario_id)


@router.get("/", response_model=list[schemas.FormularioOut], dependencies=[require_permission("formularios:ver")])
def listar_formularios(incluir_inativos: bool = False, db: Session = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    grupo_id = usuario.grupo.id
    return crud.forms.listar_formularios(db, grupo_id, incluir_inativos)

@router.get("/{formulario_id}", response_model=schemas.FormularioOut, dependencies=[require_permission("formularios:ver")])
def buscar_formulario(formulario_id: UUID, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    formulario = crud.buscar_formulario_por_id(db, formulario_id)
    if not formulario or not formulario.ativo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulário não encontrado")
    grupo_id = [current_user.grupo.id]
    tem_perm = (db.query(models.FormularioPermissao)
                .filter(models.FormularioPermissao.formulario_id == formulario_id,
                        models.FormularioPermissao.grupo_id.in_(grupo_id),
                        models.FormularioPermissao.pode_ver.is_(True))
                .first())
    if not tem_perm:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para ver este formulário")
    
    return formulario

@router.delete("/{formulario_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[require_permission("formularios:apagar")])
def deletar_formulario_route(
    formulario_id: UUID,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    """Remove um formulário se o usuário tiver permissão global ou ACL para apagar."""
    grupo_id = [usuario.grupo.id]
    tem_perm = (db.query(models.FormularioPermissao)
                .filter(models.FormularioPermissao.formulario_id == formulario_id,
                        models.FormularioPermissao.grupo_id.in_(grupo_id),
                        models.FormularioPermissao.pode_apagar.is_(True))
                        .first())
    if not tem_perm:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para apagar este formulário")
    ok = crud.deletar_formulario(db, formulario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")


@router.get("/{formulario_id}/slug", response_model=schemas.FormularioSlug, dependencies=[require_permission("formularios:ver")])
def obter_slug_formulario(formulario_id: UUID, db: Session = Depends(get_db)):
    """Obtém o slug de um formulário pelo ID."""
    formulario = crud.forms.obter_formulario_por_id(db, formulario_id)
    if not formulario or not formulario.ativo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formulário não encontrado")
    return {"slug_publico": formulario.slug_publico}
    
@router.get("/tipos-perguntas/", dependencies=[require_permission("formularios:criar")])
def listar_tipos():
    return [{"value": t.value, "label": t.name} for t in models.TipoPergunta]


@router.post("/{formulario_id}/restaurar", status_code=status.HTTP_204_NO_CONTENT, dependencies=[require_permission("formularios:restaurar")])
def restaurar_formulario_route(
    formulario_id: UUID,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    """Restaura um formulário se o usuário tiver permissão global ou ACL para restaurar."""
    if not crud.tem_permissao_formulario(db, usuario, formulario_id, "restaurar"):
        raise HTTPException(status_code=403, detail="Sem permissão para restaurar este formulário")
    ok = crud.restaurar_formulario(db, formulario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Formulário não encontrado ou já ativo")
    
@router.get("/publico/{slug}", response_model=schemas.FormularioPublicoResponse)
def obter_formulario_publico(slug: str, db: Session = Depends(get_db)):
    formulario = crud.forms.obter_formulario_publico_por_slug(db, slug)
    if not formulario:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    return {
        "titulo": formulario.titulo,
        "descricao": formulario.descricao,
        "unico_por_chave_modo": formulario.unico_por_chave_modo,
        "perguntas": formulario.perguntas,
        "ativo": formulario.ativo,
    }


@router.post("/{formulario_id}/publicar", status_code=status.HTTP_200_OK, dependencies=[require_permission("formularios:editar")])
def publicar_formulario(formulario_id: UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    """Ativa o acesso público do formulário e garante um slug público."""
    form = db.query(models.Formulario).filter(models.Formulario.id == formulario_id).first()
    grupo_id = [usuario.grupo.id]
    tem_perm = (db.query(models.FormularioPermissao)
                .filter(models.FormularioPermissao.formulario_id == formulario_id,
                        models.FormularioPermissao.grupo_id.in_(grupo_id),
                        models.FormularioPermissao.pode_editar.is_(True))
                .first())
    if not tem_perm:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar este formulário")
    if not form:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    if not form.slug_publico:
        form.slug_publico = gerar_slug_publico()
    form.recebendo_respostas = True
    db.commit()
    db.refresh(form)
    return {"slug_publico": form.slug_publico, "recebendo_respostas": form.recebendo_respostas}

@router.post("/{formulario_id}/despublicar", status_code=status.HTTP_200_OK, dependencies=[require_permission("formularios:editar")])
def despublicar_formulario(formulario_id: UUID, db: Session = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    """Desativa o acesso público do formulário."""
    form = db.query(models.Formulario).filter(models.Formulario.id == formulario_id).first()
    grupo_id = [usuario.grupo.id]
    tem_perm = (db.query(models.FormularioPermissao)
                .filter(models.FormularioPermissao.formulario_id == formulario_id,
                        models.FormularioPermissao.grupo_id.in_(grupo_id),
                        models.FormularioPermissao.pode_editar.is_(True))
                .first())
    if not tem_perm:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para editar este formulário")
    if not form:
        raise HTTPException(status_code=404, detail="Formulário não encontrado")
    form.recebendo_respostas = False
    db.commit()
    return {"slug_publico": form.slug_publico, "recebendo_respostas": form.recebendo_respostas}