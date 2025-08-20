from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UsuarioCreate
from app.schemas.empresa import EmpresaCreate
from app.crud.user import existe_admin, criar_usuario, get_usuario_admin, atualizar_imagem_usuario
from app.dependencies.auth import get_optional_user
from app.models.grupo import Grupo
from app.models.user import Usuario
from app.crud.grupo import existe_grupo_admin
from app.crud.empresa import buscar_empresa, criar_empresa, atualizar_logo_empresa
from app.utils.images import save_user_image, save_company_logo, remove_media_file
import json
from app.schemas.setup import SetupResponse

router = APIRouter(prefix="/setup", tags=["Setup"])

@router.post("/", response_model=SetupResponse)
def setup(
    db: Session = Depends(get_db),
    empresa_data: str = Form(...),
    usuario_data: str = Form(...),
    logo_empresa: UploadFile = File(None),
    imagem_usuario: UploadFile = File(None),
):
    """
    Realiza a configuração inicial do sistema, criando a empresa e o primeiro usuário (admin).
    """
    if existe_admin(db):
        raise HTTPException(status_code=403, detail="Setup já foi realizado")

    try:
        empresa_payload = EmpresaCreate(**json.loads(empresa_data))
        usuario_payload = UsuarioCreate(**json.loads(usuario_data))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON inválido nos dados do formulário.")

    # Criar grupo admin se não existir
    grupo_admin = db.query(Grupo).filter(Grupo.nome == "admin").first()
    if not grupo_admin:
        grupo_admin = Grupo(nome="admin")
        db.add(grupo_admin)
        db.commit()
        db.refresh(grupo_admin)

    # Criar empresa
    empresa_existente = buscar_empresa(db)
    if empresa_existente:
        raise HTTPException(status_code=409, detail="Empresa já cadastrada.")
    
    db_empresa = criar_empresa(db, empresa_payload)
    if logo_empresa:
        try:
            rel_path = save_company_logo(logo_empresa, str(db_empresa.id))
            atualizar_logo_empresa(db, db_empresa.id, rel_path)
        except ValueError as e:
            # Não ideal, mas evita falha do setup por erro de imagem
            print(f"Erro ao salvar logo da empresa: {e}")


    # Criar usuário admin
    dados_usuario = usuario_payload.model_dump()
    dados_usuario["grupo_id"] = grupo_admin.id
    usuario_create_com_grupo = UsuarioCreate(**dados_usuario)
    db_user = criar_usuario(db, usuario_create_com_grupo)

    if imagem_usuario:
        try:
            rel_path = save_user_image(imagem_usuario, str(db_user.id))
            atualizar_imagem_usuario(db, db_user.id, rel_path)
        except ValueError as e:
            print(f"Erro ao salvar imagem do usuário: {e}")

    db.refresh(db_user)
    db.refresh(db_empresa)
    return {"empresa": db_empresa, "usuario": db_user}


@router.get("/status")
def status(db: Session = Depends(get_db), user: Usuario | None = Depends(get_optional_user)):
    admin_existe = existe_admin(db)
    grupo_admin_existe = existe_grupo_admin(db)
    usuario_admin = get_usuario_admin(db)

    return {
        "grupo_admin_existe": grupo_admin_existe,
        "admin_existe": admin_existe,
        "autenticado": user is not None,
        "usuario": {
            "id": str(user.id),
            "nome": user.nome,
            "email": user.email,
            "grupo": user.grupo.nome if user.grupo else None,
        } if user else None,
        "usuario_admin": {
            "id": str(usuario_admin.id),
            "nome": usuario_admin.nome,
            "email": usuario_admin.email,
            "grupo": usuario_admin.grupo.nome if usuario_admin.grupo else None,
        } if usuario_admin else None
    }