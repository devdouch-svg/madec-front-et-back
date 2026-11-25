#!/bin/sh
set -e

cd /app

echo "==> Waiting for SQL Server..."
python scripts/wait_for_db.py

echo "==> Running Alembic migrations..."
alembic upgrade head

if [ "$RESET_MADEC_CATALOG" = "true" ]; then
  echo "==> Resetting MADEC catalog (products + référentiels)..."
  python -m scripts.reset_madec_catalog
fi

echo "==> Starting API..."
exec "$@"
