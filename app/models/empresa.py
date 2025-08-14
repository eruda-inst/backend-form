import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from app.models.user import Base

class Empresa(Base):
    __tablename__ = "empresas"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    cnpj: Mapped[str] = mapped_column(String(18), nullable=False, unique=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
