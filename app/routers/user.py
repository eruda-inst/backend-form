from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, crud, database, models
from app.models import Usuario as UsuarioModel
from app.dependencies.auth import get_optional_user, get_current_user, is_admin
from app.security import hash_senha, gerar_token, gerar_refresh_token



router = APIRouter(prefix="/usuarios", tags=["Cadastro"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.LoginResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db), admin: models.Usuario = Depends(is_admin)):
    if crud.buscar_usuario_por_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    if crud.buscar_usuario_por_username(db, usuario.username):
        raise HTTPException(status_code=400, detail="Username já cadastrado")

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
        "accessToken": access_token,
        "refreshToken": refresh_token
    }


@router.get("/", response_model=list[schemas.UsuarioResponse])
def listar(db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    return crud.listar_usuarios(db)

@router.get("/{usuario_id}", response_model=schemas.UsuarioResponse)
def buscar_por_id(usuario_id: str, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    usuario = crud.buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


@router.put("/{usuario_id}", response_model=schemas.UsuarioResponse)
def atualizar_usuario(
    usuario_id: str,
    dados: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user)
):
    if str(user.id) != usuario_id:
        raise HTTPException(status_code=403, detail="Você só pode editar seus próprios dados")

    usuario = crud.buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.nome = dados.nome
    usuario.email = dados.email
    usuario.nivel = dados.nivel
    usuario.ativo = dados.ativo
    usuario.username = dados.username
    usuario.genero = dados.genero if hasattr(dados, "genero") else usuario.genero
    usuario.imagem = dados.imagem if hasattr(dados, "imagem") else usuario.imagem

    db.commit()
    db.refresh(usuario)

    return usuario



@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar(usuario_id: str, db: Session = Depends(get_db), admin: models.Usuario = Depends(is_admin)):
    usuario = crud.buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usuario.nivel == "admin":
        raise HTTPException(status_code=403, detail="Não é permitido excluir um administrador")

    crud.deletar_usuario(db, usuario_id)


@router.get("/me", response_model=schemas.UsuarioResponse)
def perfil(current_user: models.Usuario = Depends(get_current_user)):
    return current_user

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

    if user.id != usuario_alvo.id and user.nivel != "admin":
        raise HTTPException(status_code=403, detail="Você não tem permissão para alterar essa senha")

    usuario_alvo.senha = hash_senha(dados.senha)
    db.commit()
    db.refresh(usuario_alvo)
    return usuario_alvo

