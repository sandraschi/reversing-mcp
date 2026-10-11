# Onboarding — reversing-mcp

First-timer path from zero to first analysis. No wrappee install is needed for the
core (static triage works out of the box); each engine below unlocks a deeper tier.

## What this is for

Agent-driven static binary analysis + Directmedia/Digibib5 format recovery, with an
optional REA sidecar for JS/Electron/native-via-provider work. Money involved: none
for the core; Hopper (~$100) and IDA Pro ($$$$) are optional commercial engines.

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

| Tier | Needs | Gives |
|------|-------|-------|
| 1 static triage | nothing (Python stdlib + `file`) | `analyze_binary`, strings, entropy, PE, DKI |
| 1+ engines | Ghidra (`GHIDRA_INSTALL_DIR`) / radare2 / binwalk | headless decompile, function discovery |
| 2 REA sidecar | Node 22.19+ → `just setup-rea`, restart agent | `rea_investigate`: JS/Electron/.NET/APK/firmware/browser/native |
| 2 native providers | Hopper (buy, auto-installed) / IDA Pro (own seat + `REA_IDA_MCP_CONFIG`) | deeper native via REA; IDA is bring-your-own-license |
| Chat | Ollama running | webapp AI Command page |

## Pitfalls

- Backend must be the FastAPI app (`uvicorn reversing_mcp.server:app`, what `start.ps1`
  launches) — `python -m reversing_mcp` is stdio-only and never binds :10750.
- No Ollama model → chat returns honest 409, not a hallucination. Pull any model first.
- Windows-Ghidra via REA is experimental upstream; big binaries need long timeouts.
- Lawful targets only (security research, education, interoperability, format recovery).

## MOCK-until-onboarded

N/A — no mock KPIs in this webapp. Every number on the dashboard comes from a live
backend probe; when the backend is down the UI says Offline, never a fake green.
