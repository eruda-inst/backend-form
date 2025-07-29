from sqlalchemy.orm import Session
from uuid import UUID
from app import models, schemas
from app.security import hash_senha

def criar_usuario(db: Session, usuario: schemas.UsuarioCreate) -> models.Usuario:
    senha_hash = hash_senha(usuario.senha)
    db_usuario = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha=senha_hash,
        nivel=usuario.nivel,
        ativo=usuario.ativo,
        username=usuario.username,
        genero=usuario.genero,
        imagem=usuario.imagem
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def buscar_usuario_por_username(db: Session, username: str):
    return db.query(models.Usuario).filter(models.Usuario.username == username).first()

def buscar_usuario_por_email(db: Session, email: str) -> models.Usuario | None:
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def listar_usuarios(db: Session) -> list[models.Usuario]:
    return db.query(models.Usuario).all()

def buscar_usuario_por_id(db: Session, usuario_id: UUID) -> models.Usuario | None:
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

def atualizar_usuario(db: Session, usuario_id: UUID, dados: schemas.UsuarioCreate) -> models.Usuario | None:
    usuario = buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        return None

def existe_admin(db: Session) -> bool:
    return db.query(models.Usuario).filter(models.Usuario.nivel == "admin").first() is not None

def deletar_usuario(db: Session, usuario_id: UUID) -> bool:
    usuario = buscar_usuario_por_id(db, usuario_id)
    if not usuario:
        return False

    if usuario.nivel == "admin":
        return False

    db.delete(usuario)
    db.commit()
    return True


