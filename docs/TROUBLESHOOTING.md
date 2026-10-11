# Troubleshooting — reversing-mcp

## Backend never becomes ready (`start.ps1` loops 60s then exits 1)

- Read the dumped job output (the launcher prints it on failure).
- Common cause: `uvicorn` missing (run `uv sync --all-extras`) or port :10750 held
  by a stale backend (the launcher clears zombies first; check manually with
  `Get-NetTCPConnection -LocalPort 10750`).
- Never run `python -m reversing_mcp` expecting HTTP: that is stdio-only.

## Dashboard says Offline but curl works

- The frontend uses `getApiBase()` (env `VITE_API_URL` → localStorage → default).
  If Settings points elsewhere, fix the API base URL there.
- Browser tabs on non-localhost hostnames need the CORS regex (already configured);
  do not widen origins — use same-origin + Tauri gate instead.

## Chat returns 409 "No Ollama model available"

- Honest signal, not a bug: start Ollama and pull any model, then retry.
  Default is resident-first (never evicts a loaded model).

## Ghidra shows "not found" / bridge down

- Headless tools need `GHIDRA_INSTALL_DIR`. Interactive decompile needs the ReVa
  MCP server + bridge on `:8089` (`GHIDRA_BRIDGE_URL`).
- REA native via Ghidra on Windows is experimental upstream; raise `timeout_s`
  and `REA_GHIDRA_STARTUP_TIMEOUT_MS` for big binaries.

## REA says "not found"

- `just setup-rea` (Node 22.19+ required), then restart the agent. `just check-rea`
  shows version + providers. See `docs/REA.md` §7 troubleshooting table.

## Logs page empty

- The in-app log is a ring buffer fed by backend events; empty after restart is normal.
  For MCP server logs: `C:\Users\sandr\AppData\Roaming\Claude\logs\mcp-server-revops.log`.

## Tests fail on fixtures

- See `tests/fixtures/MANIFEST.md` for ground truth + toolchain installs.
  REA-gated tests skip when the sidecar is absent; volume tests skip without
  `DIGITALE_BIBLIOTHEK_ROOT`.
