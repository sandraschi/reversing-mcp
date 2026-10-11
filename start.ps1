Param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser)
$SkipFrontend = $Headless -or $BackendOnly

if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}

$ScriptRoot = Split-Path -Parent $PSCommandPath
$BackendPort = 10750
$FrontendPort = 10751
$UvExe = "C:\Users\sandr\.local\bin\uv.exe"
$NpmCmd = "C:\Program Files\nodejs\npm.cmd"

Write-Host 'Starting reversing-mcp...' -ForegroundColor Cyan
Set-Location $ScriptRoot

# Port zombie clearing
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Start backend (single FastAPI app: REST + /mcp mount, on the backend port)
$BackendJob = Start-Job -Name "backend" -ScriptBlock {
    param($Root, $Port, $Uv)
    Set-Location $Root
    $env:PYTHONPATH = "$Root\src"
    & $Uv run uvicorn reversing_mcp.server:app --host 127.0.0.1 --port $Port
} -ArgumentList $ScriptRoot, $BackendPort, $UvExe

# Readiness poll (fail fast with job output instead of silent fallthrough)
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) { Write-Host "Backend ready on port $BackendPort" -ForegroundColor Green; $ready = $true; break }
    } catch {}
    if ($BackendJob.State -eq 'Failed') { break }
    Start-Sleep 1
}
if (-not $ready) {
    Write-Host "Backend did not answer /health in 60s. Job output:" -ForegroundColor Red
    Receive-Job -Job $BackendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $BackendJob -ErrorAction SilentlyContinue
    exit 1
}

if ($SkipFrontend) { return }

# Start frontend (Vite dev server, own window)
Start-Process cmd.exe -ArgumentList @('/k', "`"$NpmCmd`" run dev -- --port $FrontendPort --host 127.0.0.1") -WorkingDirectory (Join-Path $ScriptRoot 'web_sota')
if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$FrontendPort/" }
