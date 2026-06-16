# Configura serviços Railway — rode após `railway login` ou com RAILWAY_TOKEN
# Uso (PowerShell):
#   $env:RAILWAY_TOKEN = "seu-project-token"
#   .\scripts\railway-setup.ps1
#
# Ou interativo:
#   railway login
#   .\scripts\railway-setup.ps1

$ErrorActionPreference = "Stop"

$PROJECT_ID = "1e1789f9-6de2-4084-af42-c1db755f1192"
$ENVIRONMENT_ID = "ad708e57-c381-4c78-bed8-3e667c5c8df0"
# Serviço informado (ajuste se for worker/frontend)
$SERVICE_API = "eca2fba8-be62-4236-9101-d841e8f20653"

function Invoke-Railway {
    param([string[]]$Args)
    & railway @Args
    if ($LASTEXITCODE -ne 0) { throw "railway falhou: $Args" }
}

Write-Host "==> Verificando autenticação..."
Invoke-Railway @("whoami")

Write-Host "==> Listando serviços do projeto..."
Invoke-Railway @(
    "status",
    "--project", $PROJECT_ID,
    "--environment", $ENVIRONMENT_ID
)

Write-Host ""
Write-Host "Informe as URLs públicas geradas no Railway (Settings -> Networking -> Generate Domain):"
$apiUrl = Read-Host "URL da API (ex: https://xxx.up.railway.app)"
$frontUrl = Read-Host "URL do Frontend (ex: https://yyy.up.railway.app)"

if (-not $apiUrl.StartsWith("http")) { $apiUrl = "https://$apiUrl" }
if (-not $frontUrl.StartsWith("http")) { $frontUrl = "https://$frontUrl" }

$apiHost = ([Uri]$apiUrl).Host
$apiPublic = "$($apiUrl.TrimEnd('/'))/api/v1"
$secretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 50 | ForEach-Object { [char]$_ })

Write-Host "==> Configurando API ($SERVICE_API)..."
$apiVars = @{
    "SECRET_KEY" = $secretKey
    "DEBUG" = "False"
    "USE_SQLITE" = "False"
    "USE_REDIS" = "True"
    "GUNICORN_WORKERS" = "1"
    "CELERY_CONCURRENCY" = "1"
    "SERVE_MEDIA" = "True"
    "NOTIFICACAO_ESCALA_AUTOMATICA" = "True"
    "NOTIFICACAO_ESCALA_CANAL" = "WhatsApp"
    "ALLOWED_HOSTS" = $apiHost
    "CORS_ALLOWED_ORIGINS" = $frontUrl
    "CSRF_TRUSTED_ORIGINS" = $frontUrl
}

foreach ($kv in $apiVars.GetEnumerator()) {
    Invoke-Railway @(
        "variables", "set",
        "$($kv.Key)=$($kv.Value)",
        "--project", $PROJECT_ID,
        "--environment", $ENVIRONMENT_ID,
        "--service", $SERVICE_API
    )
}

Write-Host "==> Referencie no dashboard da API (se ainda não linkou):"
Write-Host "    DATABASE_URL = \`${{Postgres.DATABASE_URL}}"
Write-Host "    REDIS_URL    = \`${{Redis.REDIS_URL}}"

Write-Host ""
Write-Host "==> Frontend: defina NEXT_PUBLIC_API_URL=$apiPublic"
Write-Host "    (redeploy obrigatório após alterar)"
Write-Host ""
Write-Host "==> Worker: crie serviço com root backend/ e config railway.worker.toml"
Write-Host "    Copie SECRET_KEY, DATABASE_URL e REDIS_URL da API"
Write-Host ""
Write-Host "==> Criar coordenador (após deploy OK):"
Write-Host "    railway ssh --project=$PROJECT_ID --environment=$ENVIRONMENT_ID --service=$SERVICE_API"
Write-Host "    python manage.py criar_coordenador --email coord@paroquia.org --senha 'SuaSenha'"
Write-Host ""
Write-Host "Concluído. SECRET_KEY gerada e aplicada na API."
