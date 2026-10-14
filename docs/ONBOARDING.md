# Onboarding — reversing-mcp

First-timer path from zero to first analysis. **You never hand-edit env and
never hand-install engines**: `start.ps1` boots the backend, the backend runs
the toolbox (`GET /api/v1/toolbox`, `toolbox(operation="probe")`) which
discovers everything (PATH, env, `D:\Dev\tools`, standard locations), exports
what it finds into its own environment, installs what is missing, and starts
policy services. The Status page Toolbox card shows the inventory with
one-click Install buttons. No wrappee install is needed for the core (static
triage works out of the box); each engine below unlocks a deeper tier.

## What this is for

Agent-driven static binary analysis + Directmedia/Digibib5 format recovery, with an
optional REA sidecar for JS/Electron/native-via-provider work. Money involved: none
for the core; Hopper (~$100, macOS/Linux only) and IDA Pro ($$$$) are optional commercial
engines. Full engine list: [ENGINES.md](ENGINES.md).

## Prerequisites

- Python 3.12 + `uv` (`uv sync --all-extras` in repo root).
- Node 22+ only if you want the REA sidecar (`npx rea-agents setup`).
- Ollama only if you want webapp Chat (any model; resident-first default).

## Sanity check (2 minutes)

```powershell
.\start.ps1 -BackendOnly
# expect: "Backend ready on port 10750"
Invoke-WebRequest http://127.0.0.1:10750/health -UseBasicParsing
# expect: {"status":"ok","version":"0.4.0","tool_count":15}
uv run pytest tests/test_mcp_server.py -q
```

## Tier unlocks

| Tier | Needs (toolbox handles it) | Gives |
|------|-------|-------|
| 1 static triage | nothing (Python stdlib + `file`) | `analyze_binary`, strings, entropy, PE, DKI |
| 1+ engines | auto: Ghidra (GitHub release to `D:\Dev\tools`), DiE, capa; nothing by hand | headless decompile, function discovery, packer ID, capabilities |
| 1+ ReVa | auto: pip venv + compat + extension (or Status page Install) | 86 Ghidra tools over MCP; autostarts with backend |
| 2 REA sidecar | Node 22.19+ → `just setup-rea`, restart agent | `rea_investigate`: JS/Electron/.NET/APK/firmware/browser/native |
| 2 native providers | IDA: start it (or set `IDA_DIR`) — a **running** IDA is glommed onto, licensing is your business; Hopper: macOS/Linux only ([HOPPER.md](HOPPER.md)) | deeper native via REA |
| Chat | Ollama: dashboard cue offers Start (installed, idle), Install (absent), or Pull (serving, model-less) — no manual steps | webapp AI Command page |

If the toolbox reports a tool `missing` with an Install button, click it.
If it reports `license`/`platform_blocked`, read the row's note — those are
the only two cases that need you.

## Pitfalls

- Backend must be the FastAPI app (`uvicorn reversing_mcp.server:app`, what `start.ps1`
  launches) — `python -m reversing_mcp` is stdio-only and never binds :10750.
- No Ollama model → chat returns honest 409, not a hallucination. Pull any model first.
- Windows-Ghidra via REA is experimental upstream; big binaries need long timeouts.
- Lawful targets only (security research, education, interoperability, format recovery).

## MOCK-until-onboarded

N/A — no mock KPIs in this webapp. Every number on the dashboard comes from a live
backend probe; when the backend is down the UI says Offline, never a fake green.
