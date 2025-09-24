# versions/20250922_add_email_tel_cpf_enum.py
from alembic import op
from typing import Sequence, Union


revision = "20250922_add_email_tel_cpf_enum"
down_revision: Union[str, Sequence[str], None] = 'd25feab1557d'

def upgrade():
    op.execute("ALTER TYPE tipo_pergunta ADD VALUE IF NOT EXISTS 'email'")
    op.execute("ALTER TYPE tipo_pergunta ADD VALUE IF NOT EXISTS 'telefone'")
    op.execute("ALTER TYPE tipo_pergunta ADD VALUE IF NOT EXISTS 'cpf'")

def downgrade():
    # Postgres não permite remover valores de ENUM facilmente
    pass
