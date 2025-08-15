import os
import sys
from pathlib import Path
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

from app.database import Base, DATABASE_URL  # noqa
from app import models  # noqa

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Configura e executa migrações no modo offline."""
    url = os.getenv("DATABASE_URL", DATABASE_URL)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Configura e executa migrações no modo online."""
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = os.getenv("DATABASE_URL", DATABASE_URL)
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
