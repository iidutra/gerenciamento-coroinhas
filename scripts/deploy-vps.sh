#!/usr/bin/env bash
# Deploy no VPS — build local ou pull do GitLab Registry
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BUILD_LOCAL=false
PULL_REGISTRY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build) BUILD_LOCAL=true; shift ;;
    --pull) PULL_REGISTRY=true; shift ;;
    *) echo "Uso: $0 [--build | --pull]"; exit 1 ;;
  esac
done

if [[ ! -f .env ]]; then
  echo "Arquivo .env não encontrado. Copie .env.prod.example para .env e configure."
  exit 1
fi

# shellcheck disable=SC1091
set -a && source .env && set +a

if [[ "$PULL_REGISTRY" == true ]]; then
  if [[ -z "${CI_REGISTRY_IMAGE:-}" && -z "${API_IMAGE:-}" ]]; then
    echo "Defina CI_REGISTRY_IMAGE ou API_IMAGE/FRONTEND_IMAGE no .env"
    exit 1
  fi
  export API_IMAGE="${API_IMAGE:-${CI_REGISTRY_IMAGE}/api:latest}"
  export FRONTEND_IMAGE="${FRONTEND_IMAGE:-${CI_REGISTRY_IMAGE}/frontend:latest}"
  echo "Pull: $API_IMAGE"
  echo "Pull: $FRONTEND_IMAGE"
  docker compose -f "$COMPOSE_FILE" pull api frontend worker
  docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
elif [[ "$BUILD_LOCAL" == true ]]; then
  echo "Build local (NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL)"
  docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans
else
  echo "Modo padrão: up (usa imagens existentes ou build se necessário)"
  docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
fi

echo ""
echo "Aguardando health..."
sleep 5
curl -sf "http://127.0.0.1:${HTTP_PORT:-80}/api/v1/health" && echo "" || echo "Health check falhou — veja: docker compose -f $COMPOSE_FILE logs api"

echo "Deploy concluído."
