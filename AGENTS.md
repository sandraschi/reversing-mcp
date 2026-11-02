# reversing-mcp — Agent Context

Quick reference for reversing-mcp — static binary analysis and Directmedia tools MCP server.

## Quick Ref
```powershell
uv run python -m reversing_mcp.server    # Start stdio MCP
uv run python -m reversing_mcp.server --http --port 10750  # HTTP mode
uv run pytest tests/ -q                  # Test
uv run ruff check src/ tests/            # Lint
just install-idr                         # Install IDR (Delphi reconstructor)
```

## Ports
| Service | Port |
|---------|------|
| Backend (MCP + API) | 10750 |
| Frontend (Vite dev) | 10751 |

## Tools (17)
All registered in `server.py`; implementations in `analyzers.py`, `directmedia_dki.py`, `digibib_research.py`, `rea_bridge.py`.

| Tool | Description |
|------|-------------|
| `analyze_binary` | Full analysis: file type, strings, entropy, functions |
| `extract_strings` | Extract ASCII/Unicode strings with context |
| `get_hexdump` | Hex dump at byte offset |
| `analyze_entropy` | Shannon entropy per block |
| `find_functions` | Function discovery (Ghidra/radare2) |
| `get_file_info` | File command metadata |
| `check_tools` | Reversing tool availability check (incl. REA sidecar) |
| `rea_investigate` | REA sidecar delegate: JS/Electron/native via provider |
| `digibib_research_snapshot` | DigiBib 5.exe research report |
| `analyze_pe_file` | PE structure analysis |
| `decode_dki_file` | DKI format decoder |
| `analyze_directmedia_file` | Directmedia container analysis |
| `decompress_directmedia_library` | DM library extraction |
| `shutdown` | Graceful server shutdown |
| `show_tools_card` | Engine inventory as in-chat Prefab card |
| `gym` | Cloning-run lifecycle (start/status/advance/stop/list) |
| `engine` | DiE / capa / Frida: compiler+packer ID, capabilities, runtime hooks |
| `help` | Multi-level help system |

## Documentation Map
- `README.md` — short starter (links to sub-docs below)
- `INSTALL.md` — quick start + manual setup + troubleshooting
- `docs/REVA.md` — **ReVa MCP guide** (install, assistant/headless modes, client config, two-server workflow)
- `docs/REA.md` — **REA sidecar guide** (agent-driven native + JS/Electron/.NET/APK/firmware/browser, setup, three-server workflow)
- `docs/CUA_DISASSEMBLY_COMBO.md` — **Tier 3 spec** (CUA tour + disassembly = feature-to-code maps; spec, not built)
- `docs/GYM_SPEC.md` — **Reversing Gym product spec** (oracle cloning pipeline, stages 0-8, gates)
- `docs/ELICITATION_AND_CLICKER.md` — **Gym playbook** (stage-1b format/docs mining + stage-3 clicker layers, algorithms, papers)
- `docs/GHIDRA.md` — **Ghidra headless guide** (analyzeHeadless, scripts, CLI reference)
- `docs/DIRECTMEDIA_MISSION.md` — Directmedia / Digibib5 mission scope
- `docs/DIRECTMEDIA_REVERSING_TOOLKIT.md` — CLI/MCP reversing toolkit
- `docs/DIGIBIB_REVERSING_GUIDE.md` — **DigiBib reversing guide** (dynamic tracing, Frida, procmon, Delphi detection, offset-table extraction)
- `docs/IDR.md` — **IDR Delphi reconstructor** guide (install, workflow, Ghidra map import, Delphi internals)
- `docs/IDA.md` — **IDA Pro integration** (headless analysis, env var setup, scripting)
- `docs/DIGIBIB_DECOMPILE_PLAN.md` — phased EXE reverse plan
- `PRD.md` — vision: agent-driven feature-to-code-map platform (tiers, requirements, roadmap)
- `llms-full.txt` — full LLM tool reference

## Architecture
```
server.py (FastMCP 3.4+)
  ├── analyzers.py       — BinaryAnalyzer (Ghidra, radare2, binwalk, PE, entropy, strings)
  ├── rea_bridge.py      — REA sidecar subprocess bridge (find/run/truncate)
  ├── gym.py             — Gym G1 job runner (intake/triage/assessment, run dirs)
  ├── directmedia_dki.py — DKI decode/decompress
  ├── digibib_research.py — DigiBib research snapshot builder
  ├── transport.py       — Dual transport (stdio/HTTP/SSE)
  └── logging_config.py  — Logger factory
web_sota/                — SOTA Vite/React dashboard (port 10751)
native/                  — Tauri 2.0 NSIS wrapper (PyInstaller + Rust)
```

## Linting Rules
- Python: `ruff` (line length 120, select E/F/W/I/B/S/UP/RUF)
- Webapp: `biome` (CI mode, no console.log)
- No bare `except: pass` — always log exceptions
- No `print()` in prod Python code (use logger)

## Multi-agent working rules (several agents and IDEs)

Several agents (Claude Code, OpenCode, Cursor, Windsurf and others) work on this repo from
different IDEs, sometimes at the same time. These rules exist because that went wrong once:
one agent ran a commit-all and swept another agent's half-finished manifest edits into a
release and a pushed tag, leaving the pushed tree unbuildable.

Fleet standard with the full reasoning: `mcp-central-docs/standards/MULTI_AGENT_CONCURRENCY.md`.

### Before you start

1. Run `git status` and `git log -5 --format="%h %ad %s" --date=iso`. If the tree is dirty and
   you did not make those changes, someone else is working here. Leave their files alone:
   do not reset, clean, stash or revert them.
2. Prefer your own branch (`agent/<tool>-<topic>`) or a worktree
   (`git worktree add ..\<repo>-<topic> -b agent/<tool>-<topic>`). Merge to the default branch
   only when the work is finished and checked.

### Committing

- Never `git add -A`, `git add .`, `git commit -a` or `git commit -am`. Name your paths:
  `git add <path> ...` then `git commit -m "..." -- <path> ...`.
- Before committing run `git diff --cached --stat` and check every file is yours.
- A manifest (`Cargo.toml`, `package.json`, `pyproject.toml`) and the files it points at go in the
  same commit. Never commit a manifest that names something not in the commit.
- Do not tag or release from a dirty tree, or from a `WIP-Auto` commit made by the nightly sweep.
  Before tagging, a clean clone of the exact commit must build and pass tests.
- Do not move or delete a published tag; add a new one. Do not force-push a shared branch.
- Do not push another agent's commits you did not read.

### Hooks

`.githooks/pre-commit` rejects a commit whose Cargo manifests name workspace members or path
dependencies that are not tracked. Enable it once per clone:

    git config core.hooksPath .githooks

Do not bypass it with `--no-verify`. If it blocks you, the commit really is broken.

### Leave a trail

- Commit messages say what and why. Agent commits end with the tool's own trailer.
- Long-running work: note it in the repo's worklog or plan file so the next agent sees it.
- At the end of a session, say what you left uncommitted and whose it appears to be.
