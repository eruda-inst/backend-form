import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import RedirectResponse, FileResponse
from app.core.config import settings
from app.utils.images import save_company_logo, remove_media_file
from app.crud.empresa import atualizar_logo_empresa, obter_unica_empresa
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database import get_db
from app.schemas.empresa import EmpresaUpdate, EmpresaResponse
from app.crud import empresa as crud_empresa
from app.dependencies import require_permission
from app.utils.media import public_media_url, absolute_media_path, guess_mime_type


router = APIRouter(prefix="/empresa", tags=["Empresas"])

@router.get("/", response_model=EmpresaResponse, dependencies=[require_permission("empresa:ver")])
def listar_empresas_route(db: Session = Depends(get_db)):
    """Lista empresas."""
    return crud_empresa.buscar_empresa(db)

@router.put("/", response_model=EmpresaResponse, dependencies=[require_permission("empresa:editar")])
def atualizar_empresa_route(payload: EmpresaUpdate, db: Session = Depends(get_db)):
    """Atualiza uma empresa por id."""
    try:
        emp = crud_empresa.atualizar_empresa(db, payload)
        if not emp:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")
        return emp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
def _url_media(rel_path: str, request: Request) -> str:
    """Retorna a URL pública de um caminho relativo salvo em MEDIA_ROOT."""
    if not rel_path:
        return ""
    base = (str(settings.BASE_URL).rstrip("/") if settings.BASE_URL else str(request.base_url).rstrip("/"))
    return f"{base}{settings.MEDIA_URL}/{rel_path}"

@router.post("/logo", dependencies=[require_permission("empresa:editar")])
async def enviar_logo_empresa(
    request: Request,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Recebe e salva a logo da empresa única e retorna metadados e URL pública."""
    empresa = obter_unica_empresa(db)
    if not empresa:
        raise HTTPException(status_code=404, detail="Nenhuma empresa cadastrada")
    try:
        rel = save_company_logo(arquivo, str(empresa.id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if empresa.logo_url:
        remove_media_file(empresa.logo_url)
    empresa = atualizar_logo_empresa(db, empresa.id, rel)
    return {
        "empresa_id": str(empresa.id),
        "logo": empresa.logo_url,
        "url": _url_media(empresa.logo_url, request),
    }


@router.get("/logo", dependencies=[require_permission("empresa:ver")])
def obter_logo_empresa(request: Request, db: Session = Depends(get_db)):
    """Redireciona para a URL pública da logo da empresa única."""
    empresa = obter_unica_empresa(db)
    if not empresa or not empresa.logo_url:
        raise HTTPException(status_code=404, detail="Logo não cadastrada")
    return RedirectResponse(public_media_url(empresa.logo_url, request))

@router.get("/logo/raw", dependencies=[require_permission("empresa:ver")])
def obter_logo_empresa_raw(db: Session = Depends(get_db)):
    """Retorna o arquivo binário da logo da empresa única."""
    empresa = obter_unica_empresa(db)
    if not empresa or not empresa.logo_url:
        raise HTTPException(status_code=404, detail="Logo não cadastrada")
    abs_path = absolute_media_path(empresa.logo_url)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(abs_path, media_type=guess_mime_type(empresa.logo_url))
