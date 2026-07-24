param(
    [switch]$Force,
    [string]$InstallDir = "$env:LOCALAPPDATA\IDR"
)

$ErrorActionPreference = "Stop"
$IdrUrl = "https://github.com/crypto2011/IDR/releases/download/27_01_2019/Idr.exe"
$TargetExe = Join-Path $InstallDir "Idr.exe"

if ((Test-Path $TargetExe) -and -not $Force) {
    Write-Host "IDR already installed at $TargetExe" -ForegroundColor Green
    Write-Host "Run with -Force to re-download." -ForegroundColor Yellow
    exit 0
}

Write-Host "Downloading IDR (Interactive Delphi Reconstructor)..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

try {
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $IdrUrl -OutFile $TargetExe -UseBasicParsing
    Write-Host "Downloaded to $TargetExe ($((Get-Item $TargetExe).Length / 1KB) KB)" -ForegroundColor Green
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
    Write-Host "Manual: go to https://github.com/crypto2011/IDR/releases and download Idr.exe" -ForegroundColor Yellow
    exit 1
}

# Add to PATH for current session
$env:Path += ";$InstallDir"

# Offer to add to PATH persistently
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$InstallDir*") {
    $newPath = "$InstallDir;$userPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Added $InstallDir to user PATH (persistent)" -ForegroundColor Green
}

Write-Host "IDR ready — run 'Idr.exe' to launch" -ForegroundColor Green
Write-Host "Or use with Ghidra: export .map from IDR, import into Ghidra per docs/IDR.md" -ForegroundColor Cyan
