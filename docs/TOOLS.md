# Tools — reversing-mcp (15)

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

## Directmedia / DKI (Digibib5 mission)

| Tool | One line |
|------|----------|
| `decode_dki_file(path)` | Decode report, no sidecars |
| `analyze_directmedia_file(path)` | Decode + `*_extracted.txt` |
| `decompress_directmedia_library(library_path?, volume_filter?)` | Batch `DB*/Data/TEXT.DKI` |
| `digibib_research_snapshot(exe_path?)` | Static JSON bundle + roadmap |

## System

| Tool | One line |
|------|----------|
| `check_tools()` | Engine inventory incl. REA (never crashes) |
| `shutdown(confirm=True)` | Graceful termination (DESTRUCTIVE) |
| `show_tools_card()` | Engine inventory as in-chat Prefab card |

## Gym (cloning runs — `docs/GYM_SPEC.md`)

| Tool | One line |
|------|----------|
| `gym(operation, run_id?, target?, test_files?, notes?, decision?)` | Run lifecycle: start/status/advance/stop/list (stages 0/1/4 in G1) |
| `help(level?, topic?)` | Leveled docs (basic/intermediate/advanced) |
