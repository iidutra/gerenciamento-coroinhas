#!/usr/bin/env bash
# Rode no VPS após deploy (pull das imagens novas):
#   cd /opt/coroinhas && ./scripts/pos-deploy-dia13-agosto-2026.sh
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ANO=2026
MES=8

echo ">> Migrando..."
docker compose -f "$COMPOSE_FILE" exec -T api python manage.py migrate --noinput

echo ">> Importando escala do dia 13/$MES/$ANO..."
docker compose -f "$COMPOSE_FILE" exec -T api \
  python manage.py importar_dia13_escala "$ANO" "$MES" --substituir

echo ">> Concluído. Exporte o PDF em Dashboard → Escalas → Agosto 2026."
