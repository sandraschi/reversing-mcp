set windows-shell := ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]
import 'scripts/just/fleet.just'

# --- Core ---

# Serve the MCP server (stdio mode)
serve:
    uv run python -m reversing_mcp.server

# Run tests
test:
    uv run pytest tests/ -q

# Install IDR (Interactive Delphi Reconstructor)
install-idr:
    powershell.exe -NoProfile -File scripts/Install-IDR.ps1

# --- REA sidecar (agent-driven RE: JS/Electron/.NET/APK/firmware + native) ---

# Register REA with your agents (backs up configs, then restart the agent)
setup-rea:
    npx rea-agents setup

# Check REA version + available native providers
check-rea:
    npx -y rea-agents@latest --version
    npx -y rea-agents@latest providers --json

# Refresh REA registrations (npm-global users: `rea update` instead)
update-rea:
    npx rea-agents@latest setup

# --- Dashboard ---

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# --- Quality ---

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'; uv run ruff check .; Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome ci src

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'; uv run ruff check . --fix --unsafe-fixes; uv run ruff format .; Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome check --write src

# Alias for fix (fleet gate name)
fmt:
    just fix

# Full local gate (CI runs the same; private repos keep Actions disabled per fleet standard)
ci:
    Set-Location '{{justfile_directory()}}'; uv run ruff check src/ tests/; uv run ruff format --check src/ tests/; uv run pyright src/; uv run pytest tests/ -q; Set-Location '{{justfile_directory()}}\web_sota'; npx tsc --noEmit; npx @biomejs/biome ci src

# Browser end-to-end: CUA webapp walk (stack start + nav walk in browser)
e2e:
    powershell.exe -NoProfile -File '{{justfile_directory()}}\scripts\just\cua-webapp-test.ps1'

# --- Hardening ---

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
	Set-Location '{{justfile_directory()}}'
	uv run safety check

# --- Tauri NSIS ---

# Build the Tauri NSIS desktop installer (full pipeline: frontend -> Rust -> NSIS)
build-native:
	$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"; $vcvars = "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"; $envOutput = cmd /c "`"$vcvars`" > nul & set" | Where-Object { $_ -match '^(INCLUDE|LIB|LIBPATH|VCToolsVersion|WindowsSdkDir|UniversalCRTSdkDir|UCRTVersion)=' }; foreach ($line in $envOutput) { $parts = $line.Split('=', 2); Set-Item -Path "env:$($parts[0])" -Value $parts[1] -ErrorAction SilentlyContinue }; Set-Location '{{justfile_directory()}}\native'; powershell.exe -NoProfile -File '{{justfile_directory()}}\native\build.ps1'


# Bootstrap: install dev deps + pre-commit hook
bootstrap:
    uv sync --group dev
    uv run pre-commit install
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green