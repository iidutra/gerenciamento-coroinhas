# Volume persistente para fotos no Railway (serviço API).
# Requer: railway login
#
# Uso:
#   .\scripts\railway-setup-media.ps1
#   .\scripts\railway-setup-media.ps1 -Redeploy

param(
    [switch]$Redeploy
)

$ErrorActionPreference = "Stop"

$PROJECT_ID = "1e1789f9-6de2-4084-af42-c1db755f1192"
$ENVIRONMENT_ID = "ad708e57-c381-4c78-bed8-3e667c5c8df0"
$SERVICE_API = "8129c558-9429-4e5c-b123-b80d68923a9d"
$MOUNT_PATH = "/app/media"
$VOLUME_NAME = "gerenciamento-coroinhas-volume"

function Invoke-Railway {
    param([string[]]$Args)
    & railway @Args
    if ($LASTEXITCODE -ne 0) { throw "railway falhou: $Args" }
}

Write-Host "==> Verificando autenticação..."
Invoke-Railway @("whoami")

Write-Host "==> Linkando serviço API..."
Invoke-Railway @(
    "link",
    "-p", $PROJECT_ID,
    "-e", $ENVIRONMENT_ID,
    "-s", $SERVICE_API
)

$volumes = Invoke-Railway @("volume", "list") 2>&1 | Out-String
if ($volumes -notmatch [regex]::Escape($MOUNT_PATH)) {
    Write-Host "==> Criando volume em $MOUNT_PATH ..."
    Invoke-Railway @("volume", "add", "--mount-path", $MOUNT_PATH)
} else {
    Write-Host "==> Volume em $MOUNT_PATH já existe."
    if ($volumes -match "$VOLUME_NAME[\s\S]*?Mount path: /tmp") {
        Write-Host "==> Corrigindo mount path..."
        Invoke-Railway @("volume", "update", "-v", $VOLUME_NAME, "-m", $MOUNT_PATH)
    }
}

Write-Host "==> Garantindo SERVE_MEDIA=True na API..."
Invoke-Railway @(
    "variables", "set", "SERVE_MEDIA=True",
    "--project", $PROJECT_ID,
    "--environment", $ENVIRONMENT_ID,
    "--service", $SERVICE_API
)

Write-Host ""
Write-Host "Volume configurado:"
Invoke-Railway @("volume", "list")

Write-Host ""
Write-Host "Fotos persistem em $MOUNT_PATH entre redeploys."
Write-Host "URLs públicas: https://<api>.up.railway.app/media/coroinhas/fotos/..."
Write-Host ""
Write-Host "Alternativa futura (R2/S3): defina USE_S3=True e credenciais (ver .env.railway.example)."

if ($Redeploy) {
    Write-Host "==> Redeploy da API..."
    Invoke-Railway @("up", "--detach")
}

Write-Host "Concluído."
