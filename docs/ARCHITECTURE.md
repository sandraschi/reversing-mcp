# Architecture - reversing-mcp

FastMCP 3.4 server + FastAPI HTTP app in one process (`src/reversing_mcp/server.py`).
Ports: backend :10750 (REST + MCP), frontend :10751 (Vite dev). No lifespan on
the MCP object; one FastAPI `startup` hook runs the toolbox.

## Modules

| Module | Job |
|--------|-----|
| `server.py` | 20 MCP tools + ~50 REST routes + `skill://` resources; `toolbox` boot hook |
| `analyzers.py` | `BinaryAnalyzer` (static triage, Ghidra/r2/binwalk dispatch) |
| `engines.py` | DiE/capa/Frida wrappers (cancellable Popen + tree kill) + finders |
| `toolbox.py` | Autodiscovery/install/autostart for the toolchain (see TOOLBOX.md) |
| `reva.py` | ReVa lifecycle (probe/start/stop managed child) |
| `gym.py` | Cloning-run pipeline G1 (intake/triage/assessment, workers) |
| `clickerlab.py` | G1b elicitation + G3 clicker sessions + §5 correlate |
| `rea_bridge.py` | REA sidecar subprocess bridge (truncating) |
| `directmedia_dki.py`, `digibib_research.py` | DKI decode + Digibib mission bundle |
| `transport.py`, `logging_config.py` | stdio/HTTP transport, stderr logging |

## Boot (backend)

`start.ps1` (fleet engine) → `uvicorn reversing_mcp.server:app` → FastAPI
startup runs `toolbox.ensure()`: probe → export env (`GHIDRA_INSTALL_DIR`,
`DIE_DIR`) → autostart policy services (ReVa headless). Stdio spawns skip
autostart (on-demand clients must not boot JVMs).

## Data

- Run state: `gym/runs/<id>/` (JSON + artifacts; read via artifact endpoint).
- Stateless analysis otherwise; indexes live with the engines.
- Logs: stderr + in-memory ring (`GET /api/logs`); frontend Logs page tails it.
- Fleet third-party homes (outside `uv sync` reach): `D:\Dev\tools\reva`,
  `D:\Dev\tools\ghidra_12.1.3_PUBLIC`.

## Transports

- stdio (MCP clients) with HTTP-daemon probe pattern per SOTA §2.3.
- HTTP :10750: REST `/api/*`, MCP `/mcp`, CORS pinned to localhost + Tauri.
- Webapp :10751 talks REST only; `getApiBase()` (no hardcoded ports).
