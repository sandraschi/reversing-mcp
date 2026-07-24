# reversing-mcp — Agent Context

Quick reference for reversing-mcp — static binary analysis and Directmedia tools MCP server.

## Quick Ref
```powershell
uv run python -m reversing_mcp.server    # Start stdio MCP
uv run python -m reversing_mcp.server --http --port 10750  # HTTP mode
uv run pytest tests/ -q                  # Test
uv run ruff check src/ tests/            # Lint
```

## Ports
| Service | Port |
|---------|------|
| Backend (MCP + API) | 10750 |
| Frontend (Vite dev) | 10751 |

## Tools (13)
All registered in `server.py`, implementations in `analyzers.py`, `directmedia_dki.py`, `digibib_research.py`.

| Tool | Description |
|------|-------------|
| `analyze_binary` | Full analysis: file type, strings, entropy, functions |
| `extract_strings` | Extract ASCII/Unicode strings with context |
| `get_hexdump` | Hex dump at byte offset |
| `analyze_entropy` | Shannon entropy per block |
| `find_functions` | Function discovery (Ghidra/radare2) |
| `get_file_info` | File command metadata |
| `check_tools` | Reversing tool availability check |
| `digibib_research_snapshot` | DigiBib 5.exe research report |
| `analyze_pe_file` | PE structure analysis |
| `decode_dki_file` | DKI format decoder |
| `analyze_directmedia_file` | Directmedia container analysis |
| `decompress_directmedia_library` | DM library extraction |
| `help` | Multi-level help system |

## Documentation Map
- `README.md` — short starter (links to sub-docs below)
- `INSTALL.md` — quick start + manual setup + troubleshooting
- `docs/GHIDRA.md` — **detailed Ghidra guide** (ReVa setup, headless, CLI reference, troubleshooting)
- `docs/DIRECTMEDIA_MISSION.md` — Directmedia / Digibib5 mission scope
- `docs/DIRECTMEDIA_REVERSING_TOOLKIT.md` — CLI/MCP reversing toolkit
- `docs/DIGIBIB_DECOMPILE_PLAN.md` — phased EXE reverse plan
- `llms-full.txt` — full LLM tool reference

## Architecture
```
server.py (FastMCP 3.4+)
  ├── analyzers.py       — BinaryAnalyzer (Ghidra, radare2, binwalk, PE, entropy, strings)
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
