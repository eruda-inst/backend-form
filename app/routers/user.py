import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Request, File
from fastapi.responses import RedirectResponse, FileResponse
from app.utils.media import public_media_url, absolute_media_path, guess_mime_type
from app.core.config import settings
from app.utils.images import save_user_image, remove_media_file
from app.crud.user import atualizar_imagem_usuario
from sqlalchemy.orm import Session
from app import schemas, crud, database, models
from app.models import Usuario as UsuarioModel
from uuid import UUID
from app.dependencies.auth import get_current_user, is_admin
from app.dependencies.permissoes import require_permission
from app.security import hash_senha, gerar_token, gerar_refresh_token
from app.utils.permissoes import listar_permissoes_do_usuario


router = APIRouter(prefix="/usuarios", tags=["Cadastro"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.LoginResponse, status_code=status.HTTP_201_CREATED, dependencies=[require_permission('usuarios:criar')])
def criar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db), admin: models.Usuario = Depends(is_admin)):
    if crud.buscar_usuario_por_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    if crud.buscar_usuario_por_username(db, usuario.username):
        raise HTTPException(status_code=400, detail="Username já cadastrado")
    
    grupo = db.query(models.Grupo).filter(models.Grupo.id == usuario.grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=400, detail="Grupo não encontrado")

    novo_usuario = crud.criar_usuario(db, usuario)

    access_token = gerar_token({"sub": str(novo_usuario.id)})
    refresh_token = gerar_refresh_token({"sub": str(novo_usuario.id)})

    return {
        "id": str(novo_usuario.id),
        "username": novo_usuario.username,
        "email": novo_usuario.email,
        "firstName": novo_usuario.nome.split(" ")[0] if novo_usuario.nome else "",
        "lastName": " ".join(novo_usuario.nome.split(" ")[1:]) if novo_usuario.nome and len(novo_usuario.nome.split(" ")) > 1 else "",
        "gender": novo_usuario.genero if hasattr(novo_usuario, "genero") else None,
        "image": novo_usuario.imagem if hasattr(novo_usuario, "imagem") else None,
        "grupo": novo_usuario.grupo.nome if novo_usuario.grupo else None,
        "accessToken": access_token,
        "refreshToken": refresh_token
    }


@router.get("/", response_model=list[schemas.UsuarioResponse], dependencies=[require_permission('usuarios:ver')])
def listar(request: Request, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    usuarios = crud.listar_usuarios(db)
    for usuario in usuarios:
        if usuario.imagem:
            usuario.imagem = _url_da_imagem(usuario.imagem, request)
    return usuarios

@router.get("/{usuario_id}", response_model=schemas.UsuarioResponse, dependencies=[require_permission('usuarios:ver')])
def buscar_por_id(request: Request, usuario_id: str, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    usuario = crud.buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario.imagem = _url_da_imagem(usuario.imagem, request)
    return usuario


@router.get("/{usuario_id}/permissoes")
def permissoes_do_usuario(usuario_id: UUID, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    permissoes = listar_permissoes_do_usuario(usuario)

    return {
        "usuario": usuario.nome,
        "grupo": usuario.grupo.nome if usuario.grupo else None,
        "permissoes": permissoes
    }


@router.put("/{usuario_id}", response_model=schemas.UsuarioResponse)
def atualizar_usuario(
    usuario_id: str,
    dados: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user)
):
    """Permite que o usuário edite os próprios dados sem alterar grupo."""
    if str(user.id) != usuario_id:
        raise HTTPException(status_code=403, detail="Você só pode editar seus próprios dados")

    usuario = crud.buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    payload = dados.model_dump(exclude_unset=True)
    campos_bloqueados = {"grupo_id", "grupo_nome", "grupo"}
    if "grupo_id" in payload:
        raise HTTPException(status_code=403, detail="Você não pode alterar o próprio grupo")
    if any(campo in payload for campo in campos_bloqueados):
        raise HTTPException(status_code=403, detail="Não é permitido alterar o grupo do usuário")

    for campo, valor in payload.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario

@router.put("/grupo/{usuario_id}", response_model=schemas.UsuarioResponse, dependencies=[require_permission("usuarios:editar")])
def atualizar_grupo_usuario(
    usuario_id: UUID,
    dados: schemas.UsuarioGrupoUpdate,
    db: Session = Depends(get_db),
):
    """Altera apenas o grupo de um usuário quando o solicitante tem permissão."""
    usuario = crud.buscar_usuario_por_id(db, str(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.grupo_id = dados.grupo_id
    db.commit()
    db.refresh(usuario)
    return usuario



@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[require_permission('usuarios:deletar')])
def deletar(usuario_id: UUID, db: Session = Depends(get_db), admin: models.Usuario = Depends(get_current_user)):
    usuario = crud.buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usuario.id == admin.id:
        raise HTTPException(status_code=403, detail="Você não pode excluir a si mesmo por esta rota")

    if usuario.grupo.nome == "admin":
        raise HTTPException(status_code=403, detail="Não é permitido excluir um administrador")

    crud.deletar_usuario(db, usuario_id)




@router.patch("/{usuario_id}/senha", response_model=schemas.UsuarioResponse)
def alterar_senha(
    usuario_id: str,
    dados: schemas.AlterarSenhaRequest,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user)
):
    usuario_alvo = crud.buscar_usuario_por_id(db, usuario_id)
    if not usuario_alvo:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.id != usuario_alvo.id and user.grupo.nome != "admin":
        raise HTTPException(status_code=403, detail="Você não tem permissão para alterar essa senha")

    usuario_alvo.senha = hash_senha(dados.senha)
    db.commit()
    db.refresh(usuario_alvo)
    return usuario_alvo



def _url_da_imagem(rel_path: str, request: Request) -> str:
    """Retorna URL absoluta para a imagem a partir do caminho relativo."""
    if not rel_path:
        return ""
    base = (str(settings.BASE_URL).rstrip("/") if settings.BASE_URL else str(request.base_url).rstrip("/"))
    return f"{base}{settings.MEDIA_URL}/{rel_path}"

@router.post("/me/imagem")
async def enviar_imagem_perfil_me(
    request: Request,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    """Recebe e salva a imagem de perfil do usuário autenticado e retorna metadados e URL."""
    try:
        rel = save_user_image(arquivo, str(usuario.id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if usuario.imagem:
        remove_media_file(usuario.imagem)
    usuario = atualizar_imagem_usuario(db, usuario.id, rel)
    return {
        "usuario_id": str(usuario.id),
        "imagem": usuario.imagem,
        "url": _url_da_imagem(usuario.imagem, request),
    }


@router.put("/me/imagem")
async def atualizar_imagem_perfil_me(
    request: Request,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    """Atualiza a imagem de perfil do usuário autenticado e retorna metadados e URL."""
    try:
        rel = save_user_image(arquivo, str(usuario.id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if usuario.imagem:
        remove_media_file(usuario.imagem)
    usuario = atualizar_imagem_usuario(db, usuario.id, rel)
    return {
        "usuario_id": str(usuario.id),
        "imagem": usuario.imagem,
        "url": _url_da_imagem(usuario.imagem, request),
    }


@router.get("/me/imagem")
def obter_imagem_perfil_me(request: Request, usuario: models.Usuario = Depends(get_current_user)):
    """Redireciona para a URL pública da imagem de perfil do usuário autenticado."""
    if not usuario.imagem:
        raise HTTPException(status_code=404, detail="Imagem não cadastrada")
    return RedirectResponse(public_media_url(usuario.imagem, request))

@router.get("/me/imagem/raw")
def obter_imagem_perfil_me_raw(usuario: models.Usuario = Depends(get_current_user)):
    """Retorna o arquivo binário da imagem de perfil do usuário autenticado."""
    if not usuario.imagem:
        raise HTTPException(status_code=404, detail="Imagem não cadastrada")
    abs_path = absolute_media_path(usuario.imagem)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(abs_path, media_type=guess_mime_type(usuario.imagem))

@router.get("/{usuario_id}/imagem", dependencies=[require_permission("usuarios:ver")])
def obter_imagem_perfil_por_id(usuario_id: UUID, request: Request, db: Session = Depends(get_db)):
    """Redireciona para a URL pública da imagem de perfil do usuário por id."""
    u = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not u or not u.imagem:
        raise HTTPException(status_code=404, detail="Imagem não cadastrada")
    return RedirectResponse(public_media_url(u.imagem, request))

@router.get("/{usuario_id}/imagem/raw", dependencies=[require_permission("usuarios:ver")])
def obter_imagem_perfil_por_id_raw(usuario_id: UUID, db: Session = Depends(get_db)):
    """Retorna o arquivo binário da imagem de perfil do usuário por id."""
    u = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not u or not u.imagem:
        raise HTTPException(status_code=404, detail="Imagem não cadastrada")
    abs_path = absolute_media_path(u.imagem)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(abs_path, media_type=guess_mime_type(u.imagem))

