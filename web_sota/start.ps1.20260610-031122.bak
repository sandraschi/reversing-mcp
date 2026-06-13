param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly
$WindowStyle = $FleetStart.WindowStyle

# Webapp Start - Standardized SOTA (Backend 10750, Frontend 10751)
$BackendPort = 10750
$FrontendPort = 10751

Stop-FleetPortSquatters -Ports @($BackendPort, $FrontendPort) -Label "reversing-mcp"

if (-not (Assert-FleetPortsAvailable -Ports @($BackendPort, $FrontendPort) -Label "reversing-mcp")) { exit 1 }

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start FastAPI backend (REST + /tools/status, /ghidra/status) on 10750
Write-Host "Starting FastAPI backend on port $BackendPort ..." -ForegroundColor Cyan
$apiDir = Join-Path $ProjectRoot "reversing-webapp\api"
$backendCmd = "`$env:PYTHONPATH = '$ProjectRoot\src'; Set-Location '$apiDir'; uv run python -m uvicorn main:app --host 127.0.0.1 --port $BackendPort --log-level info"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 4. Run Vite frontend on 10751 (getApiBase() = 10750)
# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$FrontendPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
if ($SkipFrontend) { return }
npm run dev -- --port $FrontendPort --host




