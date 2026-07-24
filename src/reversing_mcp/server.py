#!/usr/bin/env python3
"""
Reversing MCP Server — static binary analysis and Directmedia tools.

For interactive Ghidra analysis over MCP, run the ReVa (reverse-engineering-assistant)
server separately and connect it in your MCP client. See docs/GHIDRA.md and
CURSOR_HANDOFF.md in this repository.
"""

import os
from pathlib import Path
from typing import Any

from typing import Annotated

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .analyzers import BinaryAnalyzer
from .digibib_research import build_research_snapshot, resolve_digibib_exe
from .directmedia_dki import (
    decode_dki_path,
    legacy_extract_for_server,
    resolve_digitale_library_root,
    result_to_mcp_dict,
)
from .logging_config import get_logger
from .transport import run_server

logger = get_logger("reversing_mcp")

# Built-in .DKI decoder (zlib/gzip heuristics); no external directmedia-mcp wheel required
directmedia_available = True

# Initialize MCP server
mcp = FastMCP("ReversingMCP", version="0.4.0")

_READ_ONLY = {"readonly": True}
_MUTATING = {}
_DESTRUCTIVE = {}

SKILLS_DIR = Path(__file__).parent / "skills"


class AnalysisResult(BaseModel):
    """Result of binary analysis"""

    tool: str = Field(description="Tool used for analysis")
    file_path: str = Field(description="Path to analyzed file")
    file_size: int = Field(description="File size in bytes")
    file_type: str = Field(description="Detected file type")
    architecture: str | None = Field(description="CPU architecture if detected")
    endianness: str | None = Field(description="Endianness (little/big)")
    analysis: dict[str, Any] = Field(description="Tool-specific analysis results")


class StringResult(BaseModel):
    """String extraction result"""

    offset: int = Field(description="Offset in file")
    string: str = Field(description="Extracted string")
    encoding: str = Field(description="String encoding")
    length: int = Field(description="String length")


# Global analyzer instances
analyzer = BinaryAnalyzer()


@mcp.tool(annotations=_READ_ONLY)
async def analyze_binary(
    file_path: Annotated[str, Field(description="Path to the binary file to analyze")],
    tools: Annotated[list[str] | None, Field(description="Tools to use (ida, ghidra, r2, binwalk, static). If None, uses all available.")] = None,
) -> dict[str, Any]:
    """
    Analyze a binary file with multiple reverse engineering tools.

    ## Return Format
    {"file_path": str, "file_size": int, "tools_used": [str], "results": {tool: result}}

    ## Examples
    analyze_binary("file.exe", ["static", "strings"])
    analyze_binary("firmware.bin")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        results = analyzer.analyze_file(file_path, tools)
        return {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "tools_used": list(results.keys()),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return {"error": f"Analysis failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def extract_strings(
    file_path: Annotated[str, Field(description="Path to the binary file")],
    min_length: Annotated[int, Field(description="Minimum string length to extract")] = 4,
    encodings: Annotated[list[str] | None, Field(description="Encodings to try (ascii, utf-8, utf-16le, latin-1)")] = None,
) -> list[dict[str, Any]]:
    """
    Extract strings from a binary file.

    ## Return Format
    [{"offset": int, "string": str, "encoding": str, "length": int}]

    ## Examples
    extract_strings("file.exe", min_length=8)
    extract_strings("file.bin", encodings=["ascii", "utf-16le"])
    """
    if not os.path.exists(file_path):
        return [{"error": f"File not found: {file_path}"}]

    if encodings is None:
        encodings = ["ascii", "utf-8", "utf-16le", "latin-1"]

    try:
        strings = analyzer.extract_strings(file_path, min_length, encodings)
        return [s.model_dump() for s in strings]
    except Exception as e:
        logger.error(f"Error extracting strings from {file_path}: {e}")
        return [{"error": f"String extraction failed: {e!s}"}]


@mcp.tool(annotations=_READ_ONLY)
async def get_hexdump(
    file_path: Annotated[str, Field(description="Path to the binary file")],
    offset: Annotated[int, Field(description="Starting offset in bytes")] = 0,
    length: Annotated[int, Field(description="Number of bytes to dump")] = 256,
) -> dict[str, Any]:
    """
    Get hexadecimal dump of a binary file.

    ## Return Format
    {"file_path": str, "offset": int, "length": int, "hexdump": str}

    ## Examples
    get_hexdump("file.exe", offset=0, length=512)
    get_hexdump("firmware.bin", offset=1024)
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        hexdump = analyzer.get_hexdump(file_path, offset, length)
        return {"file_path": file_path, "offset": offset, "length": length, "hexdump": hexdump}
    except Exception as e:
        logger.error(f"Error getting hexdump for {file_path}: {e}")
        return {"error": f"Hexdump failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def analyze_entropy(
    file_path: Annotated[str, Field(description="Path to the binary file")],
    block_size: Annotated[int, Field(description="Block size for entropy calculation")] = 256,
) -> dict[str, Any]:
    """
    Analyze entropy of a binary file (detects compressed/encrypted sections).

    ## Return Format
    {"file_path": str, "block_size": int, "overall_entropy": float, "entropy_map": [...], "compressed_regions": [...], "random_regions": [...]}

    ## Examples
    analyze_entropy("file.exe")
    analyze_entropy("packed.bin", block_size=512)
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        entropy_data = analyzer.analyze_entropy(file_path, block_size)
        return {
            "file_path": file_path,
            "block_size": block_size,
            "overall_entropy": entropy_data["overall"],
            "entropy_map": entropy_data["map"],
            "compressed_regions": entropy_data["compressed"],
            "random_regions": entropy_data["random"],
        }
    except Exception as e:
        logger.error(f"Error analyzing entropy for {file_path}: {e}")
        return {"error": f"Entropy analysis failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def find_functions(
    file_path: Annotated[str, Field(description="Path to the binary file")],
    tool: Annotated[str, Field(description="Tool to use (ida, ghidra, r2, auto)")] = "auto",
) -> dict[str, Any]:
    """
    Find functions in a binary file.

    ## Return Format
    {"file_path": str, "tool_used": str, "functions": [...]}

    ## Examples
    find_functions("file.exe")
    find_functions("file.exe", tool="ghidra")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        functions = analyzer.find_functions(file_path, tool)
        return {"file_path": file_path, "tool_used": tool, "functions": functions}
    except Exception as e:
        logger.error(f"Error finding functions in {file_path}: {e}")
        return {"error": f"Function analysis failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def get_file_info(
    file_path: Annotated[str, Field(description="Path to the file to analyze")],
) -> dict[str, Any]:
    """
    Get basic information about a file.

    ## Return Format
    {"path": str, "size": int, "modified": float, "type": str, "permissions": str, "readable": bool, "writable": bool, "executable": bool}

    ## Examples
    get_file_info("file.exe")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "type": analyzer.detect_file_type(file_path),
            "permissions": oct(stat.st_mode)[-3:],
            "readable": os.access(file_path, os.R_OK),
            "writable": os.access(file_path, os.W_OK),
            "executable": os.access(file_path, os.X_OK),
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        return {"error": f"File info failed: {e!s}"}


@mcp.resource("config://tools")
def _tools_resource() -> dict[str, Any]:
    """List available RE tools as a config resource."""
    return {"tools": analyzer.check_available_tools()}


@mcp.prompt()
def reversing_help(topic: str = "overview") -> str:
    """Get reversing guidance for a specific topic."""
    topics = {
        "pe": "PE files: check DOS header at offset 0, NT headers at offset 0x3C. Use analyze_pe_file().",
        "strings": "Strings: extract_strings() with min_length=8 filters noise. Check utf-16le for wide strings.",
        "entropy": "Entropy: analyze_entropy(). Values > 7.5 suggest compression/encryption; < 5 is plain text/code.",
        "dki": "DKI decode: decode_dki_file() for single files, decompress_directmedia_library() for batch.",
    }
    return topics.get(topic, "Use check_tools() then analyze_binary() for a full overview.")


@mcp.tool(annotations=_READ_ONLY)
async def check_tools() -> dict[str, Any]:
    """
    Check which reverse engineering tools are available on the system.

    ## Return Format
    {"tools": {name: {available: bool, version: str, path: str}}, "summary": {"total": int, "available": int, "recommended": [str], "premium": [str]}, "notes": {...}}

    ## Examples
    check_tools()
    """
    try:
        available_tools = analyzer.check_available_tools()

        # Add Directmedia status
        available_tools["directmedia"] = {
            "name": "Directmedia DKI (built-in)",
            "available": directmedia_available,
            "version": "0.4",
            "description": "Heuristic zlib/gzip .DKI decode (analyze_directmedia_file, decode_dki_file)",
        }

        return {
            "tools": available_tools,
            "summary": {
                "total": len(available_tools),
                "available": len([t for t in available_tools.values() if t["available"]]),
                "recommended": ["ghidra", "r2", "binwalk"],
                "premium": ["ida"],
            },
            "notes": {
                "ghidra_mcp": (
                    "Ghidra MCP is not bundled here. Install ReVa (reverse-engineering-assistant) "
                    "and add it to your MCP client; see docs/GHIDRA.md."
                ),
                "directmedia_setup": "Install directmedia-mcp for .DKI file analysis",
                "digibib5": (
                    "Digitale Bibliothek 5: digibib_research_snapshot() for static prelude; "
                    "see docs/DIRECTMEDIA_REVERSING_TOOLKIT.md"
                ),
            },
        }
    except Exception as e:
        logger.error(f"Error checking tools: {e}")
        return {"error": f"Tool check failed: {e!s}"}


@mcp.tool()
async def digibib_research_snapshot(exe_path: str | None = None) -> dict[str, Any]:
    """
    DIGIBIB_RESEARCH_SNAPSHOT — Static research bundle for Digibib5.exe / Directmedia viewer work.

    PORTMANTEAU PATTERN RATIONALE: Single entry point for the Digitale Bibliothek 5 mission:
    file metadata, PE summary, entropy, and keyword-filtered strings (DKI, decompress, …)
    before interactive Ghidra/ReVa decompilation.

    Args:
        exe_path: Optional absolute path to Digibib5.exe. If omitted, uses repo fixture
            tests/fixtures/exe files/Digibib5.exe then the standard Program Files install path.

    Returns:
        success, exe_path, file_info, directmedia_string_hits, counts, entropy, tools,
        next_steps, viewer_roadmap; or error + paths_searched when not found.

    Examples:
        digibib_research_snapshot()
        digibib_research_snapshot("D:\\\\Dev\\\\repos\\\\reversing-mcp\\\\tests\\\\fixtures\\\\exe files\\\\Digibib5.exe")
    """
    resolved, tried = resolve_digibib_exe(exe_path)
    if resolved is None:
        return {
            "success": False,
            "error": "Digibib5.exe not found",
            "paths_searched": tried,
            "hint": "Copy Digibib5.exe into tests/fixtures/exe files/ or pass exe_path.",
        }
    try:
        return build_research_snapshot(analyzer, resolved)
    except Exception as e:
        logger.exception("digibib_research_snapshot failed")
        return {"success": False, "error": f"Snapshot failed: {e!s}", "exe_path": str(resolved)}


@mcp.tool(annotations=_READ_ONLY)
async def analyze_pe_file(
    file_path: Annotated[str, Field(description="Path to the PE file")],
) -> dict[str, Any]:
    """
    Analyze a Windows PE (Portable Executable) file.

    ## Return Format
    {"file_path": str, "pe_info": {...}}

    ## Examples
    analyze_pe_file("file.exe")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        pe_info = analyzer.analyze_pe_file(file_path)
        return {"file_path": file_path, "pe_info": pe_info}
    except Exception as e:
        logger.error(f"Error analyzing PE file {file_path}: {e}")
        return {"error": f"PE analysis failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def decode_dki_file(
    file_path: Annotated[str, Field(description="Path to a .DKI (e.g. volume Data/TEXT.DKI)")],
) -> dict[str, Any]:
    """
    DECODE_DKI_FILE — Decompress a Directmedia .DKI using built-in zlib/gzip autodetection.

    PORTMANTEAU PATTERN RATIONALE: Explicit decode report (strategy, preview, attempts) without
    also writing sidecar .txt files.

    ## Return Format
    {"success": bool, "strategy_used": str, "encoding_guess": str, "text_preview": str, "attempts": [...]} or {"success": False, "error": str}

    ## Examples
    decode_dki_file("C:/DB001/Data/TEXT.DKI")
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}
    r = decode_dki_path(Path(file_path))
    return result_to_mcp_dict(file_path, r)


@mcp.tool(annotations=_MUTATING)
async def analyze_directmedia_file(
    file_path: Annotated[str, Field(description="Path to the .DKI file to analyze")],
) -> dict[str, Any]:
    """
    Analyze a Directmedia .DKI file and extract text content.

    Uses the in-repo heuristic decoder (zlib/gzip / header skip). Writes *_extracted.txt
    next to the .DKI on success.

    ## Return Format
    {"file_path": str, "analysis": {...}, "extraction_summary": {...}, "sample_content": [str], "output_file": str, "extraction_status": str} or {"error": str}

    ## Examples
    analyze_directmedia_file("C:/DB001/Data/TEXT.DKI")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        result = legacy_extract_for_server(Path(file_path))
        if not result.get("success"):
            return {
                "error": result.get("error", "DKI decode failed"),
                "file_path": file_path,
                "extraction_status": "failed",
            }

        # Format the response for MCP
        response = {
            "file_path": file_path,
            "analysis": {
                "file_size": result["analysis"]["file_size"],
                "magic_number": f"0x{result['analysis']['magic_number']:08x}",
                "compression_type": result["analysis"]["compression_type"].name,
                "offsets_found": len(result["analysis"]["offsets"]),
            },
            "extraction_summary": {
                "sections_processed": len(result["extracted_sections"]),
                "total_text_bytes": result["total_extracted_size"],
            },
        }

        # Add sample extracted content
        if result["extracted_sections"]:
            samples = []
            for section in result["extracted_sections"][:3]:
                if section.get("records"):
                    for record in section["records"][:2]:
                        text = record.get("text_content", "")
                        if text and len(text) > 10:
                            samples.append(text[:200] + "..." if len(text) > 200 else text)

            if samples:
                response["sample_content"] = samples

        # Save extracted content to file
        output_file = Path(file_path).parent / f"{Path(file_path).stem}_extracted.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Directmedia Decompression Results for {file_path}\n")
            f.write("=" * 60 + "\n\n")
            f.write("Analysis Summary:\n")
            f.write(f"- File size: {result['analysis']['file_size']:,} bytes\n")
            f.write(f"- Magic number: 0x{result['analysis']['magic_number']:08x}\n")
            f.write(f"- Compression type: {result['analysis']['compression_type'].name}\n")
            f.write(f"- Offsets found: {len(result['analysis']['offsets'])}\n")
            f.write(f"- Sections extracted: {len(result['extracted_sections'])}\n")
            f.write(f"- Total text bytes: {result['total_extracted_size']:,}\n\n")

            # Write all extracted text
            all_text_parts = []
            for section in result["extracted_sections"]:
                if section.get("records"):
                    for record in section["records"]:
                        text = record.get("text_content", "")
                        if text and len(text) > 5:
                            all_text_parts.append(text)

            if all_text_parts:
                f.write("EXTRACTED TEXT CONTENT:\n")
                f.write("-" * 30 + "\n\n")
                for i, text in enumerate(all_text_parts, 1):
                    f.write(f"[{i}] {text}\n\n")

        response["output_file"] = str(output_file)
        response["extraction_status"] = "success"

        return response

    except Exception as e:
        logger.error(f"Error analyzing Directmedia file {file_path}: {e}")
        return {"error": f"Directmedia analysis failed: {e!s}"}


@mcp.tool(annotations=_MUTATING)
async def decompress_directmedia_library(
    library_path: Annotated[str | None, Field(description="Path to Directmedia library directory (DB* folders). If omitted, uses env DIGITALE_BIBLIOTHEK_ROOT.")] = None,
    volume_filter: Annotated[str | None, Field(description="Filter for volume names (e.g. DB002 or *philo*)")] = None,
) -> dict[str, Any]:
    """
    Batch decompress all Directmedia volumes in a library.

    ## Return Format
    {"library_path": str, "volumes_processed": int, "total_volumes_found": int, "total_text_extracted": int, "results": [...], "batch_status": str} or {"error": str}

    ## Examples
    decompress_directmedia_library()
    decompress_directmedia_library(volume_filter="DB002")
    """
    if not directmedia_available:
        return {"error": "Directmedia decoder unavailable"}

    resolved, paths_searched = resolve_digitale_library_root(library_path)
    if resolved is None:
        return {
            "error": "Digitale Bibliothek library directory not found",
            "paths_searched": paths_searched,
            "hint": "Set DIGITALE_BIBLIOTHEK_ROOT or pass library_path to your DB* parent folder.",
        }

    try:
        lib_path = resolved
        results = []

        # Find all DBxxx directories
        volume_dirs = [d for d in lib_path.iterdir() if d.is_dir() and d.name.startswith("DB")]

        if volume_filter:
            if "*" in volume_filter:
                # Simple glob matching
                import fnmatch

                volume_dirs = [d for d in volume_dirs if fnmatch.fnmatch(d.name, volume_filter)]
            else:
                volume_dirs = [d for d in volume_dirs if volume_filter in d.name]

        processed_volumes = 0
        total_text_extracted = 0

        for volume_dir in volume_dirs[:5]:  # Limit to first 5 volumes for safety
            data_dir = volume_dir / "Data"
            if not data_dir.exists():
                continue

            text_dki = data_dir / "TEXT.DKI"
            if text_dki.exists():
                try:
                    result = legacy_extract_for_server(text_dki)
                    if not result.get("success"):
                        results.append(
                            {"volume": volume_dir.name, "error": result.get("error", "decode failed")}
                        )
                        continue

                    volume_result = {
                        "volume": volume_dir.name,
                        "file_path": str(text_dki),
                        "sections_extracted": len(result["extracted_sections"]),
                        "text_bytes": result["total_extracted_size"],
                    }

                    total_text_extracted += result["total_extracted_size"]
                    processed_volumes += 1
                    results.append(volume_result)

                except Exception as e:
                    results.append({"volume": volume_dir.name, "error": str(e)})

        return {
            "library_path": str(lib_path),
            "volumes_processed": processed_volumes,
            "total_volumes_found": len(volume_dirs),
            "total_text_extracted": total_text_extracted,
            "results": results,
            "batch_status": "completed",
        }

    except Exception as e:
        logger.error(f"Error in batch Directmedia decompression: {e}")
        return {"error": f"Batch decompression failed: {e!s}"}


@mcp.tool()
async def help(level: str = "basic", topic: str | None = None) -> dict[str, Any]:
    """
    Get comprehensive help information about Reversing MCP tools and capabilities.

    Args:
        level: Help detail level ("basic", "intermediate", "advanced")
        topic: Optional specific topic to focus on

    Returns:
        Formatted help documentation
    """

    if level not in ["basic", "intermediate", "advanced"]:
        level = "basic"

    # Basic help - essential getting started
    if level == "basic":
        help_content = {
            "level": "basic",
            "description": "Essential tools and quick start guide",
            "ghidra_note": (
                "Ghidra MCP is provided by a separate server (ReVa / reverse-engineering-assistant). "
                "Add it in your MCP client; use its tools for decompilation and listings. "
                "This server covers static analysis and Directmedia."
            ),
            "quick_start": [
                "1. Check available tools: check_tools()",
                "2. Analyze a binary: analyze_binary('file.exe', ['static', 'strings'])",
                "3. Extract strings: extract_strings('file.exe', min_length=8)",
                "4. Get hex dump: get_hexdump('file.exe', offset=0, length=256)",
                "5. For Ghidra: connect ReVa MCP (see docs/GHIDRA.md)",
                "6. Digibib5 / Directmedia: digibib_research_snapshot() (see docs/DIRECTMEDIA_REVERSING_TOOLKIT.md)",
            ],
            "essential_tools": [
                "analyze_binary - Full binary analysis",
                "extract_strings - Find text in binaries",
                "get_hexdump - View raw bytes",
                "analyze_entropy - Detect compression/encryption",
                "check_tools - See what's available",
                "digibib_research_snapshot - Static bundle for Digibib5.exe / viewer roadmap",
            ],
            "next_steps": "Use level='intermediate' for detailed tool descriptions",
        }

    # Intermediate help - detailed tool descriptions
    elif level == "intermediate":
        help_content = {
            "level": "intermediate",
            "description": "Detailed tool descriptions and workflows",
            "tool_categories": {
                "binary_analysis": [
                    "analyze_binary(file_path, tools) - Analyze with multiple tools",
                    "extract_strings(file_path, min_length, encodings) - Find printable strings",
                    "get_hexdump(file_path, offset, length) - Raw byte viewer",
                    "analyze_entropy(file_path, block_size) - Detect packed/encrypted sections",
                    "find_functions(file_path, tool) - Locate functions in binaries",
                    "digibib_research_snapshot(exe_path?) - Digibib5 / Directmedia static prelude + roadmap",
                ],
                "file_info": [
                    "get_file_info(file_path) - Basic file metadata",
                    "analyze_pe_file(file_path) - Windows PE analysis",
                    "decode_dki_file(path) - Directmedia .DKI zlib/gzip decode report",
                    "file_type detection, permissions, timestamps",
                ],
                "ghidra_tools": [
                    "Use the ReVa MCP server (reverse-engineering-assistant) for Ghidra-backed tools.",
                    "Discover tools via your client's tool list or ReVa's tool_search when available.",
                ],
                "ghidra_requirements": (
                    "Install ReVa for Ghidra MCP (assistant or headless mode per Ghidra version). "
                    "See docs/GHIDRA.md and CURSOR_HANDOFF.md."
                ),
            },
            "workflows": {
                "malware_analysis": [
                    "1. check_tools() - Verify local RE tools",
                    "2. analyze_binary(file.exe, ['static', 'strings', 'ghidra']) - Static + headless Ghidra if installed",
                    "3. Use ReVa MCP for interactive decompilation and xrefs in Ghidra",
                ],
                "firmware_research": [
                    "1. get_hexdump(file.bin, 0, 1024) - Check headers",
                    "2. analyze_entropy(file.bin) - Find packed sections",
                    "3. extract_strings(file.bin) - Find embedded strings",
                    "4. binwalk analysis for embedded filesystems",
                ],
            },
            "next_steps": "Use level='advanced' for technical details and Ghidra deep-dive",
        }

    # Advanced help - technical details and Ghidra expertise
    else:  # level == "advanced"
        help_content = {
            "level": "advanced",
            "description": "Technical architecture, Ghidra deep-dive, and expert references",
            "architecture": {
                "core_components": {
                    "BinaryAnalyzer": "Multi-tool analysis orchestrator supporting IDA, Ghidra headless, radare2",
                    "Ghidra MCP": (
                        "Interactive Ghidra analysis is a separate concern: run ReVa MCP alongside this server. "
                        "analyze_binary(..., ['ghidra']) may still use headless Ghidra when installed."
                    ),
                    "Directmedia Decompressor": "Legacy .DKI format reverse engineering",
                },
                "tool_detection": {
                    "automatic_discovery": "Scans common installation paths",
                    "fallback_handling": "Graceful degradation when tools unavailable",
                    "version_detection": "Extracts version info for compatibility",
                },
            },
            "ghidra_expertise": {
                "background": {
                    "developer": "National Security Agency (NSA) - United States Government",
                    "purpose": "Professional reverse engineering and malware analysis framework",
                    "license": "Apache License 2.0 (free and open source)",
                    "first_release": "2019, evolved from IDA Pro acquisition",
                    "current_version": "Ghidra 11.x / 12.x (12.0+ for PyGhidra 3.x headless scripting)",
                },
                "technical_capabilities": {
                    "decompiler": "Industry-leading retargetable decompiler with multi-architecture support",
                    "disassembler": "Supports 90+ processor architectures and instruction sets",
                    "analysis_engine": "Auto-analysis with function detection, data flow analysis, type inference",
                    "scripting": "Java-based scripting with full API access to analysis results",
                    "collaboration": "Multi-user analysis with version control integration",
                },
                "integration_architecture": {
                    "reva_mcp": "ReVa (reverse-engineering-assistant) exposes Ghidra as MCP; connect it in your client.",
                    "headless_note": "Ghidra 12.0+: ReVa headless (`mcp-reva`). Older: assistant mode with Ghidra GUI.",
                    "companion_server": "reversing-mcp stays focused on static tools + Directmedia without GUI coupling.",
                    "see_ghidra_docs": "docs/GHIDRA.md in this repo for setup and headless options.",
                },
                "competitive_advantages": {
                    "vs_ida_pro": "Free alternative with comparable analysis quality, though steeper learning curve",
                    "vs_binary_ninja": "More comprehensive enterprise features, better collaboration tools",
                    "vs_ghidra_online": "Local deployment maintains security, no cloud dependencies",
                    "vs_radare2": "GUI-first approach with professional-grade decompiler",
                },
                "use_cases": {
                    "malware_analysis": "Signature development, behavior analysis, IOC extraction",
                    "firmware_re": "Embedded system analysis, IoT device security research",
                    "vulnerability_research": "Patch analysis, exploit development, security assessments",
                    "digital_forensics": "Evidence analysis, timeline reconstruction, artifact extraction",
                },
            },
            "references": {
                "official_resources": {
                    "homepage": "https://ghidra-sre.org/",
                    "documentation": "https://ghidra-sre.org/Help/start.html",
                    "github": "https://github.com/NationalSecurityAgency/ghidra",
                    "wiki": "https://github.com/NationalSecurityAgency/ghidra/wiki",
                    "api_docs": "https://ghidra-sre.org/Help/api/",
                },
                "community_resources": {
                    "reddit": "r/ReverseEngineering, r/Ghidra",
                    "discord": "Ghidra Discord community server",
                    "tutorials": "John Hammond, LiveOverflow, Azeria Labs Ghidra guides",
                    "books": "'The Ghidra Book' by Chris Eagle and Kara Nance",
                    "blogs": "NSA Ghidra blog, OpenSecurityResearch Ghidra posts",
                },
                "academic_citations": {
                    "papers": "IEEE Security & Privacy, Black Hat, DEF CON presentations",
                    "research": "NSA Research Directorate publications on binary analysis",
                    "comparisons": "Independent studies comparing Ghidra vs commercial tools",
                },
            },
            "expert_workflows": {
                "automated_analysis": [
                    "1. Batch processing with custom Ghidra scripts",
                    "2. CI/CD integration for continuous security scanning",
                    "3. API-driven analysis for large-scale malware processing",
                    "4. Custom plugin development for specialized analysis",
                ],
                "collaboration_setup": [
                    "1. Shared repository configuration for team analysis",
                    "2. Version control integration with Git",
                    "3. Review workflows for analysis validation",
                    "4. Automated diffing for patch analysis",
                ],
            },
            "troubleshooting": {
                "common_issues": {
                    "memory_usage": "Large binaries may require increased heap size (-Xmx8G)",
                    "analysis_time": "Complex binaries can take hours; for batch use analyzeHeadless or PyGhidra (see docs/GHIDRA.md)",
                    "false_positives": "Decompiler may produce incorrect code; always verify manually",
                    "plugin_conflicts": "Third-party plugins can cause stability issues",
                },
                "performance_tuning": {
                    "headless_flags": "-analysisTimeoutPerFile, -max-cpu, -commit",
                    "memory_settings": "-Xmx, -Xms for JVM heap configuration",
                    "parallel_processing": "Multiple Ghidra instances for batch analysis",
                },
            },
        }

    # Add topic-specific filtering if requested
    if topic:
        if topic.lower() == "ghidra":
            if level == "advanced":
                # Return only Ghidra-specific advanced content
                return {
                    "topic": "ghidra",
                    "level": "advanced",
                    **help_content["ghidra_expertise"],
                    **help_content["references"],
                }
            return {"error": f"Topic '{topic}' only available in advanced level"}
        if topic.lower() in ["binary", "analysis"]:
            return {
                "topic": topic,
                "level": level,
                "tools": help_content.get("tool_categories", {}).get("binary_analysis", []),
                "workflows": help_content.get("workflows", {}),
            }

    return help_content


@mcp.tool()
async def shutdown(confirm: bool = False) -> dict:
    """
    Gracefully shut down the Reversing MCP server.

    Requires confirm=True to prevent accidental termination.
    """
    if not confirm:
        return {"success": False, "message": "Shutdown requires confirm=True"}
    import os
    import threading
    threading.Thread(target=lambda: os._exit(0), daemon=True).start()
    return {"success": True, "message": "Server shutting down"}


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Reversing MCP Server - Free RE Tools + Directmedia Decompression"
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Set log level
    import logging

    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

    logger.info("Starting Reversing MCP Server")

    # Run MCP server
    run_server(mcp, server_name="ReversingMCP")


# ASGI app for uvicorn (e.g. web_sota: uvicorn reversing_mcp.server:app)
# Mounts MCP at /mcp; add more routes here if needed.
try:
    import platform

    from fastapi import FastAPI as _FastAPI
    from fastapi.middleware.cors import CORSMiddleware as _CORSMiddleware

    _http_app = _FastAPI(title="Reversing MCP HTTP", version="0.4.0")

    _http_app.add_middleware(
        _CORSMiddleware,
        allow_origins=[
            "http://localhost:10751",
            "http://127.0.0.1:10751",
            "http://localhost:10750",
            "http://127.0.0.1:10750",
            "tauri://localhost",
            "http://tauri.localhost",
            "https://tauri.localhost",
        ],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _start_time = __import__("time").time()

    @_http_app.get("/health")
    async def _health() -> dict:
        tools = mcp._tool_manager.list_tools() if hasattr(mcp, "_tool_manager") else []
        return {
            "status": "ok",
            "version": "0.4.0",
            "tool_count": len(tools),
        }

    @_http_app.get("/api/v1/diagnostics")
    async def _diagnostics() -> dict:
        tools = mcp._tool_manager.list_tools() if hasattr(mcp, "_tool_manager") else []
        uptime = int(__import__("time").time() - _start_time)
        return {
            "status": "ok",
            "server": "ReversingMCP",
            "version": "0.4.0",
            "uptime_seconds": uptime,
            "tool_count": len(tools),
            "tools": [{"name": t.name} for t in tools],
            "system": {
                "platform": platform.system(),
                "windows": platform.system() == "Windows",
                "python": platform.python_version(),
            },
            "errors": [],
        }

    @_http_app.post("/api/shutdown")
    async def _shutdown():
        import os
        os._exit(0)

    @_http_app.get("/api/skills")
    async def _list_skills():
        skills_dir = SKILLS_DIR
        if skills_dir.exists():
            names = [d.name for d in skills_dir.iterdir() if d.is_dir()]
            return {"skills": names}
        return {"skills": []}

    @_http_app.get("/api/skills/{name}")
    async def _get_skill(name: str):
        skill_path = SKILLS_DIR / name / "SKILL.md"
        if skill_path.exists():
            return {"name": name, "content": skill_path.read_text(encoding="utf-8")}
        return {"error": "Skill not found"}

    _http_app.mount("/mcp", mcp.http_app(path="/"))
    app = _http_app
except ImportError:
    pass  # no app when fastapi not installed; uvicorn reversing_mcp.server:app will fail


if __name__ == "__main__":
    main()
