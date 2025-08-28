#!/usr/bin/env sh
set -e
cd /app
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  alembic -c alembic.ini upgrade head
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
