---
name: reversing-mcp
description: Agent-driven static binary analysis, Directmedia format reversing, and REA sidecar delegation (20 tools).
---

# Reversing MCP Skill

Agent-driven static binary analysis, Directmedia format reversing, and REA sidecar
delegation. 20 tools. Triage first (`check_tools`, `analyze_binary`), then go targeted.
Pair with ReVa (separate MCP server) for interactive Ghidra decompilation.

## Tool Categories

### Binary analysis (no Ghidra needed)

- `analyze_binary(file_path, tools?)` — multi-tool run: static, strings, entropy, PE,
  plus ida/ghidra/r2/binwalk when installed. Default tools if omitted.
- `extract_strings(file_path, min_length?, encodings?)` — ascii, utf-8, utf-16le,
  latin-1. Grep output for DKI, .dki, expand, decompress, ReadFile, CreateFile.
- `get_hexdump(file_path, offset?, length?)` — raw bytes at offset (default 256 B).
- `analyze_entropy(file_path, block_size?)` — > 7.5 suggests packed/encrypted; < 5 is text/code.
- `find_functions(file_path, tool?)` — radare2 / headless Ghidra / auto.
- `get_file_info(file_path)` — size, type, permissions.
- `analyze_pe_file(file_path)` — sections, imports, DOS stub size.

### Agent RE (REA sidecar)

- `rea_investigate(target?, kind?, provider?, query?, symbol?, address?, snapshot_path?, timeout_s?)` —
  JS/Electron app graphs, .NET/APK/firmware/browser targets, agent-driven native
  pseudocode/search/xrefs via Hopper/Ghidra/IDA. `kind="auto"` routes dirs/`.asar` to JS,
  files to native overview. Outputs over 512 KB truncate with a snapshot hint.
  Guide: docs/REA.md. Setup: `just setup-rea`.

### Directmedia / DKI (Digibib5 mission)

- `decode_dki_file(path)` — decode report (strategy, preview, attempts), no sidecars.
- `analyze_directmedia_file(path)` — decode + write `*_extracted.txt` beside the file.
- `decompress_directmedia_library(library_path?, volume_filter?)` — batch DB*/Data/TEXT.DKI.
- `digibib_research_snapshot(exe_path?)` — static JSON bundle (keyword strings, entropy,
  PE summary, next_steps, viewer_roadmap). Auto-finds fixture or Program Files path.
- Heuristic zlib/gzip only: `text.dki` on large volumes is usually header + offset table +
  packed stream — follow docs/DIGIBIB_DECOMPILE_PLAN.md (Ghidra/ReVa) before promising
  a decoder. `tree.dki` is often plain CP1252.

### System & Lifecycle

- `check_tools()` — engine inventory incl. REA sidecar (version, path, node). Never crashes.
- `shutdown(confirm=True)` — graceful termination. `show_tools_card()` — engine badges in-chat.
- `gym(operation=...)` — cloning runs: start/status/advance/stop/list (stages 0/1/4 in G1).
- `reva(operation=...)` — ReVa bridge lifecycle (status, start headless/GUI, stop).
- `toolbox(operation=...)` — toolchain inventory probe, package installation, and policies.
- `engine(operation=...)` — die (compiler/packer), capa (capabilities, slow), frida_trace/frida_script (runtime hooks, confirm=True, VM or trusted targets only).
- `help(level?, topic?)` — leveled docs.

**Ghidra interactive is a separate server (ReVa).** This server has no decompile/xref tools.
Workflows: strings → xrefs → decompile → rename live in ReVa; headless via
`analyze_binary(..., ['ghidra'])` when Ghidra is installed (`GHIDRA_INSTALL_DIR`).

## Best practices / methodology

1. `check_tools()` first, `analyze_binary()` second, targeted tools third.
2. String → xref → decompile: filter strings, xrefs_to, function at xref, decompile, repeat.
3. High-entropy regions: decompressor code usually sits near the code handling them.
4. Every result ends with the next concrete tool call (address, function, query).
5. Dynamic probes (Frida, debugger) via docs/DIRECTMEDIA_REVERSING_TOOLKIT.md and
   scripts/directmedia/ — never invent offsets or injectors.
6. Never claim full DKI coverage; never present truncated REA output as complete.

## Configuration requirements

- Env: `GHIDRA_INSTALL_DIR` (headless Ghidra), `DIGITALE_BIBLIOTHEK_ROOT` (DB* parent),
  `OLLAMA_BASE_URL` (chat/LLM, default localhost:11434), `GHIDRA_BRIDGE_URL` (webapp bridge
  proxy, default 127.0.0.1:8089), `REA_*` (sidecar tuning, see docs/REA.md).
- External: Ollama for Chat/LLM webapp features; Node 22.19+ for REA sidecar;
  ReVa + Ghidra/IDA/Hopper for deep native work.
- Legal: entitled targets only (security research, education, interoperability,
  format recovery). Commercial EULAs may forbid analysis — check first.
