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
| **Ghidra** (ReVa forwarding) | `ghidra` (status/start/stop/tools/describe/call), `reva` (lifecycle) | [Ghidra guide](docs/GHIDRA.md) · [ReVa guide](docs/REVA.md) |
| **Toolbox** (autodiscovery/install) | `toolbox` | [Toolbox](docs/TOOLBOX.md) |
| **Directmedia / DKI** | `decode_dki_file`, `analyze_directmedia_file`, `decompress_directmedia_library`, `digibib_research_snapshot` | [Reversing guide](docs/DIGIBIB_REVERSING_GUIDE.md) · [Mission](docs/DIRECTMEDIA_MISSION.md) · [Toolkit](docs/DIRECTMEDIA_REVERSING_TOOLKIT.md) · [Decompile plan](docs/DIGIBIB_DECOMPILE_PLAN.md) |
| **System** | `check_tools`, `shutdown`, `help`, `show_tools_card` | — |

Vision: agent-driven **feature-to-code maps** (behavior + disassembly correlated) - see [PRD.md](PRD.md) and the [Tier 3 spec](docs/CUA_DISASSEMBLY_COMBO.md).

## The Twin Methods: Disassembly + CUA Clickthrough

Reversing-MCP unifies two historically separate disciplines into a synchronized reverse-engineering loop:

1. **Conventional Disassembly (White-Box)**:
   - **Engines**: Ghidra (headless PyGhidra + ReVa MCP bridge), IDA Pro, radare2, Hopper, capa, Detect It Easy (DiE), and Frida.
   - **Capabilities**: Complete structural inspection of native PE sections, function control flow graphs, decompiled C pseudocode, string references, and runtime API hooks.
   - **The Bottleneck (*Static Blindness*)**: In stripped or packed 5–50 MB binaries, static disassemblers present hundreds of thousands of unlabeled subroutines (`FUN_004012A0`), leaving analysts and LLMs with no intuitive anchor for which code implements a specific user-visible action.

2. **CUA Clickthrough & Gym Oracle Loops (Black-Box)**:
   - **Engines**: Automated Windows UI driver (pywinauto), OCR screen analysis, and accessibility element trees.
   - **Capabilities**: Systematically explores the running application through scripted or elicited workflows (*Launch -> File Open -> Search -> Export*), recording timestamped window states, OCR text, and file/registry diffs.
   - **The Bottleneck (*Dynamic Blindness*)**: Observing the UI reveals what happens externally, but remains blind to internal decompression algorithms, encryption keys, and proprietary data structures.

### The Correlation Bridge: Feature-to-Code Maps

The **ClickerLab** engine (`correlate_session`) bridges this divide. It correlates runtime OCR strings and UI interaction tokens with static string references and call-sites across the disassembled binary. The output synthesizes:
- **Ghidra Plate Comments**: Contextual labels annotating exact functions with runtime feature provenance.
- **IDA Import Scripts** (`map_import_ida.py`): Automated address renaming and tagging mapped directly to high-level UI triggers.
- **Empirical Scientific Reversing**: Equips autonomous agents with both eyes (CUA/OCR) to drive the target and hands (Ghidra/Frida/ReVa) to dissect and verify the implementation.

See [docs/CUA_DISASSEMBLY_COMBO.md](docs/CUA_DISASSEMBLY_COMBO.md) and [docs/GYM_SPEC.md](docs/GYM_SPEC.md) for full architectural specifications.

### The Reverse-to-Craft Playbook

How does reverse engineering culminate in a finished product? The [Reverse-to-Craft Playbook](docs/REVERSE_TO_CRAFT_PLAYBOOK.md) outlines the end-to-end methodology for rebuilding reversed apps into agent-native desktop applications using the pure-Rust ArtCraft architecture:
1. **Extraction (Gym Stages 0–4)**: Reverse binary, eliciting formats and CUA interaction tours.
2. **Clean-Room Specification (Stage 5)**: Author legal, unencumbered format and interaction specs.
3. **Rust Workspace Scaffolding**: Single Rust workspace (`apps/<name>-cli`, `apps/<name>-desktop`, `crates/core`, `crates/format`, `crates/mcp`).
4. **Module Harvesting**: Reuse MIT/Apache modules from `_upstream/<craft>` (FigCraft, CadCraft, PhotoCraft) for MCP servers, command palettes, viewports, and storage.
5. **Oracle Verification (Stage 8)**: Original legacy application re-opens clone's output (zero-diff proof).
6. **Central Launcher Integration**: Managed by `fleet-start.config.ps1` and `starts/<name>-start.bat`.

Read the complete guide: [docs/REVERSE_TO_CRAFT_PLAYBOOK.md](docs/REVERSE_TO_CRAFT_PLAYBOOK.md).

## Ghidra / IDA / REA integration

| Path | When | Setup |
|------|------|-------|
| **Interactive** (`ghidra` tool) | Decompile, xrefs, rename, retype via ReVa behind one portmanteau — headless `mcp-reva`, or attach to a running Ghidra GUI | [Ghidra guide](docs/GHIDRA.md) |
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
ClickerLab, a **Ghidra** section (Workbench + Tool catalogue + Call history
driving ReVa interactively), ReVa/toolbox Status, local-LLM Chat, Logs, and a
Help center whose engine guides open in-app. Port pair claimed in
`mcp-central-docs/operations/WEBAPP_PORTS.md` (BE 10750 / FE 10751).

## Preview

Screenshots pending: no browser harness on the dev host yet (Playwright +
Chromium install + capture script). Planned shots: Dashboard hero, Analyze
result, Gym run with ClickerLab session, Toolbox card. This section stays
explicit until the captures land — no stock or mock images.

## Framework Stack

- **Backend**: Python 3.12+, FastMCP 3.4+, FastAPI, Uvicorn, Pydantic v2
- **Engines & Tooling**: Ghidra (headless/ReVa), radare2, Frida, Detect It Easy (DiE), capa, REA sidecar
- **Frontend**: React 19, Vite, Tailwind CSS, Lucide icons, Biome
- **Package & Workflow**: uv, just, bun

## Legal

Analyze only binaries you are entitled to analyze. Intended for security research, education, interoperability, and format recovery.
