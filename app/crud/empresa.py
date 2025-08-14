from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import exists
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate
from app.services.cnpj import validar_cnpj

def existe_empresa(db: Session) -> bool:
    """Retorna True se já existe uma empresa cadastrada."""
    return db.query(exists().where(Empresa.id.isnot(None))).scalar()

def buscar_empresa(db: Session) -> Optional[Empresa]:
    """Retorna a única empresa cadastrada ou None se não houver."""
    return db.query(Empresa).order_by(Empresa.nome.asc()).first()

def criar_empresa(db: Session, dados: EmpresaCreate) -> Empresa:
    """Cria a empresa se não existir outra; valida CNPJ e unicidade por nome/CNPJ."""
    if existe_empresa(db):
        raise ValueError("Já existe uma empresa cadastrada")
    if not validar_cnpj(dados.cnpj):
        raise ValueError("CNPJ inválido")
    if db.query(Empresa).filter(Empresa.cnpj == dados.cnpj).first():
        raise ValueError("CNPJ já cadastrado")
    if db.query(Empresa).filter(Empresa.nome == dados.nome).first():
        raise ValueError("Nome de empresa já cadastrado")
    emp = Empresa(nome=dados.nome, cnpj=dados.cnpj, logo_url=str(dados.logo_url) if dados.logo_url else None)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp

def atualizar_empresa(db: Session, dados: EmpresaUpdate) -> Optional[Empresa]:
    """Atualiza a única empresa existente; valida CNPJ e conflitos quando informados."""
    emp = buscar_empresa(db)
    if not emp:
        return None
    if dados.nome is not None:
        if db.query(Empresa).filter(Empresa.nome == dados.nome, Empresa.id != emp.id).first():
            raise ValueError("Nome de empresa já cadastrado")
        emp.nome = dados.nome
    if dados.cnpj is not None:
        if not validar_cnpj(dados.cnpj):
            raise ValueError("CNPJ inválido")
        if db.query(Empresa).filter(Empresa.cnpj == dados.cnpj, Empresa.id != emp.id).first():
            raise ValueError("CNPJ já cadastrado")
        emp.cnpj = dados.cnpj
    if dados.logo_url is not None:
        emp.logo_url = str(dados.logo_url)
    db.commit()
    db.refresh(emp)
    return emp
