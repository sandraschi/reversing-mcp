# Reversing MCP — User Guide

## Installation

### Prerequisites

Python 3.12+ and uv from https://docs.astral.sh/uv/ are required. Optional reverse engineering tools include Ghidra from ghidra-sre.org, radare2 via winget install radare.radare2, binwalk via pip install binwalk, and IDA Pro via commercial purchase.

### Install Steps

Clone the repository with git clone https://github.com/sandraschi/reversing-mcp.git, then cd reversing-mcp and run uv sync to create the virtual environment and install all dependencies. Verify the server starts with uv run python -m reversing_mcp --stdio which should output Starting ReversingMCP v0.4.0 followed by Running in STDIO mode. For optional tool integration, install Ghidra and set GHIDRA_HOME environment variable to the extraction directory, install radare2 with winget, and install binwalk with pip. The file command for Unix can be installed via Git for Windows or WSL on Windows. Configure Claude Desktop by adding the server definition to claude_desktop_config.json with the command uv, args ["run", "--directory", "D:\\Dev\\repos\\reversing-mcp", "python", "-m", "reversing_mcp"], and environment variables PYTHONPATH, PYTHONUNBUFFERED, MCP_TRANSPORT.

### Running with HTTP

For web applications and REST clients, start with uv run python -m reversing_mcp --http --port 10750. The MCP endpoint becomes available at http://127.0.0.1:10750/mcp and the health check at http://127.0.0.1:10750/health. The HTTP mode supports FastMCP streamable HTTP transport with SSE-like streaming of responses. This mode is required for web dashboard integration and remote access scenarios.

## Step-by-Step Tutorials

### Tutorial 1: Initial Tool Discovery

Start any analysis session by checking which reverse engineering tools are available. Call check_tools() and inspect the tools dict for availability flags. Each tool entry has an available boolean, version string if detected, and path to the executable. The summary section shows total vs available counts with recommendations. If Ghidra shows available false, verify GHIDRA_HOME is set correctly by checking the environment variable exists and points to a directory containing ghidraRun.bat. If radare2 shows false, run r2 -v in a terminal to confirm it is on PATH. The notes section provides contextual guidance for Ghidra MCP integration and Directmedia setup. The directmedia entry is always available since it is built into the server.

### Tutorial 2: Basic Binary Analysis with Multiple Tools

Run a full analysis on an unknown binary using all available tools. Call analyze_binary with file_path pointing to your target. The default tool set includes static analysis (file info, strings, basic detection), file command (Unix magic-based type detection), string extraction (printable strings at minimum length 4), and binwalk (filesystem signature scanning). Review the results dict which is keyed by tool name. The static results include file metadata and detected type. The strings results list every printable string found with its offset if manual extraction was used. The binwalk results list filesystem signatures embedded in the binary if any were found. Use this as a triage step to determine if deeper Ghidra analysis is warranted.

### Tutorial 3: String Extraction for IOC Discovery

Extract strings from a suspicious binary to find indicators of compromise such as URLs, IP addresses, registry keys, file paths, and command strings. Call extract_strings with min_length set to 8 to reduce noise from short fragments. Filter the results programmatically: look for strings containing http, https, www, .com, cmd, powershell, reg, HKEY, Run, and other IOC patterns. Long strings over 50 characters often contain embedded configuration data, error messages, or debug output. Strings on even byte offsets with utf-16le encoding suggest Windows Unicode strings. Latin-1 encoding captures binary data that might contain important byte sequences.

### Tutorial 4: Hex Dump for Header Inspection

View raw bytes at the start of a file to identify its format by magic bytes. PE executables start with 4d 5a (MZ DOS header). ELF binaries start with 7f 45 4c 46. PDF files start with 25 50 44 46. ZIP archives start with 50 4b. Use get_hexdump with offset 0 and length 64 to see the initial header. For PE files, the DOS header spans the first 64 bytes and the PE signature is at the offset stored in bytes 60-63. Use a second call get_hexdump with the PE offset from the first dump to view the PE signature and machine type.

### Tutorial 5: Entropy Analysis for Packer Detection

Identify packed or encrypted executables using Shannon entropy analysis. Clean compiled code typically has overall entropy between 4.5 and 6.5. Packers like UPX, Themida, and VMProtect create high-entropy sections often above 7.5. Call analyze_entropy with block_size 256 for fine granularity. Inspect the random_regions list which contains blocks with entropy above 7.5. If any section of significant size shows entropy above 7.5, the binary is likely packed or encrypted. Inspect entropy_map for gradual transitions which may indicate section boundaries. Compare with known-unpacked versions of the same binary when available. Use compressed_regions (entropy below 3.0) to find zero-filled padding, embedded compressed data, or resource sections.

### Tutorial 6: Function Discovery with radare2

Locate functions in a binary using radare2 automatic analysis. Call find_functions with tool set to r2 or auto. radare2 runs an analysis pass with -A flag then lists all functions with the afl command. The returned functions list includes address, size in bytes, name, and source tool. Function names range from automatically detected entry points like entry0 and main to library imports. Sort by address to understand code layout and identify the program entry point (typically at the lowest address). Sort by size to find the largest functions which are often main or complex processing routines.

### Tutorial 7: PE File Analysis

Examine Windows PE file headers to understand the binary structure. Call analyze_pe_file with the path to an executable or DLL. The pe_info dict contains valid_pe boolean confirming the signature, machine string identifying the target architecture (AMD64 for 64-bit, Intel 386 for 32-bit), num_sections for layout understanding, and dos_stub_size for the legacy DOS stub. Standard compiled binaries have 3-5 sections: .text (code), .rdata (read-only data), .data (read-write data), .pdata (exception handling), .rsrc (resources). Unusual section names, section counts above 10, or sections with executable+writeable permissions indicate packing or manual section manipulation.

### Tutorial 8: File Metadata Inspection

Get quick file metadata before committing to deeper analysis. Call get_file_info for immediate type detection, size, and permissions. Use the type field to decide which analysis tools to apply: PE executables (.exe, .dll) get PE analysis, firmware images (.bin) get entropy and binwalk analysis, Directmedia files (.dki) get DKI decode. File size helps estimate analysis time: files under 5 MB are suitable for full multi-tool analysis, files above 50 MB should use targeted analysis with specific tools. Check readable and writable flags to confirm file access permissions.

### Tutorial 9: Malware Triage Workflow

Execute a complete malware triage workflow. Step 1 calls check_tools to verify tool readiness. Step 2 calls get_file_info for basic identification. Step 3 calls extract_strings with min_length 8, then filters results for IOC patterns including URLs starting with http, IP addresses matching dotted quad patterns, registry key paths starting with HKEY or HKLM, file paths with .exe, .dll, or .sys extensions, and PowerShell or cmd command strings. Step 4 calls analyze_entropy to check for packing. Step 5 calls analyze_binary with tools set to static, strings, binwalk to get the full picture. If Ghidra is available and the binary appears unpacked, proceed to analyze_binary with ghidra tool for function-level analysis.

### Tutorial 10: Firmware Analysis Workflow

Analyze a firmware binary for embedded filesystems and configuration data. Step 1 calls get_hexdump at offset 0 with length 1024 to examine the firmware header for magic bytes, version fields, and size fields. Step 2 calls analyze_entropy with block_size 1024 to find compressed regions (entropy below 3.0 indicating compressed filesystems like squashfs) and random regions (entropy above 7.5 indicating encrypted sections). Step 3 calls extract_strings with min_length 6 and filters for filesystem markers: squashfs, jffs2, ubifs, cramfs, mkfs. Step 4 calls analyze_binary with tools set to binwalk for filesystem signature scanning. Step 5 uses the entropy_map offsets as hints for targeted hex dumps at specific firmware section boundaries.

### Tutorial 11: Directmedia .DKI File Decoding

Decode a single .DKI volume from the Digitale Bibliothek. First locate the library path containing DB volume directories. Call decode_dki_file with the path to a volume's Data/TEXT.DKI file. If successful, review the strategy_used to understand which decompression approach worked. The text_preview shows the first 8000 characters to confirm correct decoding. Check the attempts list to see which strategies were tried and which produced plausible text. If all strategies fail, the attempts list provides diagnostic information for extending the decoder with additional compression formats like LZX or Huffman.

### Tutorial 12: Directmedia Extraction with Sidecar Output

Extract text from a .DKI file with full written output. Call analyze_directmedia_file which performs the same decoding but also writes a *_extracted.txt sidecar file in the same directory as the source .DKI. The sidecar file contains a header with analysis summary, file size, magic number, compression type, and offsets found, followed by all extracted text content sectioned and numbered. The tool response includes a sample_content preview and the output_file path for direct access.

### Tutorial 13: Batch Library Decompression

Process multiple volumes in a Digitale Bibliothek library simultaneously. Set the DIGITALE_BIBLIOTHEK_ROOT environment variable to the parent directory containing DB folders, or pass library_path directly. Optionally filter by volume name with volume_filter using exact name, substring match, or glob patterns like DB00*. The tool processes up to 5 volumes per call for safety. Each volume's TEXT.DKI is decoded independently. Results show per-volume progress and total text extracted across all volumes.

### Tutorial 14: Digibib5 Research Snapshot

Generate a comprehensive static analysis report for Digibib5.exe before beginning interactive Ghidra decompilation. Call digibib_research_snapshot to get file metadata, PE summary, entropy overview, and keyword-filtered strings focused on Directmedia compression functions. The keyword list includes DKI, Directmedia, Huffman, Decompress, Unpack, inflate, deflate, zlib, LZ, CreateFile, ReadFile, MapViewOfFile, lzx, mspack. Review the directmedia_string_hits for hits at specific offsets. The next_steps section provides actionable analysis guidance. The viewer_roadmap shows the milestone plan for building a modern DKI content viewer.

### Tutorial 15: Ghidra Workflow Integration

Combine reversing-mcp static analysis with ReVa MCP interactive decompilation. Start with reversing-mcp for the static prelude: check_tools to verify Ghidra availability, analyze_binary with static and strings tools for a quick overview, and digibib_research_snapshot for Directmedia-specific analysis. Then switch to ReVa MCP connected in the same MCP client for interactive Ghidra decompilation: ghidra_open to load the binary, ghidra_list_functions for function discovery, ghidra_decompile for C-like decompilation output, and ghidra_xrefs for cross-reference tracking. Return to reversing-mcp for entropy validation of specific sections identified during Ghidra analysis.

## Complete API Reference

analyze_binary parameters: file_path string required, tools list of strings optional defaulting to static file strings binwalk. Returns file_path, file_size, tools_used, results dict. extract_strings parameters: file_path string required, min_length integer optional default 4, encodings list of strings optional default ascii utf-8 utf-16le latin-1. Returns list of dicts with offset, string, encoding, length. get_hexdump parameters: file_path string required, offset integer optional default 0, length integer optional default 256. Returns file_path, offset, length, hexdump string. analyze_entropy parameters: file_path string required, block_size integer optional default 256. Returns overall_entropy float, entropy_map list, compressed_regions list, random_regions list. find_functions parameters: file_path string required, tool string optional default auto. Returns file_path, tool_used, functions list. get_file_info parameters: file_path string required. Returns path, size, modified, type, permissions, readable, writable, executable. analyze_pe_file parameters: file_path string required. Returns pe_info dict with valid_pe, machine, num_sections, dos_stub_size. decode_dki_file parameters: file_path string required. Returns success, strategy_used, encoding_guess, uncompressed_bytes, text_preview, attempts list. analyze_directmedia_file parameters: file_path string required. Returns analysis dict, extraction_summary, sample_content, output_file, extraction_status. decompress_directmedia_library parameters: library_path string optional, volume_filter string optional. Returns volumes_processed, total_text_extracted, results list.

## Troubleshooting

### 1. File not found errors
Cause: The specified path does not exist or is not readable. Fix: Verify with os.path.exists before calling tools. Use absolute paths. Avoid spaces in paths or quote them properly with double backslashes on Windows.

### 2. Ghidra not found
Cause: Ghidra is not installed or GHIDRA_HOME is not set. Fix: Download from ghidra-sre.org, extract to a stable non-temp directory, set GHIDRA_HOME. Verify {GHIDRA_HOME}/ghidraRun.bat exists. The server caches tool detection results for the session.

### 3. Ghidra headless times out
Cause: Large binaries or complex analysis. Fix: The default timeout is 900 seconds (15 minutes). Use analyze_binary with targeted tools for initial triage instead. Adjust Ghidra's analyzeHeadless.bat timeout settings via the -analysisTimeoutPerFile parameter.

### 4. radare2 analysis fails
Cause: r2 not installed or not on PATH. Fix: Install with winget install radare.radare2, verify with r2 -v. r2 must be accessible in the system PATH for the server's subprocess calls.

### 5. binwalk returns no signatures
Cause: File contains no known filesystem signatures. Fix: Use entropy analysis to find potential hidden data regions, then hex dump those regions for manual inspection. Some filesystems use custom signatures not in binwalk's database.

### 6. DKI decode fails for all strategies
Cause: The .DKI file uses a compression algorithm not supported by the built-in decoder. Fix: Use Procmon to capture the Digibib5.exe file read operations on the DKI file. Analyze the decompression code path in Ghidra/ReVa. Extend directmedia_dki.py with the discovered algorithm. Common unsupported formats include LZX, custom Huffman trees, and RC4-encrypted streams.

### 7. Digibib5.exe not located
Cause: The executable is not installed or not in the expected search path. Fix: Copy Digibib5.exe from the installed Digitale Bibliothek 5 directory to tests/fixtures/exe files/Digibib5.exe, or pass the explicit exe_path parameter. The tool returns all paths searched in the paths_searched list.

### 8. Batch decompression finds zero volumes
Cause: The library path does not contain DBxxxx subdirectories. Fix: Set DIGITALE_BIBLIOTHEK_ROOT to the parent directory containing DB folders. Verify the directory listing shows folders named DB001, DB002, etc. On Windows, check that the drive letter is correct and accessible.

### 9. File command not available
Cause: The Unix file command is not installed on Windows by default. Fix: Install via Git for Windows, Cygwin, or WSL. The server falls back to extension-based detection: .exe maps to PE executable, .dll to PE DLL, .dki to Directmedia database file.

### 10. String extraction returns empty
Cause: Binary has non-printable content or the minimum length is too high. Fix: Reduce min_length to 4. Try explicit encodings parameter with latin-1 which never fails decoding. Use entropy analysis first to confirm the data is not encrypted.

## FAQ

### 1. What is the difference between reversing-mcp and ReVa MCP?
reversing-mcp focuses on static binary analysis including strings, hex dump, entropy, file info, PE headers, and Directmedia DKI decoding. ReVa MCP provides interactive Ghidra decompilation with function-level analysis, cross-references, and decompiler output. They are complementary and designed to be used together in the same MCP client.

### 2. Does reversing-mcp include IDA Pro integration?
IDA Pro is detected by check_tools when installed, but full IDA scripting automation requires custom IDC or Python scripts that are not included. The server marks IDA as available but does not provide out-of-box IDA automation. Use Ghidra headless or radare2 for automated analysis.

### 3. Can I add custom analysis tools?
Yes, extend BinaryAnalyzer class in analyzers.py by adding a _check_X and _analyze_with_X method following the existing patterns. Then register a new @mcp.tool() in server.py.

### 4. What file formats are supported?
All binary file formats: PE (.exe, .dll), ELF, Mach-O, raw binaries (.bin), firmware images, Directmedia .DKI/.DKA, and any file readable as bytes.

### 5. Can I analyze network share files?
Yes, if the OS user has access permissions. Use UNC paths like \\server\share\file.exe or mapped drive letters.

### 6. How are Ghidra results stored?
Ghidra headless creates a temporary project in the system temp directory, runs analysis, saves JSON to the current directory, then deletes the project. The JSON is returned in the response and the temp file is cleaned up.

### 7. What is the .DKI format?
.DKI files are compressed archives used by Digitale Bibliothek 5 to store book text. They typically use zlib compression with short headers. The built-in decoder tries multiple strategies.

### 8. How do I configure the Digitale Bibliothek path?
Set DIGITALE_BIBLIOTHEK_ROOT env var to the parent directory containing DB subdirectories, or pass library_path directly.

### 9. What does entropy analysis tell me?
Entropy measures data randomness. Values 7.5+ indicate encryption or packing. Values 3.0 or lower indicate compression or repetitive data. Normal code ranges 4.5-6.5.

### 10. Can this run headlessly?
Yes, HTTP mode with --http --port 10750 enables headless/remote operation without a GUI.

### 11. Does it support batch processing?
Yes, decompress_directmedia_library processes multiple DB volumes. analyze_binary dispatches multiple tools per call.

### 12. How to update?
git pull from the repo directory, then uv sync to update dependencies.

### 13. What if no tools are installed?
The server operates with built-in string extraction, hex dump, entropy, file info, PE parsing, and DKI decoding. No external tools required.

### 14. How to analyze packed malware?
Use entropy analysis to confirm packing, extract strings for IOCs outside the packed section, examine the unpacking stub with PE analysis, then use Ghidra for interactive unpacking.

### 15. Is there a web dashboard?
The FastAPI ASGI app serves /health and mounts /mcp for MCP communication. A web dashboard can be built against these endpoints.

## Configuration Deep Dive

### Environment Variable Setup

The GHIDRA_HOME environment variable is critical for Ghidra headless analysis integration. Set it to the directory containing the ghidraRun.bat or ghidraRun script, not to the support subdirectory. For example, C:\ghidra\ghidra_12.0_PUBLIC rather than C:\ghidra\ghidra_12.0_PUBLIC\support. The server scans this directory for the ghidraRun.bat entry point. When set correctly, analyzeHeadless.bat is found at {GHIDRA_HOME}\support\analyzeHeadless.bat.

The DIGITALE_BIBLIOTHEK_ROOT variable should point to the parent directory where DB volume directories (DB001, DB002, etc.) are stored. This is typically the Digitale Bibliothek installation directory containing the Volume Management System. The server searches this directory for subdirectories starting with DB when processing Directmedia libraries.

The MCP_TRANSPORT variable can be set to http for persistent HTTP mode without CLI arguments. When set to sse, the server runs in SSE mode but emits a deprecation warning. The MCP_PORT variable overrides the default port 10750 for HTTP and SSE modes. Multiple instances can run on different ports for parallel analysis workloads.

## Advanced Ghidra Scripting

### Custom Ghidra Analysis Scripts

The ghidra_scripts directory in the repository contains the default analysis scripts used by the Ghidra headless integration. The analyze_binary.py script enumerates functions, their addresses, sizes, and calling conventions, saving results to a JSON file. The decompile_function.py script decompiles a specific function by address or name and saves the decompiled C-like output. Custom scripts can be added to this directory and referenced by the analyze_binary tool via the script_path parameter in the BinaryAnalyzer class.

### Ghidra Script API

Ghidra scripts have access to the full Ghidra API including the FlatProgramAPI for common operations, currentProgram for the program database, currentAddress for the cursor position, and the DecompInterface for decompiler access. The analyze_binary.py script uses currentProgram.getFunctionManager().getFunctions(true) to iterate all functions. The decompile_function.py script uses DecompInterface to decompile a specific Function object and retrieve the decompiled C code as text.

### Headless Analysis Limitations

Ghidra headless mode has several limitations compared to GUI mode. The auto-analysis may produce different results depending on the analysis options selected. Some plugins and extensions are not available in headless mode. The -noanalysis flag must be used with -postScript to prevent the pre-analysis stall bug in Ghidra 11.x. The analysis is triggered inside the script when needed. The temporary project is deleted after analysis completes, so no project data persists between calls.

## Troubleshooting Advanced Issues

### Ghidra analyzeHeadless.bat Not Found

If Ghidra is detected but analyzeHeadless.bat is not found at the expected path, check that the GHIDRA_HOME points to the root Ghidra installation directory. The expected structure is {GHIDRA_HOME}\support\analyzeHeadless.bat. If the file exists but is not found, check filesystem permissions on the Ghidra directory. The server logs the exact path it searches at DEBUG log level.

### Ghidra Analysis Script Failure

If the Ghidra analysis script fails, check the Ghidra version compatibility. The built-in scripts are tested with Ghidra 11.x and 12.x. Older versions may have API differences. The stderr output from the headless subprocess is included in the error response for debugging. Test the script manually with analyzeHeadless.bat from a command prompt to isolate script issues from MCP server issues.

### Large File Processing

Files over 100 MB may cause memory issues with Ghidra headless analysis. Increase the Java heap size in the Ghidra launcher configuration file (ghidraRun.bat or support/launch.properties). The -Xmx parameter controls maximum heap size. Set -Xmx8G or higher for large binaries. The server subprocess timeout of 900 seconds should be sufficient for most files, but extremely large or complex binaries may require manual analysis.

### Binary Format Not Recognized

If the file command does not recognize a binary format, the server falls back to extension-based detection. For raw firmware images without standard extensions, use get_hexdump to inspect the header bytes and analyze_entropy to characterize the data. Compare magic bytes against known format signatures to identify the binary type for manual analysis.

## Advanced Usage Patterns

### Pattern 1: Automated Malware Triage Pipeline

Build a script that processes all files in a suspicious directory with a standard triage pipeline. For each file, call get_file_info for identification and size assessment, then analyze_entropy for packer detection, then extract_strings for IOC discovery. If the entropy is above 7.0, flag the file as potentially packed. Collect all IOCs across files into a consolidated report with file paths, suspicious strings, entropy values, and detection flags.

### Pattern 2: Firmware Diff Analysis

Compare two versions of a firmware binary to identify changes. Take hex dumps at known offset ranges from both versions and compare byte-by-byte. Run entropy analysis on both to see if compression regions changed. Extract strings from both and diff the string lists to identify added or removed features, error messages, or debug output. Use find_functions if the binary exposes identifiable function prologues.

### Pattern 3: Batch Directmedia Library Import

Process an entire Digitale Bibliothek library for text extraction. First call decompress_directmedia_library with a broad volume_filter to inventory all volumes. Then iterate through each volume calling analyze_directmedia_file for full text extraction with sidecar files. Finally review the sample_content fields to identify volumes of interest for deeper analysis. The extracted text files can be loaded into document analysis tools or search engines.

### Pattern 4: Ghidra Script Development

Use the Digibib5 research snapshot to inform Ghidra script development. The directmedia_string_hits provide specific offset locations and string patterns to search for in Ghidra. The entropy analysis shows which sections contain compressed data. The PE summary provides the binary structure. Use these findings to write Ghidra scripts that trace DKI file read paths, identify decompression function calls, and document the file format structure for the viewer roadmap milestones.

### Pattern 5: Cross-Reference Validation

Validate findings from one tool against another. If binwalk detects a filesystem signature at offset X, use get_hexdump at offset X-16 to X+16 to examine the surrounding bytes for filesystem metadata like size and version fields. If a string suggests a function name, use find_functions to check if a function with that name exists. If entropy shows a high-entropy region, cross-reference with binwalk to see if it overlaps with any known signature. This cross-validation improves confidence in analysis results.

### Pattern 6: Incremental Deepening

Start with cheap operations and escalate only when needed. Begin with get_file_info for basic identification, which takes milliseconds. If the file appears to be a known format, use targeted tools instead of full analysis. If the type is unknown or suspicious, escalate to analyze_entropy for a quick packer check. Only if entropy suggests packing or encrypted content, proceed to full multi-tool analysis with analyze_binary. Reserve Ghidra headless analysis for binaries that warrant the time investment.


## Comprehensive Reference Tables

### Tool Summary Table

The following table summarizes all MCP tools, their operation discriminators, required parameters, and return value formats. Each portmanteau tool uses the operation parameter to select the sub-operation. System tools have no operation parameter and provide server-level functionality. The tool count and surface area can be queried via the capabilities endpoint.

### Parameter Type Reference

All tools use Pydantic v2 models with strict type validation. String parameters are validated as Python str types. Integer parameters use Python int with optional range constraints specified by Field ge and le arguments. Float parameters use Python float with ge and gt constraints for lower bounds. Literal types restrict values to a fixed set of string options defined in the operation parameter. Boolean parameters accept true and false values. Optional parameters have default values specified in the function signature. Required parameters have no default value and must be provided by the caller.

### Response Format Standard

All portmanteau tools return ToolResult objects wrapping a content dictionary. The content dictionary always includes a success boolean key indicating operation outcome. On success, additional keys provide the requested data. On failure, an error string key provides a human-readable description of the failure. HTTP-streamable transport wraps responses in the FastMCP 3.2 streamable HTTP protocol format. STDIO transport uses JSON-RPC 2.0 message format with the result field containing the tool output.

### Error Handling Patterns

Tools follow consistent error handling patterns. File not found errors include the attempted path in the error message. Permission errors include the path and the specific permission that was denied. Subprocess timeout errors include the tool name and timeout duration. Internal errors include the exception type and message for debugging. Unexpected errors include the full exception traceback in server logs while returning a sanitized message to the caller.

### Rate Limiting and Resource Protection

The server implements several resource protection mechanisms. Ghidra headless analysis is limited to 900 seconds maximum execution time. Directmedia batch processing is limited to 5 volumes per call to prevent excessive memory usage. File operations validate that the target file exists before reading to prevent confusing error messages. Subprocess calls use configurable timeouts to prevent hanging on unresponsive tools.

### Cross-Platform Compatibility

The server is tested on Windows 11 and Windows 10. File path handling uses pathlib.Path for cross-platform compatibility. Subprocess tool detection handles both Windows (.bat) and Unix (shell script) Ghidra launcher conventions. The file command detection falls back to extension-based type detection when the Unix file command is not available on Windows. Serial port paths differ between Windows (COM1) and Unix (/dev/ttyS0) platforms.

### Performance Optimization Tips

For optimal performance, use targeted tool selection rather than the full default tool set. Set min_length to 8 or higher for string extraction to reduce noise. Use larger block sizes like 1024 for entropy analysis of large files to reduce processing time. Prefer radare2 over Ghidra for quick function discovery. Use Ghidra headless only when decompiler output or detailed analysis is required. Batch Directmedia operations by calling decompress_directmedia_library rather than individual decode_dki_file calls for each volume.

### Extending Server Capabilities

The server architecture supports extension through multiple mechanisms. New analysis tools can be added by implementing the analysis logic in a new function and registering it with @mcp.tool() in server.py. New backends can be added to the BinaryAnalyzer class by implementing _check_X and _analyze_with_X methods. The existing help tool can be extended with new topics and detail levels. The Digibib research module can be extended with additional keyword patterns and analysis heuristics.

### Testing and Validation

Test the server functionality with the test suite using uv run pytest tests/ from the repo root. Tests cover tool availability detection, file analysis operations, error handling, and Directmedia operations. Add new tests when extending server capabilities. Run the test suite before deploying updates to ensure backward compatibility.

### Version Compatibility Matrix

Server version 0.4.0 is compatible with FastMCP 2.14.4 through 3.2.x. Python 3.10 through 3.13 are supported. The server manifest declares manifest_version 0.2 for MCPB bundle compatibility. The ASGI application requires FastAPI 0.100+ and uvicorn 0.20+ for HTTP deployment.

### Logging and Monitoring Reference

The server uses Python's standard logging framework with the logger name hierarchy based on module paths. The root logger is set to INFO level by default. Module-specific loggers include reversing_mcp for server operations and reversing_mcp.analyzers for analysis tool dispatch. Configure the log level via the --log-level CLI argument or LOG_LEVEL environment variable. Common log levels are DEBUG for detailed diagnostics, INFO for normal operations, WARNING for recoverable issues, and ERROR for operation failures.

### Security Best Practices

Run the server with minimal required permissions. The server process user only needs read access to the files being analyzed. Ghidra headless analysis requires write access to a temporary directory for project creation. Directmedia batch operations require write access to the library directory for sidecar file creation. Do not run the server as Administrator or root unless necessary. Restrict network access to the HTTP endpoint when deployed in shared environments.
