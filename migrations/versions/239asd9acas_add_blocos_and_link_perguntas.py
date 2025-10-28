"""add blocos and link perguntas to blocos"""

from alembic import op
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision: str = "239asd9acas"
down_revision: Union[str, Sequence[str], None]= "2660a287711a"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "blocos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("formularios.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("form_id", "ordem", name="uq_blocos_form_ordem"),
    )

    with op.batch_alter_table("perguntas") as batch_op:
        batch_op.add_column(sa.Column("bloco_id", postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key(
            "fk_perguntas_bloco_id",
            "blocos",
            ["bloco_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    conn = op.get_bind()

    forms = list(conn.execute(sa.text("SELECT id FROM formularios")))
    for (form_id,) in forms:
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
                WHERE form_id = :form_id AND (bloco_id IS NULL)
                """
            ),
            {"bloco_id": bloco_id, "form_id": str(form_id)},
        )

    with op.batch_alter_table("perguntas") as batch_op:
        batch_op.alter_column("bloco_id", nullable=False)


def downgrade():
    with op.batch_alter_table("perguntas") as batch_op:
        batch_op.drop_constraint("fk_perguntas_bloco_id", type_="foreignkey")
        batch_op.drop_column("bloco_id")

    op.drop_table("blocos")