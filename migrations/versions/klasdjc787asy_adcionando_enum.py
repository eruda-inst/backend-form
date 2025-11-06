

from alembic import op

# revision identifiers, used by Alembic.
revision = "klasdjc787asy"
down_revision = "c07586b7ae5c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE tipo_pergunta ADD VALUE IF NOT EXISTS 'multipla_escolha_personalizada'")


def downgrade() -> None:
    # Remover valor de ENUM em PostgreSQL exige recriar o tipo e recastar a coluna.
    # Mantemos como no-op para segurança.
    pass