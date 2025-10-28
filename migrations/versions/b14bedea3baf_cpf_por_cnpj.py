"""cpf por cnpj

Revision ID: b14bedea3baf
Revises: c6b257f48808
Create Date: 2025-10-27 18:46:10.041768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b14bedea3baf'
down_revision: Union[str, Sequence[str], None] = 'c6b257f48808'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # garante que o ENUM tipo_pergunta possua o valor 'cnpj'
    op.execute("ALTER TYPE tipo_pergunta ADD VALUE IF NOT EXISTS 'cnpj'")

    # renomeia a coluna cpf -> cnpj
    op.alter_column("respostas", "cpf", new_column_name="cnpj")

    # remove índice antigo (se existir)
    op.drop_index("ux_respostas_form_cpf_partial", table_name="respostas")

    # cria novo índice parcial para cnpj
    op.create_index(
        "ux_respostas_form_cnpj_partial",
        "respostas",
        ["formulario_id", "cnpj"],
        unique=True,
        postgresql_where=sa.text("cnpj IS NOT NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ux_respostas_form_cnpj_partial", table_name="respostas")
    op.create_index(
        "ux_respostas_form_cpf_partial",
        "respostas",
        ["formulario_id", "cpf"],
        unique=True,
        postgresql_where=sa.text("cpf IS NOT NULL"),
    )
    op.alter_column("respostas", "cnpj", new_column_name="cpf")
