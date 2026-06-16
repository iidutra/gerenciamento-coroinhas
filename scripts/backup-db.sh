#!/usr/bin/env bash
# Backup PostgreSQL — agende no cron: 0 3 * * * /opt/coroinhas/scripts/backup-db.sh
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/coroinhas_${STAMP}.sql.gz"

docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "${DB_USER:-postgres}" "${DB_NAME:-coroinhas}" | gzip > "$FILE"

echo "Backup: $FILE ($(du -h "$FILE" | cut -f1))"

find "$BACKUP_DIR" -name 'coroinhas_*.sql.gz' -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
