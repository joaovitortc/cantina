#!/usr/bin/env bash
set -euo pipefail

cd /app

if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "Waiting for Postgres to be ready..."
  for i in {1..30}; do
    if python - <<'PY'
import os
from urllib.parse import urlparse

import psycopg

parsed = urlparse(os.environ["DATABASE_URL"])
conn = psycopg.connect(
    host=parsed.hostname,
    port=parsed.port or 5432,
    dbname=parsed.path.lstrip("/"),
    user=parsed.username,
    password=parsed.password,
    connect_timeout=3,
)
conn.close()
print("ready")
PY
    then
      break
    fi

    echo "Postgres not ready yet... (${i}/30)"
    sleep 2

    if [[ "$i" -eq 30 ]]; then
      echo "Postgres did not become ready in time"
      exit 1
    fi
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn cantina.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60
