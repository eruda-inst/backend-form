from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from typing import List
from app.dependencies.permissoes import require_permission




router = APIRouter(prefix="/permissoes", tags=["Permissões"])

@router.get("/", response_model=List[schemas.PermissaoResponse], dependencies=[require_permission("permissoes:ver")])
def listar_permissoes(db: Session = Depends(get_db)):
    permissoes = db.query(models.Permissao).all()
    return permissoes
