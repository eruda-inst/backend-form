#!/usr/bin/env sh
set -e

if [ "${WAIT_FOR_DB:-1}" = "1" ]; then
  until python - <<'PY'
import os, sys
from sqlalchemy import create_engine
u = (os.getenv("DB_URL") or os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI"))
u = u.replace("+asyncpg","+psycopg2").replace("postgres://","postgresql://")
try:
    create_engine(u, future=True).connect().close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
PY
  do sleep 1; done
fi

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python -m app.db.db_bootstrap
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000