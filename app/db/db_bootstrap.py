import os, subprocess, sys
from sqlalchemy import create_engine, text

def _sync_url(u: str) -> str:
    return u.replace("+asyncpg", "+psycopg2").replace("postgres://", "postgresql://")

def _has_alembic_version(engine) -> bool:
    with engine.connect() as conn:
        return conn.execute(
            text("select 1 from information_schema.tables where table_name='alembic_version'")
        ).first() is not None

def main():
    db_url = os.getenv("DB_URL") or os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if not db_url:
        print("DB_URL/DATABASE_URL/SQLALCHEMY_DATABASE_URI não definido", file=sys.stderr)
        sys.exit(1)

    url = _sync_url(db_url)
    engine = create_engine(url, future=True)

    if not _has_alembic_version(engine):
        r = subprocess.run(["alembic", "stamp", "head"])
        if r.returncode != 0:
            sys.exit(r.returncode)

    r = subprocess.run(["alembic", "upgrade", "head"])
    if r.returncode != 0:
        sys.exit(r.returncode)

if __name__ == "__main__":
    main()