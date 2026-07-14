# Reversing MCP — System Documentation

## Overview

Reversing MCP is a FastMCP server for static binary analysis and Directmedia (Digitale Bibliothek) reverse engineering. It wraps Ghidra headless analysis, radare2, binwalk, GNU strings, and custom heuristic decompression for the .DKI format used by the Digital Library 5 (Digibib5) viewer. The server works alongside the ReVa (reverse-engineering-assistant) MCP server which provides interactive Ghidra decompilation. This server focuses on fast static analysis without requiring a Ghidra GUI.

## Architecture Overview

The server has three layers: Transport layer (transport.py) provides unified STDIO/HTTP/SSE runner with CLI args and env var config. The Analysis layer (analyzers.py) contains the BinaryAnalyzer class wrapping IDA Pro, Ghidra headless via analyzeHeadless.bat, radare2, binwalk, GNU strings, and manual Python-based analysis including string extraction, hex dump, Shannon entropy calculation, and PE header parsing. The Directmedia layer provides built-in heuristic .DKI decoder using zlib/gzip autodetection with header skip, offset scanning, and raw deflate attempts. The Digibib research module produces structured snapshots for agents and humans before interactive decompilation work.

### Deployment Modes

Three transport modes are supported. STDIO mode is the default for Claude Desktop, run via python -m reversing_mcp --stdio. HTTP streamable mode serves web apps and REST clients via python -m reversing_mcp --http --port 10750 with the MCP endpoint at /mcp and a health endpoint at /health on the FastAPI ASGI app mounted at reversing_mcp.server:app. SSE mode is a deprecated legacy mode that still functions but emits a deprecation warning at startup. The ASGI app can also be served with uvicorn reversing_mcp.server:app for production deployment behind a reverse proxy.

## Tools

### analyze_binary

Purpose: Analyze a binary file with multiple reverse engineering tools in one call. The tool orchestrates tool dispatch automatically based on availability and requested tool list.

Parameters: file_path (str, required) is the path to the binary file to analyze. tools (list[str] | None, optional) is a list of tool names to apply; supported values are ida, ghidra, r2, binwalk, static, file, strings, file_info. If None, defaults to the full set of available tools: static, file, strings, binwalk. The static pseudo-tool bundles file_info, strings, and basic detection together.

Return Format: Returns a dict with file_path (the absolute path to the analyzed file), file_size (integer bytes), tools_used (list of tool names that were actually dispatched), and results (dict keyed by tool name containing that tool's analysis output). The results sub-dict has tool-specific structure; file_info returns path, size, type, permissions, and access flags; file returns the file command type string; strings returns a list of extracted string objects with offset, string, encoding, and length fields; binwalk returns either parsed JSON signatures or raw text output; ghidra returns function lists and analysis results from Ghidra headless.

Errors: Returns {"error": "File not found: /path"} if file_path does not exist. Returns {"error": "Analysis failed: <exception message>"} on internal failure such as file read errors, subprocess timeouts, or encoding issues.

### extract_strings

Purpose: Extract printable strings from a binary file using GNU strings when available, falling back to manual byte-by-byte extraction for each requested encoding. Useful for finding embedded URLs, error messages, configuration strings, and indicators of compromise.

Parameters: file_path (str, required) is the path to the binary file. min_length (int, optional, default 4) sets the minimum string length to include in results; higher values reduce noise by filtering short fragments. encodings (list[str] | None, optional) specifies which encodings to try; default is ["ascii", "utf-8", "utf-16le", "latin-1"] with first successful encoding used and the rest skipped.

Return Format: Returns a list of dicts, each containing offset (integer byte offset in file), string (the extracted text), encoding (the encoding that produced this string), and length (character count). When GNU strings is available, offset is set to 0 because the strings command does not provide offset information in its default output.

Errors: Returns [{"error": "File not found: /path"}] if the file does not exist. Returns [{"error": "String extraction failed: <message>"}] on subprocess error or file read failure. Unicode decode errors are silently handled by trying the next encoding.

### get_hexdump

Purpose: Get a hexadecimal dump of a binary file range. Useful for manual inspection of file headers, embedded structures, and signature bytes. Output is formatted as space-separated hex bytes, 16 bytes per line.

Parameters: file_path (str, required) is the path to the binary file. offset (int, optional, default 0) is the starting offset in bytes. length (int, optional, default 256) is the number of bytes to read and format. Maximum practical length is limited by file size and memory.

Return Format: Returns a dict with file_path, offset, length, and hexdump (string with hexadecimal representation, one line per 16 bytes with spaces between byte values). The output can be parsed by splitting on newlines and then on spaces.

Errors: Returns {"error": "File not found: /path"} if file does not exist. Returns {"error": "Hexdump failed: <message>"} on read errors.

### analyze_entropy

Purpose: Analyze Shannon entropy of a binary file to detect compressed or encrypted sections. Shannon entropy measures the randomness of data on a scale from 0.0 (perfectly predictable) to 8.0 (perfectly random). Executable code typically has entropy of 4.5 to 6.5. Values above 7.5 strongly suggest encryption or packing. Values below 3.0 suggest compression or highly repetitive data such as zero-filled regions.

Parameters: file_path (str, required) is the path to the binary file. block_size (int, optional, default 256) sets the window size for block-level entropy calculation, in bytes. Smaller block sizes provide finer granularity but more data. A block size of 512 or 1024 is good for firmware analysis; 256 is best for packed binary detection.

Return Format: Returns a dict with file_path, block_size, overall_entropy (float 0.0-8.0 for the entire file), entropy_map (list of per-block dicts with offset, entropy, and size fields), compressed_regions (list of blocks with entropy below 3.0), and random_regions (list of blocks with entropy above 7.5). The entropy_map allows plotting or sectional analysis. compressed_regions and random_regions highlight sections of interest for further investigation.

Errors: Returns {"error": "File not found: /path"} if missing. Returns {"error": "Entropy analysis failed: <message>"} on read errors.

### find_functions

Purpose: Locate functions in a binary using the specified reverse engineering tool. Currently supports radare2 (r2) for auto mode and Ghidra headless when GHIDRA_HOME is configured. IDA Pro detection returns a placeholder noting that IDA scripting setup is required.

Parameters: file_path (str, required) is the path to the binary file. tool (str, optional, default "auto") selects the backend; valid values are ida, ghidra, r2, and auto. Auto mode prefers r2 if available, otherwise falls back to Ghidra.

Return Format: Returns a dict with file_path, tool_used (the resolved tool name), and functions (list of function dicts each containing address (integer), size (integer bytes), name (string), and tool (string indicating source). For r2, addresses are parsed from the radare2 afl command output hexadecimal format.

Errors: Returns {"error": "File not found: /path"} if missing. Returns [{"error": "r2 function analysis failed"}] or [{"error": "Ghidra not available"}] when the selected tool is not found.

### get_file_info

Purpose: Get basic file system metadata and type information. Uses the file command when available, with extension-based fallback detection.

Parameters: file_path (str, required) is the path to the file to analyze. No other parameters.

Return Format: Returns a dict with path (absolute path), size (integer bytes), modified (Unix timestamp float), type (string from file command or extension-based detection), permissions (Unix permission string), readable (boolean), writable (boolean), executable (boolean). For PE files (.exe, .dll), also includes pe_info sub-dict with PE header details.

Errors: Returns {"error": "File not found: /path"} if the path does not exist.

### check_tools

Purpose: Check which reverse engineering tools are available on the system by scanning standard installation paths and PATH. Returns availability, version, and path for each tool.

Parameters: None.

Return Format: Returns a dict with tools (dict keyed by tool name: ida, ghidra, r2, binwalk, strings, file, directmedia each with name, available bool, version string, path string, and optional description), summary (total tools found, available count, recommended list, premium list), and notes (contextual guidance for Ghidra MCP integration, Directmedia setup, and Digibib5 research).

Errors: Returns {"error": "Tool check failed: <message>"} on unexpected error.

### digibib_research_snapshot

Purpose: Static research bundle for Digibib5.exe or Directmedia viewer reverse engineering. Produces a structured snapshot with file metadata, PE summary, entropy analysis, and keyword-filtered strings focused on decompression and DKI-related patterns. Designed to be the first step before interactive Ghidra/ReVa decompilation.

Parameters: exe_path (str | None, optional) is an optional absolute path to Digibib5.exe. If omitted, the tool searches tests/fixtures/exe files/Digibib5.exe in the repo and then C:\Program Files (x86)\Digitale Bibliothek 5\Digibib5.exe.

Return Format: Returns a dict with success boolean, exe_path (resolved path), file_info (size, type, pe_summary with valid_pe, machine, num_sections), directmedia_string_hits (list of string objects with offset, string, encoding, length, and keyword_hit for strings matching DKI, decompress, zlib, LZ, Huffman, ReadFile, CreateFile, MapViewOfFile, and other Directmedia-related keywords), directmedia_string_hits_total count, total_strings_sampled count, entropy (overall float, random_region_count, compressed_region_count), tools (ghidra_headless_available bool, ghidra_hint path), next_steps (actionable list of recommended analysis steps), and viewer_roadmap (milestone plan for building a modern DKI viewer).

Errors: Returns {"success": false, "error": "Digibib5.exe not found", "paths_searched": [list], "hint": "..."} when the executable cannot be located. Returns {"success": false, "error": "Snapshot failed: <message>", "exe_path": "..."} on analysis errors.

### analyze_pe_file

Purpose: Analyze a Windows PE (Portable Executable) file by reading its DOS header, PE signature, machine type, and section count. Supports both 32-bit and 64-bit PE files.

Parameters: file_path (str, required) is the path to the PE file.

Return Format: Returns a dict with file_path and pe_info sub-dict containing valid_pe (boolean), machine (human-readable architecture name such as AMD64, Intel 386, or Intel Itanium), num_sections (integer), and dos_stub_size (integer bytes between DOS header and PE header).

Errors: Returns {"error": "File not found: /path"} or {"error": "File too small for PE"} for files under 64 bytes. Returns {"error": "Not a valid PE file (missing MZ signature)"} for non-PE files. Returns {"error": "Invalid PE header"} if the PE signature is missing.

### decode_dki_file

Purpose: Decompress a Directmedia .DKI file using built-in zlib/gzip autodetection. Returns a detailed decode report without writing any sidecar files. Tries multiple decompression strategies including zlib of whole file, gzip of whole file, zlib after skipping header bytes (4, 8, 12, 16, 20, 24, 32, 40, 48, 64), raw deflate with skips, and offset-based zlib stream scanning.

Parameters: file_path (str, required) is the path to a .DKI file, typically Data/TEXT.DKI inside a DB volume directory.

Return Format: Returns a dict with success boolean, file_path, strategy_used (string naming the successful decompression strategy), encoding_guess (detected text encoding), uncompressed_bytes (integer), text_preview (first 8000 characters of decoded text), and attempts (list of all strategies tried with strategy name, ok boolean, and optional detail string). If all strategies fail, the attempts list provides diagnostic information for extending the decoder.

Errors: Returns {"success": false, "error": "File not found: /path"} for missing files. Returns {"success": false, "error": "DKI decode failed: no zlib/gzip payload matched text heuristics. If this volume uses another codec, capture a TEXT.DKI sample and extend directmedia_dki.py.", "attempts": [...]} when no decompression strategy produces plausible text.

### analyze_directmedia_file

Purpose: Analyze a Directmedia .DKI file and extract text content to a sidecar file. Writes *_extracted.txt next to the .DKI on success with full extraction report and all decoded text sections.

Parameters: file_path (str, required) is the path to the .DKI file to analyze and extract.

Return Format: Returns a dict with file_path, analysis (file_size, magic_number as hex string, compression_type name, offsets_found count), extraction_summary (sections_processed count, total_text_bytes), sample_content (list of up to 6 text excerpts from decoded records for preview), output_file (path to the written sidecar text file), and extraction_status string.

Errors: Returns {"error": "File not found: /path"} or {"error": "DKI decode failed", "file_path": "...", "extraction_status": "failed"} when decompression fails.

### decompress_directmedia_library

Purpose: Batch decompress all Directmedia volumes in a library directory containing DBxxx subdirectories. Scans for TEXT.DKI in each volume's Data folder. Limited to processing the first 5 volumes per call for safety.

Parameters: library_path (str | None, optional) is the path to the Directmedia library root directory containing DB folder hierarchy. If omitted, uses DIGITALE_BIBLIOTHEK_ROOT env var, then L:\Multimedia Files\Written Word\Digitale Bibliothek. volume_filter (str | None, optional) filters by volume name using simple substring match or glob pattern with wildcards.

Return Format: Returns a dict with library_path (resolved path), volumes_processed (integer), total_volumes_found (integer), total_text_extracted (integer bytes across all processed volumes), results (list of per-volume dicts with volume name, file_path, sections_extracted, text_bytes, and optional error), and batch_status string.

Errors: Returns {"error": "Directmedia decoder unavailable"} if the built-in decoder is not available. Returns {"error": "Digitale Bibliothek library directory not found", "paths_searched": [...], "hint": "Set DIGITALE_BIBLIOTHEK_ROOT or pass library_path to your DB* parent folder."} when the library root cannot be resolved.

### help

Purpose: Get comprehensive help information about Reversing MCP tools and capabilities at three detail levels. Supports topic filtering for focused documentation.

Parameters: level (str, optional, default "basic") selects detail level: basic for essential getting-started content, intermediate for detailed tool descriptions and workflows, advanced for technical architecture, Ghidra deep-dive, competitive analysis, and expert references. topic (str | None, optional) filters to specific areas: ghidra, binary, analysis. Topic filtering is only available at certain levels.

Return Format: Returns a structured dict with level, description, and content sections depending on level and topic. Basic returns essential tools list and quick start steps. Intermediate returns tool categories with per-tool descriptions and multi-step analysis workflows for malware analysis and firmware research. Advanced returns architecture documentation, Ghidra expertise with background, technical capabilities, competitive advantages versus IDA Pro, Binary Ninja, radare2, expert workflows, troubleshooting, performance tuning, and references to official and community resources.

Errors: Invalid level values silently default to basic.

### API Endpoints

The server exposes a FastAPI ASGI app at reversing_mcp.server:app with two routes: GET /health returns {"status": "ok"} and the /mcp mount point serves the FastMCP HTTP streamable endpoint for REST-based MCP communication. The ASGI app is conditionally defined when FastAPI is importable, making it optional for STDIO-only deployments.

## Configuration

### Environment Variables

MCP_TRANSPORT controls the transport mode: stdio (default for Claude Desktop), http (for web apps and REST clients), or sse (deprecated). MCP_HOST sets the bind address for HTTP/SSE modes, defaulting to 127.0.0.1. MCP_PORT sets the listen port, defaulting to 10750 per the fleet port registry. MCP_PATH sets the HTTP endpoint path, defaulting to /mcp. GHIDRA_HOME or GHIDRA_INSTALL_DIR points to the Ghidra installation directory for headless analysis via analyzeHeadless.bat. DIGITALE_BIBLIOTHEK_ROOT points to the Digitale Bibliothek library root containing DB volume directories. PYTHONPATH should include the src directory. PYTHONUNBUFFERED should be set to 1.

### Tool Discovery

Tool detection scans standard installation paths automatically. IDA Pro is searched at C:\Program Files\IDA Pro 8.{3,2,1}\ida.exe and C:\Program Files (x86)\IDA Pro\ida.exe. Ghidra is searched via GHIDRA_HOME or GHIDRA_INSTALL_DIR env vars, then common roots C:\ghidra, D:\ghidra, C:\Program Files, D:\Dev, plus Unix paths /usr/local/ghidra and /opt/ghidra. The scanner prefers stable install paths over temp directories. radare2 is found by running r2 -v. binwalk is found by running binwalk --version. GNU strings and file command are found on PATH.

### Ghidra Headless Analysis

Ghidra integration uses analyzeHeadless.bat found in the Ghidra installation at support/analyzeHeadless.bat. It creates a temporary project, imports the target file, optionally runs auto-analysis via the -postScript flag with a custom ghidra_scripts/analyze_binary.py script, then deletes the project. The script outputs a JSON file with analysis results including function list and decompilation output. Results are parsed and returned in the tool response, with the temporary JSON file cleaned up after reading. Timeout is set to 900 seconds for large binaries.

## Security Model

File access is restricted to files the OS user has permission to read. Subprocess calls use bounded timeouts from 5 seconds for simple checks to 900 seconds for Ghidra headless analysis. No remote code execution surface exists; all analysis runs locally on the server. Directmedia batch processing is limited to 5 volumes per call to prevent runaway resource consumption. Temporary Ghidra projects are created in the OS temp directory and reliably deleted after analysis completes.

## Data Storage

No persistent database is used; the server is stateless. Extracted Directmedia text files are written alongside the source .DKI files on the filesystem. Temporary Ghidra projects use the system temp directory and are cleaned up after each analysis. Digibib research snapshots are computed fresh on each call with no caching.

## Rate Limiting

No built-in rate limiting. The server is designed for local single-user use. Subprocess calls have individual timeouts but no aggregate throttling.

## Logging

The server uses Python logging with a configurable log level set via the --log-level CLI argument. Default level is INFO. The log format includes timestamp, module name, severity level, and message. The logger name follows the module hierarchy (reversing_mcp, reversing_mcp.analyzers). All subprocess errors, file read errors, and analysis exceptions are logged at ERROR level. Debug logging can be enabled with --debug or --log-level DEBUG.

## Version Information

Current server version is 0.4.0. The manifest declares manifest_version 0.2. The Python __init__.py reports version 0.1.0 for the package. Compatibility is maintained with FastMCP 2.14.4+ and Python 3.10+.

## Detailed Tool Parameter Tables

### analyze_binary Parameter Details

The file_path parameter must be an absolute or relative path to a file that exists on the server filesystem. The tools parameter is a list of string values that select which analysis backends to invoke. Each tool name maps to a specific analysis engine: static runs file_info extraction and type detection, file runs the Unix file command for magic-based type identification, strings runs GNU strings or manual string extraction, binwalk runs the binwalk embedded filesystem scanner, r2 runs radare2 analysis, ghidra runs Ghidra headless analysis, ida runs placeholder IDA Pro detection. When tools is None, the default set is static, file, strings, binwalk. Each tool that is not available or not requested is simply omitted from the results dict; no error is raised for missing tools. The results dict keys correspond exactly to the tools that were successfully dispatched.

### extract_strings Parameter Details

The file_path must point to an existing readable file. The min_length parameter controls the minimum character length for included strings; higher values reduce false positives from short byte sequences that happen to be printable ASCII. The encodings parameter lists character encodings to attempt in order. For each encoding, the server reads the file and decodes it using the specified encoding with error replacement for non-decodable bytes. Consecutive printable characters above the minimum length threshold are collected as strings. The first encoding that produces any results is used and subsequent encodings are skipped to avoid duplicates. When GNU strings is available on the PATH, it is preferred because it is significantly faster for large files and handles a wider range of binary formats.

### get_hexdump Parameter Details

The offset must be a non-negative integer less than the file size. The length must be a positive integer; requesting more bytes than remain in the file from the offset returns only the available bytes. The output format presents 16 bytes per line separated by single spaces. Each line represents one row of a traditional hex dump display. Leading zeros are preserved for single-digit hex values to maintain consistent column alignment. The output can be parsed programmatically by splitting on newlines and then splitting each line on spaces to get individual byte values.

### analyze_entropy Parameter Details

The file_path must point to an existing file. The block_size determines the granularity of the entropy analysis. Smaller block sizes provide more detailed maps but increase the number of data points. Block sizes below 64 bytes may produce noisy results because entropy requires a minimum sample size for statistical significance. The Shannon entropy calculation counts the frequency of each byte value (0-255) in the block, computes the probability of each value, and sums the negative log2 of each probability. The overall_entropy applies the same calculation to the entire file. The compressed_regions threshold of 3.0 and random_regions threshold of 7.5 are heuristics based on empirical analysis of real-world binaries.

### find_functions Parameter Details

The file_path must exist and be a binary format. The tool parameter selects which analysis engine to use for function discovery. Auto mode first checks for radare2 because it is typically faster for function detection. If radare2 is not available or fails, auto mode does not fall back to Ghidra automatically; the caller should retry with tool explicitly set to ghidra. The r2 tool runs r2 with the -A flag for automatic analysis followed by the afl command to list functions. Each function entry includes the address parsed as hexadecimal, size parsed as hexadecimal, and name from the remaining text. The ghidra tool runs analyzeHeadless.bat with a custom Ghidra script that enumerates functions from the program database.

### get_file_info Parameter Details

The file_path must point to an existing filesystem entry. The function attempts to stat the file using os.stat to retrieve size, modification time, and permissions. The type field uses the file command when available on the system PATH, falling back to extension-based mapping that recognizes .exe, .dll, .dki, and .dka extensions. For files with .exe or .dll extensions, additional PE header parsing is attempted and included as the pe_info sub-dict when successful.

## Performance Characteristics

### Analysis Speed

The analyze_binary tool dispatches tools sequentially, with each tool adding to the total response time. File info and string extraction complete in sub-second time for files under 100 MB. Binwalk analysis takes 1-30 seconds depending on file size and number of embedded signatures. radare2 analysis with automatic analysis takes 5-60 seconds for typical binaries. Ghidra headless analysis is the slowest at 30 seconds to 15 minutes depending on file size and analysis complexity. For rapid triage, use targeted tool selection rather than the full default set.

### Memory Usage

String extraction loads the entire file into memory. For files over 500 MB, consider using extract_strings with targeted encodings and higher min_length values. Entropy analysis processes the file in configurable blocks and has constant memory overhead. Ghidra headless analysis creates temporary project files on disk using JVM heap space configurable via the Ghidra launcher settings.

## Deployment Modes

### STDIO Mode (Default)

The STDIO mode uses standard input and output for JSON-RPC message exchange. This mode is required for Claude Desktop integration and works with any MCP client that supports subprocess-based servers. The server process runs as a child of the MCP client and terminates when the client disconnects. Logging output goes to stderr to avoid interfering with the JSON-RPC protocol on stdout.

### HTTP Streamable Mode

HTTP mode uses FastMCP's streamable HTTP transport which implements the MCP HTTP specification with SSE-like streaming for tool responses. This mode is suitable for web applications, REST API clients, and multi-user scenarios. The server runs as a standalone process bound to the configured host and port. The ASGI application supports uvicorn for production deployment with optional TLS termination via reverse proxy.

## Security Architecture

### Local File Access

All file analysis tools operate on the local filesystem with the permissions of the server process user. Files on network shares, removable media, and cloud-synced directories are accessible if the OS user has read permissions. The server does not implement file path sandboxing or access control lists. Restrict access to the server process to trusted users.

### Subprocess Execution

Tools that invoke external processes (Ghidra, radare2, binwalk, strings, file) do so through Python's subprocess module with configured timeouts. Long-running subprocesses are terminated at timeout. The Ghidra headless subprocess timeout is set to 900 seconds to accommodate large binary analysis. Subprocess stdout and stderr are captured to prevent interference with the MCP protocol.

## Environment Variable Reference

The MCP_TRANSPORT variable accepts values stdio, http, and sse to select the transport mode at startup without CLI arguments. The MCP_HOST, MCP_PORT, and MCP_PATH variables configure the HTTP/SSE server binding. The GHIDRA_HOME variable should point to the Ghidra installation root directory containing ghidraRun.bat or ghidraRun. The GHIDRA_INSTALL_DIR is an alternative variable name for the same purpose. The DIGITALE_BIBLIOTHEK_ROOT variable points to the parent directory containing DB volume subdirectories for Directmedia operations. The LOG_LEVEL variable sets the Python logging level to DEBUG, INFO, WARNING, or ERROR.
