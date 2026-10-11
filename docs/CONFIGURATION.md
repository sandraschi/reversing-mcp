# Configuration — reversing-mcp

## Ports (fleet registry)

| Service | Port |
|---------|------|
| Backend (FastAPI REST + `/mcp` mount) | 10750 |
| Frontend (Vite dev) | 10751 |

## Environment variables

| Var | Default | Purpose |
|-----|---------|---------|
| `GHIDRA_INSTALL_DIR` | auto-detect | Headless Ghidra (`analyze_binary [...,'ghidra']`, `find_functions`) |
| `DIGITALE_BIBLIOTHEK_ROOT` | auto-detect | `DB*` parent for `decompress_directmedia_library` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Webapp Chat + LLM discovery |
| `GHIDRA_BRIDGE_URL` | `http://127.0.0.1:8089` | Webapp Ghidra-status proxy target (ReVa/bridge) |
| `REA_ANALYSIS_PROVIDER` | auto | REA native engine (`hopper`, `ghidra`, `ida`) |
| `REA_IDA_MCP_CONFIG` | — | Path to `ida-pro-mcp` config (IDA adapter) |
| `REA_GHIDRA_STARTUP_TIMEOUT_MS` | upstream default | Raise for big binaries |
| `MCP_TRANSPORT/HOST/PORT/PATH` | stdio/127.0.0.1/10750//mcp | `transport.py` dual-transport switch |

## Launchers

- `.\start.ps1` / `.\start.bat` (repo root): uvicorn backend + Vite frontend.
  Flags: `-BackendOnly`, `-NoBrowser`, `-Headless`.
- Fleet: `mcp-central-docs\starts\reversing-start.bat` + `fleet-start.config.ps1`
  (`uvicorn reversing_mcp.server:app`).
- Claude Desktop (stdio): `uv run python -m reversing_mcp.server`.
- HTTP MCP stream: `uv run python -m reversing_mcp.server --http --port 10750`.

## REST surface (36 routes)

Triage/analysis: `/analyze/upload`, `/analyze/file`, `/tools/status`.
Ghidra bridge proxy: `/ghidra/status|instances|connect|functions|decompile|disassemble`, `/start_ghidra`.
LLM: `/llm/*` (providers/models/select/load/unload/status/health), `/api/llm/discover`,
`/api/llm/providers`, `/api/llm/models`, `/api/llm/onboarding`, `/api/llm/chat`,
`/api/v1/chat`. Skills: `/api/skills`, `/api/skills/{name}`, `/skill/{name}`.
Ops: `/health`, `/api/v1/diagnostics`, `/api/shutdown`, `/api/capabilities`, `/api/logs*`.
Digibib: `/api/v1/digibib/*` (5 routes). MCP: `/mcp` mount. Docs: `/docs`, `/redoc`.
