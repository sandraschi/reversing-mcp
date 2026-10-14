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

**Claude Desktop bundle (one-liner):**
```powershell
powershell -c "irm https://github.com/sandraschi/reversing-mcp/releases/latest/download/install.ps1 | iex"
```

## What it does

20 tools across eight domains:

| Domain | Tools | Docs |
|--------|-------|------|
| **Binary analysis** | `analyze_binary`, `extract_strings`, `get_hexdump`, `analyze_entropy`, `find_functions` | — |
| **File / PE analysis** | `get_file_info`, `analyze_pe_file` | — |
| **Agent RE** (REA sidecar) | `rea_investigate` | [REA sidecar guide](docs/REA.md) |
| **Gym** (cloning runs + ClickerLab) | `gym` (lifecycle + elicit/clicker_*/correlate) | [Gym spec](docs/GYM_SPEC.md) |
| **Engines** (DiE / capa / Frida) | `engine` | [Engines](docs/ENGINES.md) |
| **Ghidra bridge** (ReVa lifecycle) | `reva` | [ReVa guide](docs/REVA.md) |
| **Toolbox** (autodiscovery/install) | `toolbox` | [Toolbox](docs/TOOLBOX.md) |
| **Directmedia / DKI** | `decode_dki_file`, `analyze_directmedia_file`, `decompress_directmedia_library`, `digibib_research_snapshot` | [Reversing guide](docs/DIGIBIB_REVERSING_GUIDE.md) · [Mission](docs/DIRECTMEDIA_MISSION.md) · [Toolkit](docs/DIRECTMEDIA_REVERSING_TOOLKIT.md) · [Decompile plan](docs/DIGIBIB_DECOMPILE_PLAN.md) |
| **System** | `check_tools`, `shutdown`, `help`, `show_tools_card` | — |

Vision: agent-driven **feature-to-code maps** (behavior + disassembly correlated) - see [PRD.md](PRD.md) and the [Tier 3 spec](docs/CUA_DISASSEMBLY_COMBO.md).

## Ghidra / IDA / REA integration

| Path | When | Setup |
|------|------|-------|
| **Interactive** (ReVa MCP) | You want decompile, xrefs, rename in Ghidra via MCP | [ReVa MCP guide](docs/REVA.md) |
| **Agent RE** (REA sidecar) | JS/Electron, .NET, APK, firmware, browser, or agent-driven native via Hopper/Ghidra/IDA | [REA sidecar guide](docs/REA.md) |
| **Behavioral + static** (Tier 3) | CUA feature tour correlated to disassembly: feature-to-code maps (tour + capture + correlate MVP built; VM + B4 open) | [Combo spec](docs/CUA_DISASSEMBLY_COMBO.md) |
| **Headless** (`analyzeHeadless`) | Batch/script analysis from `analyze_binary` | Install Ghidra, set `GHIDRA_INSTALL_DIR` |
| **IDA Pro headless** | Higher-quality decompilation if you have IDA | [IDA integration guide](docs/IDA.md) |
| **radare2 / binwalk** | Function list, signature scan (subprocess, optional) | [radare2](docs/RADARE2.md) · [binwalk](docs/BINWALK.md) |
| **Hopper** | Only via REA, macOS/Linux only | [Hopper](docs/HOPPER.md) |
| **Frida** | Runtime hooking (verified; feeds Gym stage 2 oracle capture) | [Frida](docs/FRIDA.md) |

All engines, cost and status in one table: [docs/ENGINES.md](docs/ENGINES.md).

## Web UI

SOTA React dashboard on `http://localhost:10751` (backend `:10750`): hero with
live KPIs (tools, toolbox, runs, models), Analyze uploads, Gym runs with
ClickerLab, ReVa/toolbox Status, local-LLM Chat, Logs, and a Help center whose
engine guides open in-app. Port pair claimed in
`mcp-central-docs/operations/WEBAPP_PORTS.md` (BE 10750 / FE 10751).

## Preview

Screenshots pending: no browser harness on the dev host yet (Playwright +
Chromium install + capture script). Planned shots: Dashboard hero, Analyze
result, Gym run with ClickerLab session, Toolbox card. This section stays
explicit until the captures land — no stock or mock images.

## Legal

Analyze only binaries you are entitled to analyze. Intended for security research, education, interoperability, and format recovery.
