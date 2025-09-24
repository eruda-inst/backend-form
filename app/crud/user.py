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
        grupo_id=usuario.grupo_id,
        ativo=usuario.ativo,
        username=usuario.username,
        genero=usuario.genero
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

def get_usuario_admin(db: Session) -> models.Usuario | None:
    return db.query(models.Usuario).filter(models.Usuario.grupo.has(nome="admin")).first()


def existe_admin(db: Session) -> bool:
    return (
        db.query(models.Usuario)
        .join(models.Grupo)
        .filter(models.Grupo.nome == "admin")
        .first()
        is not None
    )

def deletar_usuario(db: Session, usuario_id: UUID) -> bool:
    usuario = buscar_usuario_por_id(db, usuario_id)
    print(usuario)
    if not usuario:
        return False

    if usuario.grupo.nome == "admin":
        return False
    
    db.delete(usuario)
    db.commit()

    return True


def deletar_me(db: Session, usuario_id: UUID) -> bool:
    usuario = buscar_usuario_por_id(db, usuario_id)
    if usuario:
        print("Deletando usuário:", usuario.id)
        db.delete(usuario)
        db.commit()
    else:
        print("Usuário não encontrado para deletar:", usuario_id)

    return True


def atualizar_imagem_usuario(db: Session, usuario_id, caminho_relativo: str) -> models.Usuario:
    """Atualiza o campo imagem do usuário e retorna o usuário atualizado."""
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise ValueError("Usuário não encontrado")
    usuario.imagem = caminho_relativo
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario

def obter_usuario_por_id(db: Session, usuario_id):
    """Retorna o usuário pelo id."""
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()


