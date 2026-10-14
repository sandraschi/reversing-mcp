Param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

# Fleet unified launcher - do not edit logic here.
# Change fleet-start.config.ps1 at the repo root instead.
# Delegates to web_sota\start.ps1 (fleet engine: Invoke-FleetWebappStart.ps1).
$webStart = Join-Path $PSScriptRoot "web_sota\start.ps1"
if (-not (Test-Path $webStart)) {
    Write-Host "ERROR: web_sota\start.ps1 not found." -ForegroundColor Red
    exit 1
}
& $webStart `
    -Headless:$Headless `
    -BackendOnly:$BackendOnly `
    -FrontendOnly:$FrontendOnly `
    -NoBrowser:$NoBrowser
