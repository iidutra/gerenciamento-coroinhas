# Deploy manual no Railway (monorepo) — use se o GitHub deploy falhar.
# Requer: railway login
#
# Uso: .\scripts\railway-deploy.ps1

$ErrorActionPreference = "Stop"

$PROJECT_ID = "1e1789f9-6de2-4084-af42-c1db755f1192"
$ENVIRONMENT = "production"

function Invoke-RailwayCli {
    param([string[]]$RailwayArgs)
    & railway @RailwayArgs
    if ($LASTEXITCODE -ne 0) { throw "railway falhou: $RailwayArgs" }
}

Write-Host "==> Deploy API..."
Invoke-RailwayCli @(
    "up", "backend", "--path-as-root",
    "--service", "gerenciamento-coroinhas",
    "-e", $ENVIRONMENT,
    "-d"
)

Write-Host "==> Deploy Worker..."
Invoke-RailwayCli @(
    "up", "backend", "--path-as-root",
    "--service", "coroinhas-worker",
    "-e", $ENVIRONMENT,
    "-d"
)

Write-Host "==> Deploy Frontend..."
Invoke-RailwayCli @(
    "up", "frontend", "--path-as-root",
    "--service", "coroinhas-frontend",
    "-e", $ENVIRONMENT,
    "-d"
)

Write-Host "Deploys iniciados. Acompanhe no dashboard Railway."
