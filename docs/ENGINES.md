# Engines - what reversing-mcp wraps

One page per engine. Status is what the code does today, not what is planned. Live install
state: Status page **Toolbox** card (reads `GET /api/v1/toolbox`) with one-click
Install buttons, or the `toolbox(operation="probe")` MCP tool. The backend
autodiscovers everything on boot (PATH, env, `D:\Dev\tools`, standard paths),
exports what it finds into its own environment, and autostarts policy services
(ReVa headless by default) — no hand-editing env, no manual installs. Running
IDA instances are glommed onto; licensing is never checked.

## Built-in static (free, always on)

Pure Python in `analyzers.py`: `file`-style typing, string extraction
(ascii/utf-8/utf-16le), Shannon entropy per block (packed > 7.5, text < 5),
PE section/import parsing. Needs nothing installed. Guide: [TOOLS.md](TOOLS.md).

## Ghidra (free)

The NSA's open-source disassembler + decompiler: machine code back to readable
C-like pseudocode with full cross-references. Wired headless (`analyzeHeadless`
batch jobs) and interactive (ReVa MCP bridge on `:8089`: decompile, xrefs,
rename). Guide: [GHIDRA.md](GHIDRA.md), [REVA.md](REVA.md).

## IDR (free, probe only)

Interactive Delphi Reconstructor: recovers Delphi forms, VMT names, RTTI that
Ghidra sees as blobs (`FUN_00xxxxxx` becomes `TTextReader.ReadLn`). Manual GUI,
not an API; `/api/v1/digibib/check-idr` probes the install. Mandatory for the
Digibib5 mission. Guide: [IDR.md](IDR.md).

## REA / rea-agents (free, MIT)

Agent-native sidecar for targets Ghidra fumbles: JS/Electron, .NET, APKs,
firmware, websites, plus native via provider (Hopper/Ghidra/IDA). Separate
server (`npx rea-agents`); `rea_investigate` shells out with truncation.
Guide: [REA.md](REA.md).

## radare2 (free, unverified on this host)

Scriptable command-line analysis framework: `r2 -A -q -c i` for info,
`afl` for functions; default backend of `find_functions` auto mode. Fast,
no JVM, no project DB. Guide: [RADARE2.md](RADARE2.md).

## binwalk (free, unverified on this host)

Embedded-content scanner: finds compressed streams, filesystems, images hiding
inside containers (relevant to `.DKI` volumes). Only the signature scan
(`binwalk -J`) is wired; extraction (`-e`) is not. Watch the v2/v3 `-J`
split. Guide: [BINWALK.md](BINWALK.md).

## IDA Pro / Home (EUR 365+/yr, never run against a real install)

Commercial reference decompiler (Hex-Rays). Headless `idat -A -S<script>`;
finds 8.x/9.x installs, gloms onto running instances (licensing never
checked). IDA Free has no IDAPython/headless and is not wired.
Guide: [IDA.md](IDA.md).

## Hopper (~USD 100, macOS/Linux only)

Indie Apple-platform disassembler with fast pseudo-code. No Windows build:
reachable only as an REA provider name here. Do not buy for Windows-only
setups. Guide: [HOPPER.md](HOPPER.md).

## Detect It Easy (free, verified DiE 3.21)

Compiler/linker/packer/protector ID in under a second (`diec -j`). The first
question before disassembly; its packed flag gates static-vs-dynamic strategy.
Gym triage runs it on every run. Guide: [DIE.md](DIE.md).

## capa (free, verified 9.4.0, slow)

Mandiant capability detection: ~1,000 rules → what the binary can do, with
ATT&CK/MBC ids. Behaviour map for cloning; 42 min on Digibib5 (96 rules,
anti-VM flags that matter for the clicker plan). Ranked rows only, never raw
JSON. Guide: [CAPA.md](CAPA.md).

## Frida (free, verified 17.23.3)

Dynamic instrumentation: inject JS into a live process, hook exports, dump
buffers. Shows what runs (vs static what-could-run); feeds Gym stage 2 oracle
capture. Spawns/attaches → `confirm=True`, VM-or-trusted only.
Guide: [FRIDA.md](FRIDA.md).

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
