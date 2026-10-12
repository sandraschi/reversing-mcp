# Engines - what reversing-mcp wraps

One page per engine. Status is what the code does today, not what is planned. Live install
state: webapp **Help -> Engines** tab (reads `GET /tools/status`), or the `check_tools()` MCP tool.

| Engine | Kind | Cost | How it is wired | Status | Guide |
|--------|------|------|-----------------|--------|-------|
| **Built-in static** | file / strings / entropy / PE | free | pure Python in `analyzers.py` | Implemented, always on | [TOOLS.md](TOOLS.md) |
| **Ghidra** | disassembler + decompiler | free | headless `analyzeHeadless` + ReVa MCP bridge (`:8089`) | Implemented | [GHIDRA.md](GHIDRA.md), [REVA.md](REVA.md) |
| **IDR** | Delphi decompiler | free | manual GUI; `/api/v1/digibib/check-idr` probes the install | Probe only | [IDR.md](IDR.md) |
| **REA** (rea-agents) | agent RE sidecar (JS/.NET/APK/native) | free (MIT) | `rea_investigate` -> `npx rea-agents` | Implemented | [REA.md](REA.md) |
| **radare2** | disassembler | free | subprocess `r2 -A -q -c <cmd>` | Implemented, unverified on this host | [RADARE2.md](RADARE2.md) |
| **binwalk** | firmware / embedded-file scan | free | subprocess `binwalk -J` | Implemented, unverified on this host | [BINWALK.md](BINWALK.md) |
| **IDA Pro / Home** | disassembler + decompiler | EUR 365+/yr | headless `ida64.exe -A -S<script>` | Implemented, never run against a real install | [IDA.md](IDA.md) |
| **IDA Free** | disassembler (GUI) | free | not wired - no IDAPython / headless | Not supported | [IDA.md](IDA.md#edition-comparison-2026-pricing) |
| **Hopper** | disassembler + decompiler | ~USD 100 | only as an REA provider (`provider="hopper"`) | macOS/Linux only - not on Windows | [HOPPER.md](HOPPER.md) |
| **Detect It Easy** | compiler / packer ID | free | `engine(operation="die")` -> `diec -j` | Implemented, verified | [DIE.md](DIE.md) |
| **capa** | capability detection (ATT&CK / MBC) | free | `engine(operation="capa")` -> `capa -j` + rules/sigs | Implemented, verified (slow: ~42 min on Digibib5) | [CAPA.md](CAPA.md) |
| **Frida** | dynamic instrumentation | free | `engine(operation="frida_trace"\|"frida_script")`, Python binding | Implemented, verified | [FRIDA.md](FRIDA.md) |

"Unverified on this host" means the code path exists but the tool is not installed on the
development machine (Goliath), so the command line and output parsing have not been checked
against a real run. See the per-engine page for the specific doubts.

## Picking an engine

| You want | Use |
|----------|-----|
| First look at an unknown binary | Built-in static (`analyze_binary`, `extract_strings`, `analyze_entropy`, `analyze_pe_file`) + DiE |
| What can this code do (file, network, crypto, anti-VM) | capa |
| Decompiled C for a native PE | Ghidra (free) or IDA Pro/Home (paid) |
| Delphi forms, event handlers, VMT names | IDR, then Ghidra |
| Electron app, .NET assembly, APK | REA |
| Embedded files / compressed blobs inside a container | binwalk |
| What the program does at runtime (file reads, decrypted buffers) | Frida |
