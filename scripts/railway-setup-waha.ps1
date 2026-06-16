# Configura WAHA no Railway e liga API/Worker ao provedor waha.
# Requer: railway login
#
# Uso:
#   .\scripts\railway-setup-waha.ps1
#   .\scripts\railway-setup-waha.ps1 -WahaUrl "https://waha-xxx.up.railway.app"
#   .\scripts\railway-setup-waha.ps1 -Redeploy

param(
    [string]$WahaUrl = "",
    [switch]$Redeploy
)

$ErrorActionPreference = "Stop"

$PROJECT_ID = "1e1789f9-6de2-4084-af42-c1db755f1192"
$ENVIRONMENT_ID = "ad708e57-c381-4c78-bed8-3e667c5c8df0"
$SERVICE_API = "8129c558-9429-4e5c-b123-b80d68923a9d"
$MOUNT_PATH = "/app/.sessions"
$VOLUME_NAME = "waha-sessions-volume"
$SERVICE_WAHA = "waha"

function Invoke-Railway {
    param([string[]]$Args)
    & railway @Args
    if ($LASTEXITCODE -ne 0) { throw "railway falhou: $Args" }
}

function New-Secret {
    param([int]$Bytes = 32)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $buf = New-Object byte[] $Bytes
    $rng.GetBytes($buf)
    return ([BitConverter]::ToString($buf) -replace "-", "").ToLower()
}

Write-Host "==> Verificando autenticação..."
Invoke-Railway @("whoami")

$apiKey = New-Secret
$dashPass = New-Secret 16
$swaggerPass = New-Secret 16

Write-Host ""
Write-Host "==> Crie o serviço WAHA no Railway (se ainda não existir):"
Write-Host "    1. New Service -> GitHub Repo -> gerenciamento-coroinhas"
Write-Host "    2. Root Directory: /waha"
Write-Host "    3. Nome do serviço: waha"
Write-Host "    4. Generate Domain e anote a URL"
Write-Host ""
Write-Host "    Ou via CLI (imagem Docker, sem volume automático):"
Write-Host "    railway add --service waha --image devlikeapro/waha"
Write-Host ""

if (-not $WahaUrl) {
    $WahaUrl = Read-Host "URL pública do WAHA (ex: https://waha-xxx.up.railway.app)"
}
if (-not $WahaUrl.StartsWith("http")) { $WahaUrl = "https://$WahaUrl" }
$WahaUrl = $WahaUrl.TrimEnd("/")

Write-Host "==> Linkando serviço WAHA..."
try {
    Invoke-Railway @("service", "link", $SERVICE_WAHA)
} catch {
    Write-Host "AVISO: serviço '$SERVICE_WAHA' não encontrado. Configure manualmente no dashboard."
    Write-Host "Continuando com variáveis na API/Worker..."
}

Write-Host "==> Volume de sessões WAHA ($MOUNT_PATH)..."
try {
    Invoke-Railway @("link", "-p", $PROJECT_ID, "-e", $ENVIRONMENT_ID, "-s", $SERVICE_WAHA)
    $volumes = Invoke-Railway @("volume", "list") 2>&1 | Out-String
    if ($volumes -notmatch [regex]::Escape($MOUNT_PATH)) {
        Write-Host "Criando volume..."
        Invoke-Railway @("volume", "add", "--mount-path", $MOUNT_PATH)
    } else {
        Write-Host "Volume em $MOUNT_PATH já existe."
    }

    $wahaVars = @{
        "WAHA_API_KEY" = $apiKey
        "WAHA_BASE_URL" = $WahaUrl
        "WAHA_DASHBOARD_USERNAME" = "coordenador"
        "WAHA_DASHBOARD_PASSWORD" = $dashPass
        "WHATSAPP_SWAGGER_USERNAME" = "admin"
        "WHATSAPP_SWAGGER_PASSWORD" = $swaggerPass
        "WAHA_API_KEY_EXCLUDE_PATH" = "ping"
        "WHATSAPP_RESTART_ALL_SESSIONS" = "True"
        "WAHA_AUTO_START_DELAY_SECONDS" = "5"
    }
    foreach ($kv in $wahaVars.GetEnumerator()) {
        Invoke-Railway @("variables", "--set", "$($kv.Key)=$($kv.Value)")
    }
} catch {
    Write-Host "AVISO: não foi possível configurar o serviço WAHA via CLI. Use waha/.env.railway.example"
}

Write-Host "==> Configurando API e Worker (WHATSAPP_PROVIDER=waha)..."
$whatsappVars = @{
    "WHATSAPP_PROVIDER" = "waha"
    "WHATSAPP_API_URL" = $WahaUrl
    "WHATSAPP_API_TOKEN" = $apiKey
    "WHATSAPP_WAHA_SESSION" = "default"
    "WHATSAPP_DEFAULT_COUNTRY_CODE" = "55"
    "NOTIFICACAO_ESCALA_CANAL" = "WhatsApp"
}

foreach ($serviceId in @($SERVICE_API)) {
    Invoke-Railway @("service", "link", $serviceId)
    foreach ($kv in $whatsappVars.GetEnumerator()) {
        Invoke-Railway @("variables", "--set", "$($kv.Key)=$($kv.Value)")
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "WAHA configurado"
Write-Host "========================================"
Write-Host "URL WAHA:     $WahaUrl"
Write-Host "API Key:      $apiKey"
Write-Host "Dashboard:    $WahaUrl/dashboard"
Write-Host "  usuário:    coordenador"
Write-Host "  senha:      $dashPass"
Write-Host "Swagger:      $WahaUrl/"
Write-Host "  usuário:    admin"
Write-Host "  senha:      $swaggerPass"
Write-Host ""
Write-Host "Próximos passos:"
Write-Host "  1. Abra $WahaUrl/dashboard"
Write-Host "  2. Inicie a sessão 'default' e escaneie o QR Code com WhatsApp da paróquia"
Write-Host "  3. Copie WHATSAPP_API_TOKEN para o Worker (mesmas vars da API)"
Write-Host "  4. Teste em Dashboard -> Comunicação (banner deve mostrar waha configurado)"
Write-Host ""
Write-Host "GUARDE a API Key — ela foi aplicada na API; anote se precisar no Worker manualmente."

if ($Redeploy) {
    Write-Host "==> Redeploy WAHA..."
    try {
        Invoke-Railway @("link", "-p", $PROJECT_ID, "-e", $ENVIRONMENT_ID, "-s", $SERVICE_WAHA)
        Invoke-Railway @("up", "--detach")
    } catch {
        Write-Host "Redeploy WAHA manual no dashboard."
    }
}

Write-Host "Concluído."
