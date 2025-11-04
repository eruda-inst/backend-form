"""add blocos and link perguntas to blocos (idempotent)"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
import uuid

# revision identifiers, used by Alembic.
revision: str = "239asd9acas"
down_revision: str = "2660a287711a"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Cria tabela blocos apenas se não existir
    if not insp.has_table("blocos"):
        op.create_table(
            "blocos",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column("titulo", sa.String(length=255), nullable=False),
            sa.Column("descricao", sa.Text(), nullable=True),
            sa.Column("ordem", sa.Integer(), nullable=False),
            sa.Column("form_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("formularios.id", ondelete="CASCADE"), nullable=False),
            sa.UniqueConstraint("form_id", "ordem", name="uq_blocos_form_ordem"),
        )

    # Adiciona coluna bloco_id se não existir
    cols = [c["name"] for c in insp.get_columns("perguntas")]
    if "bloco_id" not in cols:
        with op.batch_alter_table("perguntas") as batch_op:
            batch_op.add_column(sa.Column("bloco_id", postgresql.UUID(as_uuid=True), nullable=True))
            batch_op.create_foreign_key(
                "fk_perguntas_bloco_id",
                "blocos",
                ["bloco_id"],
                ["id"],
                ondelete="RESTRICT",
            )

    # Popula blocos e faz backfill se necessário
    conn = op.get_bind()
    forms = list(conn.execute(sa.text("SELECT id FROM formularios")))
    for (form_id,) in forms:
        # Verifica se já existe bloco para o formulário
        existing = conn.execute(
            sa.text("SELECT id FROM blocos WHERE form_id = :form_id"),
            {"form_id": str(form_id)},
        ).fetchone()
        if existing:
            bloco_id = existing[0]
        else:
            bloco_id = str(uuid.uuid4())
            conn.execute(
                sa.text(
                    """
                    INSERT INTO blocos (id, titulo, descricao, ordem, form_id)
                    VALUES (:id, :titulo, :descricao, :ordem, :form_id)
                    """
                ),
                {
                    "id": bloco_id,
                    "titulo": "Bloco 1 (Geral)",
                    "descricao": None,
                    "ordem": 1,
                    "form_id": str(form_id),
                },
            )

        conn.execute(
            sa.text(
                """
                UPDATE perguntas
                SET bloco_id = :bloco_id
                WHERE formulario_id = :form_id AND (bloco_id IS NULL)
                """
            ),
            {"bloco_id": bloco_id, "form_id": str(form_id)},
        )

    # Altera para não nulo se ainda não for
    cols = [c["name"] for c in insp.get_columns("perguntas")]
    if "bloco_id" in cols:
        with op.batch_alter_table("perguntas") as batch_op:
            batch_op.alter_column("bloco_id", nullable=False)


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # Remove FK e coluna bloco_id se existirem
    fks = {fk["name"] for fk in insp.get_foreign_keys("perguntas")}
    if "fk_perguntas_bloco_id" in fks:
        with op.batch_alter_table("perguntas") as batch_op:
            batch_op.drop_constraint("fk_perguntas_bloco_id", type_="foreignkey")

    cols = [c["name"] for c in insp.get_columns("perguntas")]
    if "bloco_id" in cols:
        with op.batch_alter_table("perguntas") as batch_op:
            batch_op.drop_column("bloco_id")

    # Remove tabela blocos se existir
    if insp.has_table("blocos"):
        op.drop_table("blocos")