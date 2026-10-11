#Requires -Version 5.1
# Shim: the canonical pack pipeline lives in mcp-central-docs (never vendored, so fixes apply fleet-wide).
# (Replaced a 272-line local fork 2026-10-11; fleet script is a superset incl. launch check. Backup: pack.ps1.<ts>.bak, gitignored.)
$central = Join-Path (Split-Path -Parent $PSScriptRoot | Split-Path -Parent) 'mcp-central-docs\scripts\fleet-mcpb-pack.ps1'
if (-not (Test-Path $central)) { throw "Canonical pack script missing: $central (clone mcp-central-docs next to this repo)" }
& $central -RepoRoot (Split-Path -Parent $PSScriptRoot)
exit $LASTEXITCODE
