#!/bin/sh
# Re-seed CTGS categories + Figma sous-categories + products on VPS.
# Run ON the server as root (API container must be Up, not Restarting).
#
# Prereq: data in /tmp/seed-data/
#   /tmp/seed-data/ctgs/*.png
#   /tmp/seed-data/my-madic-catalog.csv
#   /tmp/seed-data/product-images/
#
# Usage:
#   chmod +x scripts/seed-ctgs-vps.sh
#   ./scripts/seed-ctgs-vps.sh

set -e
cd /root/my-madec/backend

DATA=/tmp/seed-data
CTN=backend-api-1

if ! docker ps --format '{{.Names}}' | grep -qx "$CTN"; then
  echo "ERROR: $CTN not running. Fix API first (migration + docker compose up)."
  exit 1
fi

status=$(docker inspect -f '{{.State.Status}}' "$CTN" 2>/dev/null || echo missing)
if [ "$status" != "running" ]; then
  echo "ERROR: $CTN status=$status (need running, not restarting)"
  exit 1
fi

for d in "$DATA/ctgs" "$DATA/my-madic-catalog.csv" "$DATA/product-images"; do
  if [ ! -e "$d" ]; then
    echo "ERROR: missing $d — upload seed data to $DATA first"
    exit 1
  fi
done

echo "==> Copy seed data into container..."
docker exec "$CTN" rm -rf /tmp/seed-data
docker cp "$DATA" "$CTN:/tmp/seed-data"

echo "==> 1/3 CTGS categories..."
docker exec "$CTN" python -m scripts.seed_ctgs_categories --ctgs-dir /tmp/seed-data/ctgs

echo "==> 2/3 Figma sous-categories..."
docker exec "$CTN" python -m scripts.seed_figma_sous_categories

echo "==> 3/3 Figma products..."
docker exec "$CTN" python -m scripts.seed_figma_products \
  --catalog-csv /tmp/seed-data/my-madic-catalog.csv \
  --images-dir /tmp/seed-data/product-images

echo "==> Done. Check counts:"
docker exec "$CTN" python -c "
from app.db.session import SessionLocal
from app.models.catalog import CatalogCategorie, CatalogSousCategorie
from app.models.product import Product
db = SessionLocal()
print('categories', db.query(CatalogCategorie).count())
print('sous_categories', db.query(CatalogSousCategorie).count())
print('products', db.query(Product).count())
db.close()
"
