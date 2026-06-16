# Configura Root Directory / Config-as-Code no Railway (monorepo GitHub).
# Requer: railway login (token em ~/.railway/config.json)
#
# Uso: .\scripts\railway-set-monorepo.ps1

$ErrorActionPreference = "Stop"

$PROJECT_ID = "1e1789f9-6de2-4084-af42-c1db755f1192"
$ENVIRONMENT_ID = "ad708e57-c381-4c78-bed8-3e667c5c8df0"

$SERVICES = @(
    @{ Id = "8129c558-9429-4e5c-b123-b80d68923a9d"; Name = "gerenciamento-coroinhas"; Root = "/backend" },
    @{ Id = "6bff179f-510e-457d-a4b7-0489e6e1ec19"; Name = "coroinhas-worker"; Root = "/backend" },
    @{ Id = "cee4af84-908a-48ce-a522-c1c5e3c60a98"; Name = "coroinhas-frontend"; Root = "/frontend" }
)

$configPath = Join-Path $env:USERPROFILE ".railway\config.json"
if (-not (Test-Path $configPath)) { throw "Execute 'railway login' antes." }
$token = (Get-Content $configPath -Raw | ConvertFrom-Json).user.token

function Invoke-RailwayGraphQL($Query) {
    $body = @{ query = $Query } | ConvertTo-Json -Compress
    $headers = @{
        Authorization = "Bearer $token"
        "Content-Type" = "application/json"
        "User-Agent" = "Mozilla/5.0"
    }
    $resp = Invoke-RestMethod -Uri "https://backboard.railway.com/graphql/v2" -Method Post -Headers $headers -Body $body
    if ($resp.errors) { throw ($resp.errors | ConvertTo-Json -Depth 5) }
    return $resp
}

Write-Host "==> Configurando monorepo (Root Directory por servico)..."
foreach ($svc in $SERVICES) {
    $q = "mutation { serviceInstanceUpdate(serviceId: `"$($svc.Id)`", environmentId: `"$ENVIRONMENT_ID`", input: { rootDirectory: `"$($svc.Root)`", railwayConfigFile: null }) }"
    Invoke-RailwayGraphQL $q | Out-Null
    Write-Host "  OK $($svc.Name) -> $($svc.Root)"
}

Write-Host ""
Write-Host "Concluido. Faca redeploy ou push no GitHub para aplicar."
