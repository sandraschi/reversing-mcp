# Start Reversing MCP WebApp (SOTA ports 10750 backend, 10751 frontend)
# Use %~dp0 from start.bat so script dir = reversing-webapp when launched via symlink

$Root = $PSScriptRoot
if (-not $Root) { $Root = Split-Path -Parent $MyInvocation.MyCommand.Path }

$PythonCmd = Get-Command python, py -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $PythonCmd) {
    Write-Host "Python not found. Install Python 3.8+ first." -ForegroundColor Red
    exit 1
}
$Python = $PythonCmd.Definition
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js not found. Install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

# Backend (10750)
Write-Host "Starting FastAPI backend on http://localhost:10750" -ForegroundColor Green
$apiDir = Join-Path $Root "api"
if (-not (Test-Path (Join-Path $apiDir "venv"))) {
    Push-Location $apiDir
    & $Python -m venv venv
    Pop-Location
}
Start-Job -ScriptBlock {
    param($path, $pythonPath)
    $env:REVERSING_API_PORT = "10750"
    Set-Location $path
    & ".\venv\Scripts\Activate.ps1"
    & $pythonPath main.py
} -ArgumentList $apiDir, $Python -Name "ReversingAPI"

# Frontend (10751)
Write-Host "Starting Next.js frontend on http://localhost:10751" -ForegroundColor Green
if (-not (Test-Path (Join-Path $Root "node_modules"))) {
    Push-Location $Root
    npm install
    Pop-Location
}
Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    npm run dev
} -ArgumentList $Root -Name "ReversingFrontend"

Start-Sleep -Seconds 3
Write-Host "Frontend: http://localhost:10751  Backend: http://localhost:10750/docs" -ForegroundColor Cyan
Write-Host "To stop: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor Yellow
