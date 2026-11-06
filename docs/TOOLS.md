# Tools - reversing-mcp (27)

Full signatures live in `llms-full.txt`. Every tool returns a `message` key.

## Static triage (no engine needed)

| Tool | One line |
|------|----------|
| `analyze_binary(file_path, tools?)` | Multi-tool run (static/strings/entropy/PE + ida/ghidra/r2/binwalk when installed) |
| `extract_strings(file_path, min_length?, encodings?)` | ascii/utf-8/utf-16le/latin-1 string dump |
| `get_hexdump(file_path, offset?, length?)` | Raw bytes at offset |
| `analyze_entropy(file_path, block_size?)` | >7.5 packed/encrypted, <5 text/code |
| `find_functions(file_path, tool?)` | radare2 / headless Ghidra / auto |
| `get_file_info(file_path)` | Size, type, permissions |
| `analyze_pe_file(file_path)` | Sections, imports, DOS stub |

## Agent RE (REA sidecar)

| Tool | One line |
|------|----------|
| `rea_investigate(target?, kind?, provider?, query?, symbol?, address?, snapshot_path?, timeout_s?)` | JS/Electron graphs, .NET/APK/firmware/browser, native pseudocode/search/xrefs. `auto` routes dirs→JS, files→native. See `docs/REA.md` |

## Ghidra (ReVa forwarding + community extensions)

| Tool | One line |
|------|----------|
| `ghidra(operation, tool?, arguments?, ...)` | Status/start/stop/tools/describe/call via stdio `mcp-reva` child (headless or watch). See `docs/GHIDRA.md`, `docs/REVA.md` |
| `ghidra_extensions(operation, name?, version?, confirm?)` | Community extension download + CRUD: catalog/list/install/remove/enable/disable in the user Extensions dir. SNES/65816-first. See `docs/GHIDRA_EXTENSIONS.md` |

## Directmedia / DKI (Digibib5 mission)

| Tool | One line |
|------|----------|
| `decode_dki_file(path)` | Decode report, no sidecars |
| `analyze_directmedia_file(path)` | Decode + `*_extracted.txt` |
| `decompress_directmedia_library(library_path?, volume_filter?)` | Batch `DB*/Data/TEXT.DKI` |
| `digibib_research_snapshot(exe_path?)` | Static JSON bundle + roadmap |

## Hardware (Hercules DJ Console MK1)

| Tool | One line |
|------|----------|
| `hercules_hw_info()` | Physical/USB/control descriptors (VID `0x06F8`, PID `0xB100`) |
| `hercules_virtual_spin(deck, ticks)` / `hercules_virtual_fader(fader, value)` / `hercules_virtual_button(button, pressed)` | Synthesize 16-byte HID reports + MIDI CC/Note translation |
| `hercules_decode_packet(packet_hex)` | Decode a raw 16-byte USB interrupt IN report |

## System

| Tool | One line |
|------|----------|
| `check_tools()` | Engine inventory incl. REA (never crashes) |
| `shutdown(confirm=True)` | Graceful termination (DESTRUCTIVE) |
| `show_tools_card()` | Engine inventory as in-chat Prefab card |

## Gym (cloning runs — `docs/GYM_SPEC.md`)

| Tool | One line |
|------|----------|
| `gym(operation, run_id?, target?, test_files?, notes?, decision?, session_id?, mode?, tour_rel?, step_cap?, time_cap_s?, confirm?, accept_local?)` | Run lifecycle: start/status/advance/stop/list (G1) + elicit/clicker_*/correlate/compare/export (ClickerLab 1b/3/§5 + determinism + map export). Clicker executes: needs confirm + accept_local |
| `engine(operation, file_path?, target?, args?, pid?, functions?, arg0_filter?, source?, duration_s?, max_events?, timeout_s?, confirm?)` | `die`: compiler/packer ID; `capa`: capabilities (slow on big binaries); `frida_trace` / `frida_script`: runtime hooks, need `confirm=True` |
| `reva(operation?, mode?, confirm?)` | ReVa lifecycle: probe/start/stop (headless `mcp-reva` or Ghidra GUI). Start needs confirm |
| `toolbox(operation?, name?)` | Toolchain autodiscovery/install/autostart: probe/install/ensure/policy. See `docs/TOOLBOX.md` |
| `help(level?, topic?)` | Leveled docs (basic/intermediate/advanced) |
