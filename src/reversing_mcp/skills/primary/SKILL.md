# Reversing MCP Skill

Static binary analysis and Directmedia format reversing MCP server with 13 tools.

## Tool Categories

### Binary Analysis
- `analyze_binary` — multi-tool analysis (Ghidra headless, radare2, binwalk, strings, PE)
- `extract_strings` — ASCII/Unicode string extraction with encoding options
- `get_hexdump` — hex dump at byte offset with configurable length
- `analyze_entropy` — Shannon entropy per block; detects packed/encrypted sections
- `find_functions` — function discovery via radare2 or headless Ghidra

### File Analysis
- `get_file_info` — file metadata (type, size, permissions)
- `analyze_pe_file` — Windows PE structure (sections, imports, exports)

### Directmedia
- `decode_dki_file` — single .DKI decompress with auto-detection (zlib/gzip)
- `analyze_directmedia_file` — full .DKI analysis with text extraction
- `decompress_directmedia_library` — batch all volumes in a library

### System
- `check_tools` — availability of Ghidra, radare2, binwalk, file, strings
- `digibib_research_snapshot` — DigiBib5 static research prelude
- `shutdown` — graceful server termination (requires confirm=True)

## Best Practices
1. Start with `check_tools()` to verify available RE tools
2. Use `analyze_binary()` for initial triage, then targeted tools
3. Pair with ReVa MCP (separate server) for interactive Ghidra decompilation
