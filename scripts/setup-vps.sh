#!/usr/bin/env bash
# Configuração inicial do VPS (Ubuntu 22.04/24.04) — rode como root ou com sudo
# Uso: curl -fsSL ... | bash   OU   sudo ./scripts/setup-vps.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/coroinhas}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"

echo "==> Atualizando pacotes..."
apt-get update -qq
apt-get upgrade -y -qq

echo "==> Instalando dependências..."
apt-get install -y -qq ca-certificates curl git ufw

echo "==> Instalando Docker..."
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

echo "==> Habilitando Docker no boot..."
systemctl enable docker
systemctl start docker

if ! id "$DEPLOY_USER" &>/dev/null; then
  echo "==> Criando usuário $DEPLOY_USER..."
  useradd -m -s /bin/bash "$DEPLOY_USER"
  usermod -aG docker "$DEPLOY_USER"
fi

echo "==> Firewall (UFW): SSH + HTTP + HTTPS..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

mkdir -p "$APP_DIR"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$APP_DIR"

echo ""
echo "Setup concluído."
echo "  App dir: $APP_DIR"
echo "  Usuário deploy: $DEPLOY_USER (membro do grupo docker)"
echo ""
echo "Próximos passos (como $DEPLOY_USER):"
echo "  git clone <seu-repo> $APP_DIR"
echo "  cd $APP_DIR && cp .env.prod.example .env && nano .env"
echo "  ./scripts/deploy-vps.sh --build"
