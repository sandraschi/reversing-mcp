# Reversing MCP

[![Just](https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white)](https://github.com/casey/just)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square)](https://github.com/jlowin/fastmcp)

FastMCP 3.4 server for **static binary analysis** and **Directmedia format reversing**.  
Pair with **[ReVa](https://github.com/cyberkaida/reverse-engineering-assistant)** for interactive Ghidra decompilation over MCP.

**Quick start:**
```powershell
git clone https://github.com/sandraschi/reversing-mcp
cd reversing-mcp
just                   # list recipes
just serve             # start MCP server (stdio)
just test              # run tests
```

> Full install: [INSTALL.md](INSTALL.md) · Tools: [llms-full.txt](llms-full.txt) · Changelog: [CHANGELOG.md](CHANGELOG.md)

## What it does

13 tools across four domains:

| Domain | Tools | Docs |
|--------|-------|------|
| **Binary analysis** | `analyze_binary`, `extract_strings`, `get_hexdump`, `analyze_entropy`, `find_functions` | — |
| **File / PE analysis** | `get_file_info`, `analyze_pe_file` | — |
| **Directmedia / DKI** | `decode_dki_file`, `analyze_directmedia_file`, `decompress_directmedia_library`, `digibib_research_snapshot` | [Directmedia mission](docs/DIRECTMEDIA_MISSION.md) · [Toolkit](docs/DIRECTMEDIA_REVERSING_TOOLKIT.md) · [Decompile plan](docs/DIGIBIB_DECOMPILE_PLAN.md) |
| **System** | `check_tools`, `shutdown` | — |

## Ghidra integration — two paths

| Path | When | Setup |
|------|------|-------|
| **Interactive** (ReVa MCP) | You want decompile, xrefs, rename in Ghidra via MCP | [Detailed Ghidra guide](docs/GHIDRA.md) |
| **Headless** (`analyzeHeadless`) | Batch/script analysis from `analyze_binary` | Install Ghidra, set `GHIDRA_INSTALL_DIR` |

## Web UI

SOTA React dashboard on `http://localhost:10751` (backend `:10750`). Upload binaries, view analysis, chat with local LLM.

## Legal

Analyze only binaries you are entitled to analyze. Intended for security research, education, interoperability, and format recovery.
