from sqlalchemy.orm import Session
from app.models import Grupo, Permissao
from app.data.permissoes_padrao import PERMISSOES_PADRAO


def seed_grupo_admin_e_permissoes(db: Session):
    grupo_admin = db.query(Grupo).filter(Grupo.nome == "admin").first()
    if not grupo_admin:
        grupo_admin = Grupo(nome="admin")
        db.add(grupo_admin)
        db.commit()
        db.refresh(grupo_admin)

    for permissao_data in PERMISSOES_PADRAO:
        codigo = permissao_data["codigo"]
        nome = permissao_data["nome"]

        permissao = db.query(Permissao).filter(Permissao.codigo == codigo).first()
        if not permissao:
            permissao = Permissao(codigo=codigo, nome=nome)
            db.add(permissao)
            db.commit()
            db.refresh(permissao)

        if permissao not in grupo_admin.permissoes:
            grupo_admin.permissoes.append(permissao)

    db.commit()
