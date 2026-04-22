param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$node = Join-Path $root "node-v24.14.1-win-x64\node.exe"
$npm = Join-Path $root "node-v24.14.1-win-x64\npm.cmd"
$python = Join-Path $root "venv\Scripts\python.exe"
$frontendDir = Join-Path $root "frontend"
$distDir = Join-Path $frontendDir "dist"
$nodeModulesDir = Join-Path $frontendDir "node_modules"
$viteCli = Join-Path $frontendDir "node_modules\vite\bin\vite.js"
$iaDir = Join-Path $root "IA"

if (-not (Test-Path $node)) {
    throw "Node local nao encontrado em $node"
}

if (-not (Test-Path $python)) {
    throw "Python do venv nao encontrado em $python"
}

if (-not (Test-Path $nodeModulesDir)) {
    Write-Host "Dependencias do frontend ainda nao foram instaladas." -ForegroundColor Yellow
    Write-Host "Rode primeiro:" -ForegroundColor Yellow
    Write-Host "  cd `"$frontendDir`"" -ForegroundColor Yellow
    Write-Host "  `"$npm`" install" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $viteCli)) {
    throw "CLI do Vite nao encontrado em $viteCli"
}

if ($SkipBuild) {
    Write-Host "[1/2] Build do frontend ignorado por parametro; reutilizando dist atual." -ForegroundColor Yellow
}
else {
    Write-Host "[1/2] Gerando build do frontend..." -ForegroundColor Cyan
    Push-Location $frontendDir
    try {
        & $node $viteCli build
    }
    finally {
        Pop-Location
    }
}

$hostAddress = if ($env:FASTAPI_HOST) { $env:FASTAPI_HOST } else { "127.0.0.1" }
$port = if ($env:FASTAPI_PORT) { $env:FASTAPI_PORT } else { "8000" }

Write-Host "[2/2] Iniciando API e servindo o frontend..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Abra: http://127.0.0.1:$port" -ForegroundColor Green
Write-Host "Para parar, use Ctrl+C." -ForegroundColor Green
Write-Host ""

Push-Location $iaDir
try {
    & $python -m uvicorn main:app --host $hostAddress --port $port
}
finally {
    Pop-Location
}
