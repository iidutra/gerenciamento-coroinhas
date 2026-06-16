#!/usr/bin/env bash
# Configura variáveis Railway — requer RAILWAY_TOKEN ou `railway login`
# Uso:
#   export RAILWAY_TOKEN=xxx
#   ./scripts/railway-setup.sh --api-url https://api-xxx.up.railway.app --frontend-url https://front-xxx.up.railway.app

set -euo pipefail

PROJECT_ID="1e1789f9-6de2-4084-af42-c1db755f1192"
ENVIRONMENT_ID="ad708e57-c381-4c78-bed8-3e667c5c8df0"
SERVICE_API="${SERVICE_API:-eca2fba8-be62-4236-9101-d841e8f20653}"

API_URL=""
FRONTEND_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-url) API_URL="$2"; shift 2 ;;
    --frontend-url) FRONTEND_URL="$2"; shift 2 ;;
    --service-api) SERVICE_API="$2"; shift 2 ;;
    *) echo "Uso: $0 --api-url URL --frontend-url URL"; exit 1 ;;
  esac
done

railway whoami

echo "==> Serviços:"
railway status --project "$PROJECT_ID" --environment "$ENVIRONMENT_ID" || true

if [[ -z "$API_URL" || -z "$FRONTEND_URL" ]]; then
  echo "Informe --api-url e --frontend-url (domínios públicos do Railway)"
  exit 1
fi

API_HOST=$(echo "$API_URL" | sed -E 's|https?://||; s|/.*||')
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python -c "import secrets; print(secrets.token_hex(32))")

set_var() {
  railway variables set "$1=$2" \
    --project "$PROJECT_ID" \
    --environment "$ENVIRONMENT_ID" \
    --service "$SERVICE_API"
}

echo "==> API service $SERVICE_API"
set_var SECRET_KEY "$SECRET_KEY"
set_var DEBUG "False"
set_var USE_SQLITE "False"
set_var USE_REDIS "True"
set_var GUNICORN_WORKERS "1"
set_var CELERY_CONCURRENCY "1"
set_var SERVE_MEDIA "True"
set_var NOTIFICACAO_ESCALA_AUTOMATICA "True"
set_var NOTIFICACAO_ESCALA_CANAL "WhatsApp"
set_var ALLOWED_HOSTS "$API_HOST"
set_var CORS_ALLOWED_ORIGINS "$FRONTEND_URL"
set_var CSRF_TRUSTED_ORIGINS "$FRONTEND_URL"

echo ""
echo "Manual no dashboard (Reference Variables):"
echo "  DATABASE_URL = \${{Postgres.DATABASE_URL}}"
echo "  REDIS_URL    = \${{Redis.REDIS_URL}}"
echo ""
echo "Frontend service — variable de build:"
echo "  NEXT_PUBLIC_API_URL=${API_URL%/}/api/v1"
echo ""
echo "Worker — root backend/, config railway.worker.toml, mesmas vars + DATABASE_URL/REDIS_URL"
echo ""
echo "Coordenador:"
echo "  railway ssh --project=$PROJECT_ID --environment=$ENVIRONMENT_ID --service=$SERVICE_API"
echo "  python manage.py criar_coordenador --email coord@paroquia.org --senha 'SuaSenha'"
