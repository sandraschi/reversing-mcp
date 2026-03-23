# Reversing MCP - Reverse Engineering Toolkit

[![FastMCP](https://img.shields.io/badge/FastMCP-2.13+-blue)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-sandraschi/reversing--mcp-blue)](https://github.com/sandraschi/reversing-mcp)

FastMCP 3.1 server for **static** binary analysis and Directmedia/DKI helpers. **ReVa’s MCP tools are not implemented here** — ReVa is a **separate** MCP server ([reverse-engineering-assistant](https://github.com/cyberkaida/reverse-engineering-assistant)); configure both servers in your IDE if you want static tools plus interactive Ghidra.

## Primary mission

**Scope:** This stack is aimed at **small and medium Windows programs**, not at decompiling huge office suites (think **`Digibib5.exe`**, not **`WINWORD.EXE`**).

**Reference example / test case:** **`Digibib5.exe`** and the Directmedia **`.DKI`** volume layout are the main **worked example** to see whether reversing-mcp plus the webapp are actually usable for real (but modest-sized) apps: static overview in the webapp/MCP, deeper work in Ghidra via **ReVa** when needed. The goal is to learn **how those volumes are read and decoded** (especially packed **`text.dki`**), not to promise a universal decompiler.

**Plan:** [docs/DIGIBIB_DECOMPILE_PLAN.md](docs/DIGIBIB_DECOMPILE_PLAN.md). More context: [docs/DIRECTMEDIA_MISSION.md](docs/DIRECTMEDIA_MISSION.md), [docs/DIRECTMEDIA_REVERSING_TOOLKIT.md](docs/DIRECTMEDIA_REVERSING_TOOLKIT.md).

**Built-in `.DKI` helpers** (`decode_dki_file`, `analyze_directmedia_file`, `decompress_directmedia_library`) use **zlib-oriented heuristics**; they may work for some blobs or cleartext `tree.dki`, but **large-book body text** requires the codec and layout from **EXE reverse**. After Ghidra identifies the real reader, extend or replace logic in `src/reversing_mcp/directmedia_dki.py`. **Changelog:** [CHANGELOG.md](CHANGELOG.md).

## Overview

Python toolkit on **FastMCP 3.1+** with programmatic binary analysis and a **Compilation–Decompilation–Comparison (CDC)** test workflow for fixtures.

**Features:**

- Static analysis (PE, strings, entropy, hexdump); optional **headless** Ghidra from this repo; **interactive** Ghidra only via **ReVa** (other MCP server)
- LLM providers: Ollama, LM Studio, OpenAI, Anthropic, Google AI (configurable)
- Web UI: Next.js frontend, FastAPI backend ([reversing-webapp](reversing-webapp/))
- CDC tests: compile fixtures, decompile, compare to source where applicable
- Directmedia: heuristic DKI tools and [docs/DIGIBIB_DECOMPILE_PLAN.md](docs/DIGIBIB_DECOMPILE_PLAN.md) for full EXE-led decode
- Test fixtures including DOS-era game **source** repos (external) for sample complexity

### Ethical use

Typical legitimate uses: security research, malware analysis, interoperability, format recovery, and preservation of obsolete software. Ensure you have the right to analyze any binary you load. This project is not legal advice.

## Quick Start

```powershell
# One-command setup and launch
.\start-webapp.ps1

# Or from fleet (mcp-central-docs): starts\reversing-start.bat

# Frontend http://localhost:10751, backend http://localhost:10750 (see operations/WEBAPP_PORTS.md in mcp-central-docs)
# Webapp also: reversing-webapp\start.bat or .\start.ps1
```

## Architecture

### Core components

```
reversing-mcp/
├── BinaryAnalyzer (analyzers.py)     # Multi-tool analysis engine
├── directmedia_dki.py                # Heuristic DKI / library paths
├── MCP Server (server.py)            # FastMCP 3.1+ interface
├── LLM settings / API                # Provider configuration
├── Web Interface (reversing-webapp/) # Next.js + FastAPI
└── Test Suite (tests/)               # CDC and unit tests
```

### Ghidra integration

| Layer | Where it lives |
|-------|----------------|
| **ReVa MCP tools** (decompile, xrefs, strings in Ghidra, …) | **[ReVa / reverse-engineering-assistant](https://github.com/cyberkaida/reverse-engineering-assistant)** — **not** in reversing-mcp. Add it as a **second** MCP server in your client. |
| **Headless Ghidra** (batch JSON) | This repo: `analyze_binary(..., ['ghidra'])` when `analyzeHeadless` is installed ([docs/GHIDRA.md](docs/GHIDRA.md)). |
| **LaurieWired `ghidra_*` HTTP bridge** | Removed from this repo. |

**Rationale:** [CURSOR_HANDOFF.md](CURSOR_HANDOFF.md), [TODO_REFACTOR.md](TODO_REFACTOR.md).

### AI / LLM

Ollama, LM Studio, OpenAI, Anthropic, Google AI; endpoints such as `/llm/list_providers`, `/llm/load_model`, `/llm/status`.

### Web UI

Upload and analyze binaries, LLM dashboard, static analysis. Ghidra decompilation runs in the IDE via ReVa, not inside the browser.

## CDC testing

**Compilation–Decompilation–Comparison:** compile C/asm fixtures, run tools (e.g. Ghidra), compare output to source to spot gross information loss.

**Fixtures include:** `hello_world.c`, `simple_math.c`, `data_structures.c`, `simple_asm.asm`, `classic_game.c` (game-loop style code).

### DOS game source (external)

Useful **source** references for non-trivial examples (clone separately if needed):

- [awesome-dos](https://github.com/balintkissdev/awesome-dos) — Wolf3D, Doom, Keen, etc.
- [DOS-Progs](https://github.com/Panda381/DOS-Progs) — assorted DOS sources
- [Gist list](https://gist.github.com/lucasw/af65aa7314886764e650ccf561ee6291) — open DOS games

## Supported analysis (this repo)

| Tool | Status | Purpose |
|------|--------|---------|
| **Ghidra (interactive)** | **ReVa** MCP server (separate install) | Decompilation, xrefs, etc. in the IDE |
| **Ghidra (headless)** | This repo: `analyze_binary(..., ['ghidra'])` | Scripts under `ghidra_scripts/` |
| **radare2** | Not integrated | — |
| **Binwalk** | Not integrated | — |
| **strings / PE** | Used | Via `BinaryAnalyzer` |
| **IDA Pro** | Not used | Ghidra is the supported free path for this project |

## Legal

- Analyze only binaries you are entitled to analyze.
- Intended for research, security, education, and interoperability.
- **Directmedia note:** DKI payloads may embed copyrighted text; do not redistribute book content with tooling.
- Not legal advice; consult counsel for your jurisdiction.

## Installation

- [uv](https://docs.astral.sh/uv/) recommended; Python 3.12+ for the MCP package.
- Webapp: Node.js 18+; optional Ghidra for headless/interactive workflows.

**Run MCP via uv:**

```bash
uvx reversing-mcp
```

**Claude Desktop** (example):

```json
"mcpServers": {
  "reversing-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/reversing-mcp", "run", "reversing-mcp"]
  }
}
```

**Full clone:**

```bash
git clone https://github.com/sandraschi/reversing-mcp.git
cd reversing-mcp
pip install -r requirements-dev.txt
cd reversing-webapp
npm install
cd ..
.\start-webapp.ps1
```

## Usage

- **Web:** `http://localhost:10751` (API `http://localhost:10750`).
- **MCP only:** `python -m src.reversing_mcp.server`
- **Tests:** `pytest` from repo root (see `tests/` for scope).

**MCP tools (this server only):** e.g. `analyze_binary`, `extract_strings`, `get_hexdump`, `analyze_entropy`, `decompress_directmedia_library`, `digibib_research_snapshot`, LLM list/load/status. **Ghidra decompilation / xrefs** are **ReVa’s** tools on a **separate** MCP server — not registered by reversing-mcp.

## Development status

**Working:** static analysis stack, webapp, MCP surface, heuristic DKI helpers, docs for Digibib5 reverse ([DIGIBIB_DECOMPILE_PLAN.md](docs/DIGIBIB_DECOMPILE_PLAN.md)).

**Planned:** spec-driven `text.dki` decode once EXE analysis is done; more providers/fixtures as needed.

## Acknowledgments

Contributors and upstream projects including **ReVa**, **Ghidra**, **FastMCP**, and **Directmedia Publishing** (historical publisher of the Digitale Bibliothek line). See licenses in respective repositories.

### Third-party

- [ReVa](https://github.com/cyberkaida/reverse-engineering-assistant) — Ghidra MCP
- [Ghidra](https://ghidra-sre.org/) — Apache 2.0
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP framework
