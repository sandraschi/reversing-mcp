# CLAUDE.md — reversing-mcp

## Quick Start
```powershell
uv run python -m reversing_mcp.server    # Start MCP server (stdio)
uv run ruff check src/ tests/            # Lint
uv run pytest tests/ -q                  # Test
```

## Ports
- Backend: 10750 (MCP + FastAPI health)
- Frontend: 10751 (Vite dev server)

## Architecture
- FastMCP 3.4+ server wrapping Ghidra headless decompilation + radare2 + binwalk
- Dual transport: stdio (Claude Desktop default) and HTTP (--http flag)
- 12 analysis tools + help system
- Legacy webapp at `reversing-webapp/` (Next.js), SOTA webapp at `web_sota/` (Vite/React)
- Tauri native wrapper at `native/`

## Key Rules
- **No console.log** in webapp (Biome enforces)
- **No bare `except: pass`** — always log exceptions
- `ruff` for Python linting (line length 120), `biome` for webapp
- `uv sync` for dependencies, `uv run` for execution

## Tools (all in server.py, impls in analyzers.py)
| Tool | Description |
|------|-------------|
| `analyze_binary` | Run all analysis passes on a binary |
| `extract_strings` | Extract readable strings |
| `get_hexdump` | Hex dump at byte offset |
| `analyze_entropy` | Shannon entropy per block |
| `find_functions` | Discover functions (Ghidra/radare2) |
| `get_file_info` | File metadata |
| `check_tools` | System tool availability check |
| `digibib_research_snapshot` | DigiBib PE research |
| `analyze_pe_file` | PE structure parsing |
| `decode_dki_file` | DKI file decoder |
| `analyze_directmedia_file` | DM container analysis |
| `decompress_directmedia_library` | DM library archive extraction |
| `help` | Multi-level documentation |
