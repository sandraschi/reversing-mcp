#!/usr/bin/env python3
"""
Reversing MCP Server - Ghidra and Free Reverse Engineering Tools
"""

import os
import subprocess
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .analyzers import BinaryAnalyzer
from .logging_config import get_logger

# Try to import Directmedia decompressor (optional)
try:
    from directmedia_mcp.directmedia_decompressor import DirectmediaDecompressor

    directmedia_available = True
except ImportError:
    directmedia_available = False
    logger.warning("Directmedia decompressor not available - Directmedia tools will be disabled")

logger = get_logger("reversing_mcp")

# Initialize MCP server
mcp = FastMCP("ReversingMCP", version="0.1.0")

# Import OUR CUSTOM Ghidra bridge (connects to LaurieWired's plugin)
try:
    from .bridge_mcp_ghidra import (
        decompile_function,
        decompile_function_by_address,
        disassemble_function,
        get_current_address,
        get_current_function,
        get_function_by_address,
        get_function_xrefs,
        get_xrefs_from,
        get_xrefs_to,
        list_classes,
        list_data_items,
        list_exports,
        list_functions,
        list_imports,
        # These are OUR MCP tools that call THEIR Ghidra plugin via HTTP
        list_methods,
        list_namespaces,
        list_segments,
        list_strings,
        rename_data,
        rename_function,
        rename_function_by_address,
        rename_variable,
        search_functions_by_name,
        set_decompiler_comment,
        set_disassembly_comment,
        set_function_prototype,
        set_local_variable_type,
    )

    ghidra_available = True
    logger.info("OUR Ghidra bridge loaded successfully (connects to LaurieWired's plugin)")
except ImportError as e:
    ghidra_available = False
    logger.warning(f"OUR Ghidra bridge not available: {e}")


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
directmedia_decompressor = DirectmediaDecompressor() if directmedia_available else None


@mcp.tool()
async def analyze_binary(file_path: str, tools: list[str] | None = None) -> dict[str, Any]:
    """
    Analyze a binary file with multiple reverse engineering tools

    Args:
        file_path: Path to the binary file to analyze
        tools: List of tools to use (ida, ghidra, r2, binwalk, static)
               If None, uses all available tools
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


@mcp.tool()
async def extract_strings(
    file_path: str, min_length: int = 4, encodings: list[str] | None = None
) -> list[dict[str, Any]]:
    """
    Extract strings from a binary file

    Args:
        file_path: Path to the binary file
        min_length: Minimum string length to extract
        encodings: List of encodings to try (ascii, utf-8, utf-16le, latin-1)
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


@mcp.tool()
async def get_hexdump(file_path: str, offset: int = 0, length: int = 256) -> dict[str, Any]:
    """
    Get hexadecimal dump of a binary file

    Args:
        file_path: Path to the binary file
        offset: Starting offset in bytes
        length: Number of bytes to dump
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        hexdump = analyzer.get_hexdump(file_path, offset, length)
        return {"file_path": file_path, "offset": offset, "length": length, "hexdump": hexdump}
    except Exception as e:
        logger.error(f"Error getting hexdump for {file_path}: {e}")
        return {"error": f"Hexdump failed: {e!s}"}


@mcp.tool()
async def analyze_entropy(file_path: str, block_size: int = 256) -> dict[str, Any]:
    """
    Analyze entropy of a binary file (detects compressed/encrypted sections)

    Args:
        file_path: Path to the binary file
        block_size: Block size for entropy calculation
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


@mcp.tool()
async def find_functions(file_path: str, tool: str = "auto") -> dict[str, Any]:
    """
    Find functions in a binary file

    Args:
        file_path: Path to the binary file
        tool: Tool to use (ida, ghidra, r2, auto)
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        functions = analyzer.find_functions(file_path, tool)
        return {"file_path": file_path, "tool_used": tool, "functions": functions}
    except Exception as e:
        logger.error(f"Error finding functions in {file_path}: {e}")
        return {"error": f"Function analysis failed: {e!s}"}


@mcp.tool()
async def get_file_info(file_path: str) -> dict[str, Any]:
    """
    Get basic information about a file

    Args:
        file_path: Path to the file to analyze
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


@mcp.tool()
async def check_tools() -> dict[str, Any]:
    """
    Check which reverse engineering tools are available on the system
    """
    try:
        available_tools = analyzer.check_available_tools()

        # Add GhidraMCP status
        available_tools["ghidra_mcp"] = {
            "name": "GhidraMCP (HTTP Server)",
            "available": ghidra_available,
            "version": "1.2" if ghidra_available else None,
            "description": "Ghidra plugin with HTTP server for MCP integration",
            "endpoint": "http://127.0.0.1:8080/" if ghidra_available else None,
        }

        # Add Directmedia status
        available_tools["directmedia"] = {
            "name": "Directmedia Decompressor",
            "available": directmedia_available,
            "version": "1.0" if directmedia_available else None,
            "description": "Extract text from Directmedia Digitale Bibliothek files",
        }

        return {
            "tools": available_tools,
            "summary": {
                "total": len(available_tools),
                "available": len([t for t in available_tools.values() if t["available"]]),
                "recommended": ["ghidra", "ghidra_mcp", "r2", "binwalk"],  # Free/open source tools
                "premium": ["ida"],  # Commercial tools
            },
            "notes": {
                "ghidra_setup": "Install GhidraMCP plugin (GhidraMCP.zip) and start Ghidra for HTTP server access",
                "directmedia_setup": "Install directmedia-mcp for .DKI file analysis",
            },
        }
    except Exception as e:
        logger.error(f"Error checking tools: {e}")
        return {"error": f"Tool check failed: {e!s}"}


@mcp.tool()
async def analyze_pe_file(file_path: str) -> dict[str, Any]:
    """
    Analyze a Windows PE (Portable Executable) file

    Args:
        file_path: Path to the PE file
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        pe_info = analyzer.analyze_pe_file(file_path)
        return {"file_path": file_path, "pe_info": pe_info}
    except Exception as e:
        logger.error(f"Error analyzing PE file {file_path}: {e}")
        return {"error": f"PE analysis failed: {e!s}"}


@mcp.tool()
async def analyze_directmedia_file(file_path: str) -> dict[str, Any]:
    """
    Analyze a Directmedia .DKI file and extract text content

    This tool can reverse engineer Directmedia Digitale Bibliothek files
    from the 1990s, extracting readable text content from proprietary formats.

    Args:
        file_path: Path to the .DKI file to analyze
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        result = directmedia_decompressor.extract_text_content(Path(file_path))

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


@mcp.tool()
async def decompress_directmedia_library(
    library_path: str, volume_filter: str | None = None
) -> dict[str, Any]:
    """
    Batch decompress all Directmedia volumes in a library

    Args:
        library_path: Path to the Directmedia library directory
        volume_filter: Optional filter for volume names (e.g., "DB002" or "*philo*")
    """
    if not os.path.exists(library_path):
        return {"error": f"Library path not found: {library_path}"}

    try:
        lib_path = Path(library_path)
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
                    result = directmedia_decompressor.extract_text_content(text_dki)

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
            "library_path": library_path,
            "volumes_processed": processed_volumes,
            "total_volumes_found": len(volume_dirs),
            "total_text_extracted": total_text_extracted,
            "results": results,
            "batch_status": "completed",
        }

    except Exception as e:
        logger.error(f"Error in batch Directmedia decompression: {e}")
        return {"error": f"Batch decompression failed: {e!s}"}


# GhidraMCP Tools Integration (if available)
if ghidra_available:
    # Register all GhidraMCP tools with the main MCP server

    @mcp.tool()
    async def ghidra_list_methods(offset: int = 0, limit: int = 100) -> list:
        """List all function names in the Ghidra program with pagination."""
        return list_methods(offset, limit)

    @mcp.tool()
    async def ghidra_list_classes(offset: int = 0, limit: int = 100) -> list:
        """List all namespace/class names in the Ghidra program with pagination."""
        return list_classes(offset, limit)

    @mcp.tool()
    async def ghidra_decompile_function(name: str) -> str:
        """Decompile a specific function by name and return the decompiled C code."""
        return decompile_function(name)

    @mcp.tool()
    async def ghidra_rename_function(old_name: str, new_name: str) -> str:
        """Rename a function by its current name to a new user-defined name."""
        return rename_function(old_name, new_name)

    @mcp.tool()
    async def ghidra_rename_data(address: str, new_name: str) -> str:
        """Rename a data label at the specified address."""
        return rename_data(address, new_name)

    @mcp.tool()
    async def ghidra_list_segments(offset: int = 0, limit: int = 100) -> list:
        """List all memory segments in the Ghidra program with pagination."""
        return list_segments(offset, limit)

    @mcp.tool()
    async def ghidra_list_imports(offset: int = 0, limit: int = 100) -> list:
        """List imported symbols in the Ghidra program with pagination."""
        return list_imports(offset, limit)

    @mcp.tool()
    async def ghidra_list_exports(offset: int = 0, limit: int = 100) -> list:
        """List exported functions/symbols with pagination."""
        return list_exports(offset, limit)

    @mcp.tool()
    async def ghidra_list_namespaces(offset: int = 0, limit: int = 100) -> list:
        """List all non-global namespaces in the Ghidra program with pagination."""
        return list_namespaces(offset, limit)

    @mcp.tool()
    async def ghidra_list_data_items(offset: int = 0, limit: int = 100) -> list:
        """List defined data labels and their values with pagination."""
        return list_data_items(offset, limit)

    @mcp.tool()
    async def ghidra_search_functions(query: str, offset: int = 0, limit: int = 100) -> list:
        """Search for functions whose name contains the given substring."""
        return search_functions_by_name(query, offset, limit)

    @mcp.tool()
    async def ghidra_rename_variable(function_name: str, old_name: str, new_name: str) -> str:
        """Rename a local variable within a function."""
        return rename_variable(function_name, old_name, new_name)

    @mcp.tool()
    async def ghidra_get_function_by_address(address: str) -> str:
        """Get a function by its address."""
        return get_function_by_address(address)

    @mcp.tool()
    async def ghidra_get_current_address() -> str:
        """Get the address currently selected by the user."""
        return get_current_address()

    @mcp.tool()
    async def ghidra_get_current_function() -> str:
        """Get the function currently selected by the user."""
        return get_current_function()

    @mcp.tool()
    async def ghidra_list_functions() -> list:
        """List all functions in the Ghidra database."""
        return list_functions()

    @mcp.tool()
    async def ghidra_decompile_by_address(address: str) -> str:
        """Decompile a function at the given address."""
        return decompile_function_by_address(address)

    @mcp.tool()
    async def ghidra_disassemble_function(address: str) -> list:
        """Get assembly code for a function."""
        return disassemble_function(address)

    @mcp.tool()
    async def ghidra_set_decompiler_comment(address: str, comment: str) -> str:
        """Set a comment for a given address in the function pseudocode."""
        return set_decompiler_comment(address, comment)

    @mcp.tool()
    async def ghidra_set_disassembly_comment(address: str, comment: str) -> str:
        """Set a comment for a given address in the function disassembly."""
        return set_disassembly_comment(address, comment)

    @mcp.tool()
    async def ghidra_rename_function_by_address(function_address: str, new_name: str) -> str:
        """Rename a function by its address."""
        return rename_function_by_address(function_address, new_name)

    @mcp.tool()
    async def ghidra_set_function_prototype(function_address: str, prototype: str) -> str:
        """Set a function's prototype."""
        return set_function_prototype(function_address, prototype)

    @mcp.tool()
    async def ghidra_set_variable_type(
        function_address: str, variable_name: str, new_type: str
    ) -> str:
        """Set a local variable's type."""
        return set_local_variable_type(function_address, variable_name, new_type)

    @mcp.tool()
    async def ghidra_get_xrefs_to(address: str, offset: int = 0, limit: int = 100) -> list:
        """Get all references to the specified address."""
        return get_xrefs_to(address, offset, limit)

    @mcp.tool()
    async def ghidra_get_xrefs_from(address: str, offset: int = 0, limit: int = 100) -> list:
        """Get all references from the specified address."""
        return get_xrefs_from(address, offset, limit)

    @mcp.tool()
    async def ghidra_get_function_xrefs(name: str, offset: int = 0, limit: int = 100) -> list:
        """Get all references to the specified function by name."""
        return get_function_xrefs(name, offset, limit)

    @mcp.tool()
    async def ghidra_list_strings(
        offset: int = 0, limit: int = 2000, filter_str: str = None
    ) -> list:
        """List all defined strings in the Ghidra program with their addresses."""
        return list_strings(offset, limit, filter_str)


@mcp.tool()
async def start_ghidra(
    file_path: str = None, project_name: str = None, wait: bool = False
) -> dict[str, Any]:
    """
    Start Ghidra GUI with optional binary file loading.

    This tool launches Ghidra manually when you want to use the Ghidra interface
    directly instead of through MCP tools. Useful for complex analysis or when
    you need the full Ghidra GUI experience.

    Args:
        file_path: Optional path to a binary file to open in Ghidra
        project_name: Optional project name to create/use (default: auto-generated)
        wait: Whether to wait for Ghidra to exit before returning (default: False)

    Returns:
        Dictionary with launch status and Ghidra information
    """
    try:
        # Check if Ghidra is available
        if not analyzer.tools_cache or not analyzer.tools_cache["ghidra"]["available"]:
            return {
                "error": "Ghidra not found on system",
                "available": False,
                "suggestion": "Install Ghidra and ensure GhidraMCP plugin is installed",
            }

        ghidra_path = analyzer.tools_cache["ghidra"]["path"]
        version = analyzer.tools_cache["ghidra"].get("version", "unknown")

        # Build command arguments
        cmd = [ghidra_path]

        # Add project creation if specified
        if project_name:
            # Create a temporary project directory if needed
            import tempfile

            temp_dir = tempfile.gettempdir()
            project_dir = os.path.join(temp_dir, f"ghidra_mcp_{project_name}")
            os.makedirs(project_dir, exist_ok=True)
            cmd.extend(["-import", project_dir])

        # Add file to import if specified
        if file_path:
            if not os.path.exists(file_path):
                return {
                    "error": f"File not found: {file_path}",
                    "ghidra_path": ghidra_path,
                    "version": version,
                }
            cmd.extend(["-import", file_path])

        logger.info(f"Starting Ghidra: {' '.join(cmd)}")

        # Launch Ghidra
        if wait:
            # Synchronous launch - wait for Ghidra to exit
            result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=300)
            return {
                "success": True,
                "ghidra_path": ghidra_path,
                "version": version,
                "command": " ".join(cmd),
                "file_loaded": file_path,
                "project_name": project_name,
                "waited": True,
                "return_code": result.returncode,
                "stdout": result.stdout[-500:] if result.stdout else None,
                "stderr": result.stderr[-500:] if result.stderr else None,
            }
        # Asynchronous launch - don't wait
        process = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        )

        # Give Ghidra a moment to start
        import time

        time.sleep(2)

        # Check if process is still running
        process.poll()

        return {
            "success": True,
            "ghidra_path": ghidra_path,
            "version": version,
            "command": " ".join(cmd),
            "file_loaded": file_path,
            "project_name": project_name,
            "waited": False,
            "process_id": process.pid if process.poll() is None else None,
            "process_running": process.poll() is None,
            "note": "Ghidra launched in background. Use MCP Ghidra tools once a binary is loaded.",
        }

    except subprocess.TimeoutExpired:
        return {
            "error": "Ghidra launch timed out",
            "ghidra_path": ghidra_path if "ghidra_path" in locals() else None,
            "suggestion": "Try launching Ghidra manually or check system resources",
        }
    except Exception as e:
        return {
            "error": f"Failed to start Ghidra: {e!s}",
            "ghidra_path": ghidra_path if "ghidra_path" in locals() else None,
            "suggestion": "Check Ghidra installation and try launching manually",
        }


@mcp.tool()
async def help(level: str = "basic", topic: str = None) -> dict[str, Any]:
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
            "quick_start": [
                "1. Check available tools: check_tools()",
                "2. Analyze a binary: analyze_binary('file.exe', ['static', 'strings'])",
                "3. Extract strings: extract_strings('file.exe', min_length=8)",
                "4. Get hex dump: get_hexdump('file.exe', offset=0, length=256)",
            ],
            "essential_tools": [
                "analyze_binary - Full binary analysis",
                "extract_strings - Find text in binaries",
                "get_hexdump - View raw bytes",
                "analyze_entropy - Detect compression/encryption",
                "check_tools - See what's available",
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
                ],
                "file_info": [
                    "get_file_info(file_path) - Basic file metadata",
                    "analyze_pe_file(file_path) - Windows PE analysis",
                    "file_type detection, permissions, timestamps",
                ],
                "ghidra_tools": [
                    "ghidra_decompile_function(name) - Decompile to C code",
                    "ghidra_list_functions() - All functions in loaded binary",
                    "ghidra_disassemble_function(addr) - Assembly code",
                    "ghidra_list_strings() - Extract strings with addresses",
                    "ghidra_get_xrefs_to/from(addr) - Cross-references",
                ]
                if ghidra_available
                else ["Ghidra tools not available - install GhidraMCP plugin"],
            },
            "workflows": {
                "malware_analysis": [
                    "1. check_tools() - Verify Ghidra availability",
                    "2. analyze_binary(file.exe, ['ghidra']) - Full analysis",
                    "3. ghidra_list_functions() - See all functions",
                    "4. ghidra_decompile_function('main') - Analyze main function",
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
                    "BinaryAnalyzer": "Multi-tool analysis orchestrator supporting IDA, Ghidra, radare2",
                    "GhidraMCP Integration": "HTTP-based Ghidra plugin bridge for headless analysis",
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
                    "current_version": "Ghidra 11.x series (as of 2024)",
                },
                "technical_capabilities": {
                    "decompiler": "Industry-leading retargetable decompiler with multi-architecture support",
                    "disassembler": "Supports 90+ processor architectures and instruction sets",
                    "analysis_engine": "Auto-analysis with function detection, data flow analysis, type inference",
                    "scripting": "Java-based scripting with full API access to analysis results",
                    "collaboration": "Multi-user analysis with version control integration",
                },
                "integration_architecture": {
                    "mcp_bridge": "HTTP server plugin exposes Ghidra API to MCP clients",
                    "headless_mode": "Non-GUI analysis for automation and CI/CD pipelines",
                    "api_endpoints": "RESTful API for decompilation, disassembly, cross-references",
                    "real_time_sync": "Live synchronization between GUI and headless sessions",
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
                    "analysis_time": "Complex binaries can take hours; use headless mode for batch processing",
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
    mcp.run()


if __name__ == "__main__":
    main()
