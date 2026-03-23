# Run static Digibib5 research snapshot (JSON)
param(
    [string] $ExePath = "",
    [string] $Output = ""
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root
$argsList = @("run", "python", "scripts/analyze_digibib.py")
if ($ExePath -ne "") {
    $argsList += "--exe"
    $argsList += $ExePath
}
if ($Output -ne "") {
    $argsList += "--output"
    $argsList += $Output
}
& uv @argsList
exit $LASTEXITCODE
