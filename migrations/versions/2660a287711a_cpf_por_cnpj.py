"""cpf por cnpj

Revision ID: 2660a287711a
Revises: b14bedea3baf
Create Date: 2025-10-27 19:59:53.363023
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2660a287711a'
down_revision: Union[str, Sequence[str], None] = 'b14bedea3baf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema (idempotente)."""
    op.execute("ALTER TYPE tipo_pergunta ADD VALUE IF NOT EXISTS 'cnpj'")

    conn = op.get_bind()
    insp = sa.inspect(conn)

    cols = {c['name'] for c in insp.get_columns('respostas')}
    if 'cpf' in cols and 'cnpj' not in cols:
        op.alter_column('respostas', 'cpf', new_column_name='cnpj')
    elif 'cnpj' in cols:
        pass  # já existe
    else:
        op.add_column('respostas', sa.Column('cnpj', sa.String(length=18), nullable=True))

    idx_names = {i['name'] for i in insp.get_indexes('respostas')}

    if 'ux_respostas_form_cpf_partial' in idx_names:
        op.drop_index('ux_respostas_form_cpf_partial', table_name='respostas')

    if 'ux_respostas_form_cnpj_partial' not in idx_names:
        op.create_index(
            'ux_respostas_form_cnpj_partial',
            'respostas',
            ['formulario_id', 'cnpj'],
            unique=True,
            postgresql_where=sa.text('cnpj IS NOT NULL'),
        )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ux_respostas_form_cnpj_partial', table_name='respostas')
    op.create_index(
        'ux_respostas_form_cpf_partial',
        'respostas',
        ['formulario_id', 'cpf'],
        unique=True,
        postgresql_where=sa.text('cpf IS NOT NULL'),
    )
    conn = op.get_bind()
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('respostas')]
    if 'cnpj' in cols:
        op.alter_column('respostas', 'cnpj', new_column_name='cpf')
