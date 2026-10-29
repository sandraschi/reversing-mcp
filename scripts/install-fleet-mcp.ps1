#Requires -Version 5.1
<#
.SYNOPSIS
Register (or remove) a fleet MCP server in every detected AI client, in one command.

.DESCRIPTION
Thin orchestrator over install-mcp-clients.ps1 - the CANONICAL config writer that
backs up each client config, MERGES one entry (never replaces the file), and is
idempotent. This script only resolves what to register; it does not write configs
itself.

Generic by design. Any fleet Python repo with a [project.scripts] entry works with
no per-repo edit. Resolution order for the stdio launch command:

  1. -Command (explicit override wins - installers use this)
  2. <repo>\.venv\Scripts\<project.scripts key>.exe   (preferred: real exe, no stdout pollution)
  3. <repo>\.venv\Scripts\python.exe -m <pkg>.server  (when src\<pkg>\server.py exists)
  4. <repo>\.venv\Scripts\python.exe run_server.py    (legacy PyInstaller entrypoint)

The client-server alias is taken from an existing registration that already points
at this repo path, so it never creates a duplicate under a second name (e.g. a repo
called git-github-mcp whose clients already know it as "gitops"). Falls back to the
repo stem with any trailing -mcp removed.

Stdio env defaults are the ones a working FastMCP registration needs: PYTHONUNBUFFERED
and the FastMCP banner/update-check suppressed so nothing writes to the stdio channel.

.PARAMETER Repo
Repo directory name (resolved under -ReposRoot) or an absolute path.

.PARAMETER ReposRoot
Fleet root searched when -Repo is a bare name. Default: D:\Dev\repos, then
the parent of this script's repository.

.PARAMETER Check
Diagnose only: report resolution, venv state, detected clients, existing alias.
Writes nothing, installs nothing.

.PARAMETER Yes
Allow unattended prerequisite install (uv via winget) and venv sync without prompting.

.EXAMPLE
.\install-fleet-mcp.ps1 -Repo reversing-mcp -Check

.EXAMPLE
.\install-fleet-mcp.ps1 -Repo reversing-mcp -Yes

.EXAMPLE
.\install-fleet-mcp.ps1 -Repo reversing-mcp -Uninstall
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Repo,
    [string]$ReposRoot,
    [string]$Name,
    [string]$Command,
    [string[]]$Arguments = @(),
    [string[]]$EnvPairs = @('MCP_TRANSPORT=stdio', 'PYTHONUNBUFFERED=1', 'FASTMCP_BANNER=0', 'FASTMCP_UPDATE_CHECK=0'),
    [string[]]$SyncExtras = @(),
    [ValidateSet('mcp', 'webapp', 'desktop', 'all')][string]$Mode = 'mcp',
    [switch]$NoStart,
    [switch]$OpenBrowser,
    [string]$AssetName,
    [switch]$SkipReleaseCheck,
    [ValidateSet('claude-desktop', 'cursor', 'antigravity', 'windsurf', 'opencode', 'claude-code')]
    [string[]]$Clients,
    [switch]$Check,
    [switch]$Uninstall,
    [switch]$List,
    [switch]$DryRun,
    [switch]$Json,
    [switch]$Yes
)
$ErrorActionPreference = 'Stop'

function Write-Step($msg) { if (-not $Json) { Write-Host $msg } }
function Write-Fail($msg) {
    if ($Json) { ConvertTo-Json -InputObject @(@{ status = 'error'; detail = $msg }) -Compress -Depth 4 }
    else { Write-Host "ERROR: $msg" -ForegroundColor Red }
    exit 1
}

# ---- locate the canonical writer -------------------------------------------------
$writer = Join-Path $PSScriptRoot 'install-mcp-clients.ps1'
if (-not (Test-Path -LiteralPath $writer)) {
    Write-Fail "canonical writer not found at $writer (install-mcp-clients.ps1 must sit next to this script)"
}

# ---- resolve the repo ------------------------------------------------------------
$repoStem = $null
if (Test-Path -LiteralPath $Repo -PathType Container) {
    $repoPath = (Resolve-Path -LiteralPath $Repo).Path
    $repoStem = Split-Path $repoPath -Leaf
} else {
    $roots = @()
    if ($ReposRoot) { $roots += $ReposRoot }
    else {
        $roots += 'D:\Dev\repos'
        $roots += (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
    }
    foreach ($root in $roots) {
        $candidate = Join-Path $root $Repo
        if (Test-Path -LiteralPath $candidate -PathType Container) { $repoPath = (Resolve-Path -LiteralPath $candidate).Path; break }
    }
    $repoStem = $Repo
}

if (-not $repoPath) {
    if ($Check -or $DryRun -or $List -or $Uninstall) {
        Write-Fail "repo '$Repo' not found under: $($roots -join '; ')"
    }
    $gitExe = 'C:\Program Files\Git\cmd\git.exe'
    if (-not (Test-Path -LiteralPath $gitExe)) { $gitExe = (Get-Command git -ErrorAction SilentlyContinue).Source }
    if (-not $gitExe) { Write-Fail "git not found, cannot clone '$Repo'" }
    $root = if ($ReposRoot) { $ReposRoot } else { 'D:\Dev\repos' }
    $repoPath = Join-Path $root $Repo
    Write-Step "cloning $Repo -> $repoPath"
    & $gitExe clone "https://github.com/sandraschi/$Repo.git" $repoPath
    if ($LASTEXITCODE -ne 0) { Write-Fail "git clone failed for $Repo" }
}

$repoPathPosix = $repoPath.Replace('\', '/')
$alias = ($repoStem -replace '-mcp$', '')

# ---- discover the stdio launch command -------------------------------------------
function Get-VenvPython([string]$Root) { Join-Path $Root '.venv\Scripts\python.exe' }

function Get-LaunchSpec([string]$Root, [string]$Stem) {
    $pyproject = Join-Path $Root 'pyproject.toml'
    $scriptKey = $null
    if (Test-Path -LiteralPath $pyproject) {
        $inScripts = $false
        foreach ($ln in (Get-Content -LiteralPath $pyproject)) {
            if ($ln -match '^\s*\[([^\]]+)\]\s*$') { $inScripts = ($Matches[1].Trim() -eq 'project.scripts'); continue }
            if ($inScripts -and $ln -match '^\s*([A-Za-z0-9_.\-]+)\s*=\s*"') { $scriptKey = $Matches[1]; break }
        }
    }

    if ($scriptKey) {
        $exe = Join-Path $Root ".venv\Scripts\$scriptKey.exe"
        return [pscustomobject]@{ Command = $exe; Arguments = @(); EnvPairs = @(); NeedsSync = (-not (Test-Path -LiteralPath $exe)); How = "project.scripts -> $scriptKey.exe" }
    }

    $python = Get-VenvPython $Root
    if (-not (Test-Path -LiteralPath $python)) {
        return [pscustomobject]@{ Command = $null; Arguments = @(); EnvPairs = @(); NeedsSync = $true; How = 'no venv' }
    }
    $pkg = ($Stem -replace '-', '_')
    if (Test-Path -LiteralPath (Join-Path $Root "src\$pkg\server.py")) {
        return [pscustomobject]@{ Command = $python; Arguments = @('-m', "$pkg.server"); EnvPairs = @("PYTHONPATH=$Root\src"); NeedsSync = $false; How = "-m $pkg.server" }
    }
    if (Test-Path -LiteralPath (Join-Path $Root 'run_server.py')) {
        return [pscustomobject]@{ Command = $python; Arguments = @((Join-Path $Root 'run_server.py')); EnvPairs = @(); NeedsSync = $false; How = 'run_server.py' }
    }
    return [pscustomobject]@{ Command = $null; Arguments = @(); EnvPairs = @(); NeedsSync = $false; How = 'unresolved' }
}

# Launch-command resolution happens below, after the resolver functions are defined.

function Convert-EnvPairsToMap([string[]]$Pairs) {
    $map = @{}
    foreach ($p in $Pairs) { if ($p -match '^([^=]+)=(.*)$') { $map[$Matches[1]] = $Matches[2] } }
    return $map
}

function Get-ManifestSpec([string]$Root) {
    # The declared install contract. 158 of 233 fleet -mcp repos already ship this;
    # nothing was consuming it, so every installer re-derived the launch command.
    $manifest = Join-Path $Root 'mcpb\manifest.json'
    if (-not (Test-Path -LiteralPath $manifest)) { return $null }
    try { $m = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json } catch { return $null }
    $cfg = $m.server.mcp_config
    if (-not $cfg -or -not $cfg.command) { return $null }

    $cmd = ([string]$cfg.command).Replace('${__dirname}', $Root)
    $argList = @()
    foreach ($a in @($cfg.args)) { if ($null -ne $a) { $argList += ([string]$a).Replace('${__dirname}', $Root) } }
    $envList = @()
    if ($cfg.env) {
        foreach ($p in $cfg.env.PSObject.Properties) { $envList += "$($p.Name)=$(([string]$p.Value).Replace('${__dirname}', $Root))" }
    }

    # A bare tool name is unreliable in a non-interactive session (NAKED_PC_INSTALL_STANDARD 2b).
    if ($cmd -match '^(uv|uv\.exe)$') {
        $resolved = (Get-Command uv -ErrorAction SilentlyContinue).Source
        if ($resolved) { $cmd = $resolved }
    }
    if ($cmd -match '^(python|python\.exe)$') {
        $venvPy = Join-Path $Root '.venv\Scripts\python.exe'
        if (Test-Path -LiteralPath $venvPy) { $cmd = $venvPy }
    }

    $needsSync = $false
    if ($cmd -match '[\\/]') { if (-not (Test-Path -LiteralPath $cmd)) { $needsSync = $true } }
    elseif (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { $needsSync = $true }

    return [pscustomobject]@{ Command = $cmd; Arguments = $argList; EnvPairs = $envList; NeedsSync = $needsSync; How = 'mcpb/manifest.json -> server.mcp_config' }
}

function Read-SharedText([string]$Path) {
    # Start-Process holds the redirect target open; a plain ReadAllText throws
    # "being used by another process" and every tier gets rejected for the wrong reason.
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    try { $fs = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite) }
    catch { return '' }
    try {
        $sr = New-Object System.IO.StreamReader($fs)
        return $sr.ReadToEnd()
    } finally {
        try { if ($sr) { $sr.Dispose() } } catch { }
        try { $fs.Dispose() } catch { }
    }
}

function Get-FleetSyncExtras([string]$Root) {
    # Parsed, never dot-sourced: an installer must not execute repo-provided PowerShell.
    $cfg = Join-Path $Root 'fleet-start.config.ps1'
    if (-not (Test-Path -LiteralPath $cfg)) { return @() }
    $hit = Select-String -LiteralPath $cfg -Pattern 'SyncExtras\s*=\s*@\(([^)]*)\)' | Select-Object -First 1
    if (-not $hit) { return @() }
    return @([regex]::Matches($hit.Matches[0].Groups[1].Value, "'([^']+)'") | ForEach-Object { $_.Groups[1].Value })
}

function Test-StdioHandshake {
    param([string]$Cmd, [string[]]$ArgList = @(), [hashtable]$EnvMap = @{}, [int]$TimeoutSec = 45)
    $tmpDir = Join-Path ([IO.Path]::GetTempPath()) ('mcp-probe-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
    $inF = Join-Path $tmpDir 'in.txt'; $outF = Join-Path $tmpDir 'out.txt'; $errF = Join-Path $tmpDir 'err.txt'
    $req = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"fleet-probe","version":"1"}}}'
    Set-Content -LiteralPath $inF -Value $req -Encoding ascii

    $saved = @{}
    foreach ($k in $EnvMap.Keys) {
        $saved[$k] = [Environment]::GetEnvironmentVariable($k)
        [Environment]::SetEnvironmentVariable($k, [string]$EnvMap[$k])
    }
    $proc = $null
    try {
        $proc = Start-Process -FilePath $Cmd -ArgumentList $ArgList -NoNewWindow -PassThru `
            -RedirectStandardInput $inF -RedirectStandardOutput $outF -RedirectStandardError $errF
        $deadline = (Get-Date).AddSeconds($TimeoutSec)
        $text = ''
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 400
            if (Test-Path -LiteralPath $outF) { $text = Read-SharedText $outF }
            if ($text -match '"serverInfo"') { break }
            if ($proc.HasExited -and $text) { break }
        }
        $ok = (($text -match '"jsonrpc"') -and ($text -match '"result"'))
        $serverName = $null; $serverVer = $null
        if ($text -match '"serverInfo"\s*:\s*\{[^}]*?"name"\s*:\s*"([^"]+)"') { $serverName = $Matches[1] }
        if ($text -match '"serverInfo"\s*:\s*\{[^}]*?"version"\s*:\s*"([^"]+)"') { $serverVer = $Matches[1] }
        $errText = ''
        if (Test-Path -LiteralPath $errF) { $errText = Read-SharedText $errF }
        return [pscustomobject]@{ Ok = $ok; Server = $serverName; Version = $serverVer; Stdout = $text; Stderr = $errText }
    } catch {
        return [pscustomobject]@{ Ok = $false; Server = $null; Version = $null; Stdout = ''; Stderr = $_.Exception.Message }
    } finally {
        if ($proc -and -not $proc.HasExited) { try { [void]$proc.Kill() } catch { } }
        foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) }
        Remove-Item -LiteralPath $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Resolve-Spec {
    # Ordered attempts; a tier is only accepted if it ANSWERS, unless -NoProbe.
    # This is why a stale manifest degrades a repo to the next tier instead of breaking it.
    param([string]$Root, [string]$Stem, [string[]]$BaseEnv = @(), [switch]$NoProbe)
    $script:LastProbe = $null
    $tiers = @()
    $manifestSpec = Get-ManifestSpec $Root
    if ($manifestSpec) { $tiers += $manifestSpec }
    $tiers += (Get-LaunchSpec $Root $Stem)

    foreach ($tier in $tiers) {
        if (-not $tier.Command) { continue }
        if ($NoProbe) { return $tier }
        if ($tier.NeedsSync) { continue }
        $probeEnv = Convert-EnvPairsToMap (@($BaseEnv) + @($tier.EnvPairs))
        $probe = Test-StdioHandshake -Cmd $tier.Command -ArgList $tier.Arguments -EnvMap $probeEnv
        $script:LastProbe = $probe
        if ($probe.Ok) {
            Write-Step ("  ok: {0}  [{1} {2}]" -f $tier.How, $probe.Server, $probe.Version)
            return $tier
        }
        $why = (($probe.Stderr -split "`r?`n") | Where-Object { $_ -match '\S' } | Select-Object -Last 1)
        Write-Step ("  rejected: {0} - {1}" -f $tier.How, $(if ($why) { $why.Trim() } else { 'no handshake response' }))
    }
    return $null
}


function Get-ReleaseInstaller([string]$RepoName, [string]$Wanted) {
    # Latest GitHub release, preferring an NSIS asset. Public repos need no auth.
    $api = "https://api.github.com/repos/sandraschi/$RepoName/releases/latest"
    try {
        $rel = Invoke-RestMethod -Uri $api -Headers @{ 'User-Agent' = 'fleet-install' } -TimeoutSec 20
    } catch { return $null }
    $assets = @($rel.assets)
    if (-not $assets.Count) { return $null }
    $pick = $null
    if ($Wanted) { $pick = $assets | Where-Object { $_.name -eq $Wanted } | Select-Object -First 1 }
    if (-not $pick) { $pick = $assets | Where-Object { $_.name -match '(?i)(setup|installer).*\.exe$' } | Select-Object -First 1 }
    if (-not $pick) { $pick = $assets | Where-Object { $_.name -match '(?i)\.exe$' } | Select-Object -First 1 }
    if (-not $pick) { return $null }
    return [pscustomobject]@{ tag = $rel.tag_name; name = $pick.name; url = $pick.browser_download_url; size = $pick.size }
}

function Invoke-WebappMode([string]$Root, [switch]$ProvisionOnly, [switch]$AllowBrowser) {
    $launcher = Join-Path $Root 'start.ps1'
    if (-not (Test-Path -LiteralPath $launcher)) {
        Write-Step '  webapp: no start.ps1 in this repo - nothing to launch'
        return
    }
    if ($ProvisionOnly) {
        Write-Step "  webapp: launcher present. Run: $launcher"
        return
    }
    # Pass -NoBrowser only if the repo's start.ps1 actually declares it.
    $text = Get-Content -LiteralPath $launcher -Raw
    $launchArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $launcher)
    if (-not $AllowBrowser -and $text -match '\$NoBrowser') { $launchArgs += '-NoBrowser' }
    $pwshExe = (Get-Process -Id $PID).Path
    $proc = Start-Process -FilePath $pwshExe -ArgumentList $launchArgs -WorkingDirectory $Root -PassThru
    Write-Step "  webapp: started start.ps1 (pid $($proc.Id))"
}

function Get-RepoRegistrations([string]$RepoPathPosix) {
    # Compare with ALL separators stripped from both sides. Matching on '\\' vs '/'
    # fails: ConvertTo-Json escapes a backslash as '\\', so a naive Replace turns
    # 'D:\Dev\repos\x' into 'D://Dev//repos//x' and never equals 'D:/Dev/repos/x'.
    # That produced a duplicate 'reversing' entry next to a working 'revops'.
    $needle = ($RepoPathPosix.ToLowerInvariant() -replace '[\\/]', '')
    $userHome = $env:USERPROFILE
    $appData = $env:APPDATA
    $candidates = @(
        @{ File = (Join-Path $appData 'Claude\claude_desktop_config.json'); Key = 'mcpServers' },
        @{ File = (Join-Path $userHome '.cursor\mcp.json'); Key = 'mcpServers' },
        @{ File = (Join-Path $userHome '.gemini\antigravity\mcp_config.json'); Key = 'mcpServers' },
        @{ File = (Join-Path $userHome '.codeium\windsurf\mcp_config.json'); Key = 'mcpServers' },
        @{ File = (Join-Path $userHome '.config\opencode\opencode.json'); Key = 'mcp' }
    )
    $found = @()
    foreach ($c in $candidates) {
        if (-not (Test-Path -LiteralPath $c.File)) { continue }
        try { $cfg = [IO.File]::ReadAllText($c.File).TrimStart([char]0xFEFF) | ConvertFrom-Json } catch { continue }
        $bag = $cfg.PSObject.Properties[$c.Key]
        if (-not $bag) { continue }
        foreach ($entry in $bag.Value.PSObject.Properties) {
            $flat = (($entry.Value | ConvertTo-Json -Depth 6 -Compress).ToLowerInvariant() -replace '[\\/]', '')
            if ($needle -and $flat.Contains($needle)) { $found += $entry.Name }
        }
    }
    return @($found | Select-Object -Unique)
}

$registeredAs = @(Get-RepoRegistrations $repoPathPosix)
if (-not $Name) {
    if ($registeredAs.Count) {
        $alias = $registeredAs[0]
        Write-Step "alias: reusing existing registration '$alias' (points at this repo)"
    } else {
        Write-Step "alias: '$alias' (no existing registration found for this repo)"
    }
}

# Fail closed: never silently overwrite another server's entry that shares the alias.
if (-not $Check -and -not $Uninstall) {
    $probe = & $writer -Name $alias -List -Json
    $present = @(($probe | ConvertFrom-Json) | Where-Object { $_.status -eq 'present' } | ForEach-Object { $_.label })
    if ($present.Count -and ($registeredAs -notcontains $alias)) {
        Write-Fail "alias '$alias' is already registered in $($present -join ', ') but points at a different server. Re-run with -Name <alias> to pick a distinct name."
    }
}

# ---- resolve the stdio launch command (manifest contract first, then fallbacks) ---
# -Check/-List/-Uninstall always inspect the MCP registration regardless of -Mode.
$doMcp = ($Mode -eq 'mcp') -or ($Mode -eq 'all') -or $Check -or $List -or $Uninstall
$probeDisabled = $Check -or $DryRun -or $List -or $Uninstall
$spec = $null
if ($doMcp) {
    if ($Command) {
        $spec = [pscustomobject]@{ Command = $Command; Arguments = @($Arguments); EnvPairs = @(); NeedsSync = $false; How = 'explicit -Command' }
    } else {
        Write-Step ''
        Write-Step 'resolving launch command ...'
        $spec = Resolve-Spec -Root $repoPath -Stem $repoStem -BaseEnv $EnvPairs -NoProbe:$probeDisabled
    }
}

# ---- -Check ----------------------------------------------------------------------
if ($Check) {
    $uvExe = (Get-Command uv -ErrorAction SilentlyContinue).Source
    $python = Get-VenvPython $repoPath
    $report = [ordered]@{
        repo       = $repoPath
        alias      = $alias
        launch     = $(if ($spec) { $spec.How } else { '<unresolved>' })
        command    = $(if ($spec) { $spec.Command } else { $null })
        arguments  = $(if ($spec) { $spec.Arguments } else { @() })
        venv       = (Test-Path -LiteralPath $python)
        uv         = $uvExe
        needs_sync = $(if ($spec) { $spec.NeedsSync } else { $true })
        probe      = 'skipped (-Check)'
        webapp     = (Test-Path -LiteralPath (Join-Path $repoPath 'start.ps1'))
        desktop    = $(if ($SkipReleaseCheck) { 'skipped' } else {
                $r = Get-ReleaseInstaller -RepoName $repoStem -Wanted $AssetName
                if ($r) { "$($r.name) [$($r.tag)]" } else { 'none' }
            })
        writer     = $writer
    }
    if ($Json) { ConvertTo-Json -InputObject $report -Depth 5 }
    else {
        Write-Host ''
        Write-Host '  repo       ' -NoNewline; Write-Host $report.repo
        Write-Host '  alias      ' -NoNewline; Write-Host $report.alias
        Write-Host '  launch     ' -NoNewline; Write-Host $report.launch
        Write-Host '  command    ' -NoNewline; Write-Host $(if ($report.command) { $report.command } else { '<unresolved>' })
        Write-Host '  venv       ' -NoNewline; Write-Host $report.venv
        Write-Host '  uv         ' -NoNewline; Write-Host $(if ($report.uv) { $report.uv } else { '<missing>' })
        Write-Host '  needs sync ' -NoNewline; Write-Host $report.needs_sync
        Write-Host '  webapp     ' -NoNewline; Write-Host $(if ($report.webapp) { 'start.ps1 present' } else { 'no start.ps1' })
        Write-Host '  desktop    ' -NoNewline; Write-Host $report.desktop
        Write-Host ''
        Write-Host '  Detected clients:' -ForegroundColor Cyan
        & $writer -Name $alias -List
    }
    exit 0
}

# ---- ensure the launch command actually exists -----------------------------------
# Nothing answered: build the venv once, then retry the whole tier ladder.
if ($doMcp -and -not $spec -and -not $probeDisabled) {
    $venvPython = Get-VenvPython $repoPath
    # NEVER re-sync an EXISTING venv. `uv sync` reconciles to the base dependency set and
    # PRUNES whatever the optional extras installed: reversing-mcp lost pyghidra, frida,
    # pywinauto, pytest and 43 more this way. Build only when there is no venv at all.
    if (-not (Test-Path -LiteralPath $venvPython)) {
        $uvExe = (Get-Command uv -ErrorAction SilentlyContinue).Source
        if (-not $uvExe) {
            if (-not $Yes) { Write-Fail "uv is required to build the venv but is not on PATH. Install with: winget install --id astral-sh.uv --source winget   (or re-run with -Yes)" }
            if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { Write-Fail "uv missing and winget unavailable - install uv manually (astral-sh.uv)" }
            Write-Step 'installing uv via winget ...'
            winget install --id astral-sh.uv --source winget --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
            $env:PATH = [System.Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' + [System.Environment]::GetEnvironmentVariable('PATH', 'User')
            $uvExe = (Get-Command uv -ErrorAction SilentlyContinue).Source
            if (-not $uvExe) { Write-Fail 'uv installed but not on PATH - reopen PowerShell and re-run' }
        }
        $effectiveExtras = @($SyncExtras)
        if (-not $effectiveExtras.Count) { $effectiveExtras = @(Get-FleetSyncExtras $repoPath) }
        $syncArgs = @('sync', '--project', $repoPath)
        foreach ($extraName in $effectiveExtras) { $syncArgs += @('--extra', $extraName) }
        Write-Step "no venv - building: uv $($syncArgs -join ' ')"
        & $uvExe @syncArgs
        if ($LASTEXITCODE -ne 0) { Write-Fail 'uv sync failed' }
        $spec = Resolve-Spec -Root $repoPath -Stem $repoStem -BaseEnv $EnvPairs
    }
}

if ($doMcp -and -not $spec -and -not ($List -or $Uninstall)) {
    $lastErr = ''
    if ($script:LastProbe -and $script:LastProbe.Stderr) {
        $lastErr = (($script:LastProbe.Stderr -split "`r?`n") | Where-Object { $_ -match '\S' } | Select-Object -Last 3) -join ' | '
    }
    Write-Fail "could not prove a stdio launch command for $repoStem. Tried mcpb/manifest.json and pyproject/src/run_server.py. Last stderr: $lastErr   Pass -Command explicitly if the repo needs a custom entrypoint."
}

# ---- delegate to the canonical writer --------------------------------------------
if ($doMcp) {
$mergeEnv = @{}
foreach ($pair in @(if ($spec) { $spec.EnvPairs } else { @() })) { if ($pair -match '^([^=]+)=(.*)$') { $mergeEnv[$Matches[1]] = $Matches[2] } }
foreach ($pair in $EnvPairs) {
    if ($pair -match '^([^=]+)=(.*)$') { $mergeEnv[$Matches[1]] = $Matches[2] }
}
$envFlat = @()
foreach ($k in $mergeEnv.Keys) { $envFlat += "$k=$($mergeEnv[$k])" }

# Hashtable splat, not an array: an array splat passes a nested array as ONE
# argument (Object[] -> -EnvPairs -> wrong parameter), while a hashtable binds
# array values to [string[]] parameters correctly.
$writerArgs = @{ Name = $alias; EnvPairs = $envFlat }
if ($spec -and $spec.Command) { $writerArgs['Command'] = $spec.Command }
if ($spec -and $spec.Arguments.Count) { $writerArgs['Arguments'] = $spec.Arguments }
if ($Clients) { $writerArgs['Clients'] = $Clients }
if ($Uninstall) { $writerArgs['Uninstall'] = $true }
if ($List) { $writerArgs['List'] = $true }
if ($DryRun) { $writerArgs['DryRun'] = $true }
if ($Json) { $writerArgs['Json'] = $true }

if (-not $Json) {
    Write-Host ''
    Write-Host "  Registering '$alias'" -ForegroundColor Cyan
    Write-Host "  command: $(if ($spec) { $spec.Command } else { '<none>' })" -NoNewline
    if ($spec -and $spec.Arguments.Count) { Write-Host " $($spec.Arguments -join ' ')" } else { Write-Host '' }
    Write-Host ''
}

& $writer @writerArgs
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# ---- webapp mode ------------------------------------------------------------------
# Provisions and launches the fleet launcher (start.ps1): winget prereqs, uv sync with
# the repo's SyncExtras, npm install, port clearing, uvicorn + vite. -Mode all only
# reports it, because starting servers is not something "install" should do silently.
if ($Mode -eq 'webapp' -or $Mode -eq 'all') {
    Invoke-WebappMode -Root $repoPath -ProvisionOnly:($NoStart -or $Mode -eq 'all') -AllowBrowser:$OpenBrowser
}

# ---- desktop mode -----------------------------------------------------------------
# Tauri/NSIS installers are release assets, never run as a side effect of registering
# an MCP server. Requires -Yes; without it the exact asset is named and nothing runs.
if ($Mode -eq 'desktop' -or $Mode -eq 'all') {
    if ($SkipReleaseCheck) {
        Write-Step '  desktop: release check skipped'
    } else {
        $rel = Get-ReleaseInstaller -RepoName $repoStem -Wanted $AssetName
        if (-not $rel) {
            Write-Step '  desktop: no .exe asset in the latest GitHub release'
        } elseif ($Mode -eq 'all') {
            Write-Step ("  desktop: available - {0} ({1:N1} MB, {2}) - re-run with -Mode desktop -Yes" -f $rel.name, ($rel.size / 1MB), $rel.tag)
        } elseif (-not $Yes) {
            Write-Step ("  desktop: would install {0} ({1:N1} MB, {2}) - re-run with -Yes to run it" -f $rel.name, ($rel.size / 1MB), $rel.tag)
        } else {
            $dest = Join-Path $env:TEMP $rel.name
            Write-Step "  desktop: downloading $($rel.name)"
            Invoke-WebRequest -Uri $rel.url -OutFile $dest -UseBasicParsing
            Write-Step ("  desktop: sha256 " + (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash)
            Write-Step '  desktop: running the NSIS installer silently (/S)'
            $inst = Start-Process -FilePath $dest -ArgumentList '/S' -PassThru -Wait
            Write-Step "  desktop: installer exit code $($inst.ExitCode)"
        }
    }
}
