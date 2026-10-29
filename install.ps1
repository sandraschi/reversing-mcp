#Requires -Version 5.1
<#
.SYNOPSIS
One-line installer for reversing-mcp across every AI client on this machine.

.DESCRIPTION
  irm https://raw.githubusercontent.com/sandraschi/reversing-mcp/main/install.ps1 | iex

Resolves the canonical fleet installer (install-fleet-mcp.ps1 in mcp-central-docs),
which backs up each client config, merges one entry, and is idempotent. Nothing is
replaced and no unrelated software is installed.

Local checkout wins over the network copy, so working from a clone is offline-safe.

.PARAMETER Check
Diagnose only - writes nothing.

.PARAMETER DryRun
Show what would change in each client.

.PARAMETER Uninstall
Remove only the entry this installer owns.

.EXAMPLE
.\install.ps1 -Check

.EXAMPLE
.\install.ps1 -Yes
#>
[CmdletBinding()]
param(
    [switch]$Check,
    [switch]$DryRun,
    [switch]$Uninstall,
    [switch]$List,
    [switch]$Json,
    [switch]$Yes
)
$ErrorActionPreference = 'Stop'

$repoName = 'reversing-mcp'
# mcp-central-docs is PRIVATE, so its raw URL 404s for anyone without a token.
# The public repo therefore vendors the canonical pair under scripts\ (same pattern
# install-mcp-clients.ps1 documents for NSIS installers; drift is checked by
# audit-mcpb-bundles.ps1). Network fallback points at THIS repo, which is public.
$canonicalUrl = 'https://raw.githubusercontent.com/sandraschi/reversing-mcp/master/scripts/install-fleet-mcp.ps1'

$pass = @{}
if ($Check) { $pass['Check'] = $true }
if ($DryRun) { $pass['DryRun'] = $true }
if ($Uninstall) { $pass['Uninstall'] = $true }
if ($List) { $pass['List'] = $true }
if ($Json) { $pass['Json'] = $true }
if ($Yes) { $pass['Yes'] = $true }

# Vendored copy first (works offline and for anyone), then a local fleet checkout.
$installer = $null
if ($PSScriptRoot) {
    foreach ($candidate in @(
            (Join-Path $PSScriptRoot 'scripts\install-fleet-mcp.ps1'),
            (Join-Path $PSScriptRoot '..\mcp-central-docs\scripts\install-fleet-mcp.ps1')
        )) {
        if (Test-Path -LiteralPath $candidate) { $installer = (Resolve-Path -LiteralPath $candidate).Path; break }
    }
}

if (-not $installer) {
    $installer = Join-Path $env:TEMP 'install-fleet-mcp.ps1'
    Write-Host "Fetching installer -> $installer"
    Invoke-WebRequest -Uri $canonicalUrl -OutFile $installer -UseBasicParsing
    # The fetcher needs the writer beside it; fetch that too on the network path.
    $writerPath = Join-Path (Split-Path $installer -Parent) 'install-mcp-clients.ps1'
    if (-not (Test-Path -LiteralPath $writerPath)) {
        Invoke-WebRequest -Uri ($canonicalUrl -replace 'install-fleet-mcp\.ps1$', 'install-mcp-clients.ps1') -OutFile $writerPath -UseBasicParsing
    }
}

& $installer -Repo $repoName @pass
