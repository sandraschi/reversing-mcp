# reversing-mcp Agent Context

Quick reference for reversing-mcp — static binary analysis and Directmedia tools MCP server.

## Quick Ref
```powershell
# Start
uv run python -m reversing_mcp.server
# Tests
uv run pytest tests/ -q
# Lint
uv run ruff check src/ tests/
```

## Ports
| Service | Port |
|---|---|
| Backend | 10750 |

## Architecture
FastMCP server wrapping Ghidra headless analysis (DecompInterface) and Directmedia tools. Tools for binary analysis, decompilation, and pattern matching.
