# Webapp Start - Standardized SOTA (Backend 10750, Frontend 10751)
$BackendPort = 10750
$FrontendPort = 10751
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 1. Kill any process squatting on the ports
Write-Host "Checking for port squatters on $BackendPort and $FrontendPort..." -ForegroundColor Yellow
$pids = Get-NetTCPConnection -LocalPort $BackendPort, $FrontendPort -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 4 } | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($p in $pids) {
    Write-Host "Found squatter (PID: $p). Terminating..." -ForegroundColor Red
    try { Stop-Process -Id $p -Force -ErrorAction Stop } catch { Write-Host "Warning: Could not terminate PID $p." -ForegroundColor Gray }
}

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start FastAPI backend (REST + /tools/status, /ghidra/status) on 10750
Write-Host "Starting FastAPI backend on port $BackendPort ..." -ForegroundColor Cyan
$apiDir = Join-Path $ProjectRoot "reversing-webapp\api"
$backendCmd = "`$env:PYTHONPATH = '$ProjectRoot\src'; Set-Location '$apiDir'; uv run python -m uvicorn main:app --host 127.0.0.1 --port $BackendPort --log-level info"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 4. Run Vite frontend on 10751 (getApiBase() = 10750)
Write-Host "Starting Vite frontend on port $FrontendPort ..." -ForegroundColor Green
npm run dev -- --port $FrontendPort --host

