from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from uuid import UUID
from schemas.grupo import GrupoErroResponse
from app.models.permissao import Permissao
from schemas.grupo import PermissaoGrupoInput



router = APIRouter(prefix="/grupos", tags=["Grupos"])

@router.post("/", response_model=schemas.GrupoResponse, status_code=status.HTTP_201_CREATED)
def criar_grupo(grupo: schemas.GrupoCreate, db: Session = Depends(get_db)):
    grupo_existente = db.query(models.Grupo).filter(models.Grupo.nome == grupo.nome).first()
    if grupo_existente:
        raise HTTPException(status_code=400, detail="Nome de grupo já cadastrado")

    novo_grupo = models.Grupo(nome=grupo.nome)
    db.add(novo_grupo)
    db.commit()
    db.refresh(novo_grupo)
    return novo_grupo


@router.delete("/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_grupo(grupo_id: UUID, db: Session = Depends(get_db)):
    grupo = db.query(models.Grupo).filter(models.Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    if grupo.nome == "admin":
        raise HTTPException(status_code=403, detail="O grupo admin não pode ser deletado")

    usuarios_vinculados = db.query(models.Usuario).filter(models.Usuario.grupo_id == grupo.id).all()
    if usuarios_vinculados:
        usuarios_data = [
            {"id": u.id, "nome": u.nome, "email": u.email}
            for u in usuarios_vinculados
        ]
        raise HTTPException(
            status_code=400,
            detail=GrupoErroResponse(
                mensagem="Existem usuários vinculados a este grupo",
                usuarios=usuarios_data
            ).model_dump()
        )
    db.delete(grupo)
    db.commit()

@router.post("/{grupo_id}/permissoes", status_code=status.HTTP_200_OK)
def adicionar_permissoes_ao_grupo(
    grupo_id: UUID,
    dados: PermissaoGrupoInput,
    db: Session = Depends(get_db)
):
    grupo = db.query(models.Grupo).filter(models.Grupo.id == grupo_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")

    for nome_permissao in dados.permissoes:
        permissao = db.query(Permissao).filter(Permissao.nome == nome_permissao).first()

        if not permissao:
            permissao = Permissao(nome=nome_permissao)
            db.add(permissao)
            db.commit()
            db.refresh(permissao)

        if permissao not in grupo.permissoes:
            grupo.permissoes.append(permissao)

    db.commit()
    return {"mensagem": "Permissões adicionadas com sucesso"}