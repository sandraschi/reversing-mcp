#!/usr/bin/env python3
"""
Reversing MCP Server - Ghidra and Free Reverse Engineering Tools
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .analyzers import BinaryAnalyzer
from directmedia_mcp.directmedia_decompressor import DirectmediaDecompressor
from .logging_config import get_logger

logger = get_logger("reversing_mcp")

# Initialize MCP server
mcp = FastMCP(
    "ReversingMCP",
    version="0.1.0"
)


class AnalysisResult(BaseModel):
    """Result of binary analysis"""
    tool: str = Field(description="Tool used for analysis")
    file_path: str = Field(description="Path to analyzed file")
    file_size: int = Field(description="File size in bytes")
    file_type: str = Field(description="Detected file type")
    architecture: Optional[str] = Field(description="CPU architecture if detected")
    endianness: Optional[str] = Field(description="Endianness (little/big)")
    analysis: Dict[str, Any] = Field(description="Tool-specific analysis results")


class StringResult(BaseModel):
    """String extraction result"""
    offset: int = Field(description="Offset in file")
    string: str = Field(description="Extracted string")
    encoding: str = Field(description="String encoding")
    length: int = Field(description="String length")


# Global analyzer instances
analyzer = BinaryAnalyzer()
directmedia_decompressor = DirectmediaDecompressor()


@mcp.tool()
async def analyze_binary(file_path: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
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
            "results": results
        }
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return {"error": f"Analysis failed: {str(e)}"}


@mcp.tool()
async def extract_strings(file_path: str, min_length: int = 4,
                         encodings: Optional[List[str]] = None) -> List[Dict[str, Any]]:
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
        return [{"error": f"String extraction failed: {str(e)}"}]


@mcp.tool()
async def get_hexdump(file_path: str, offset: int = 0, length: int = 256) -> Dict[str, Any]:
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
        return {
            "file_path": file_path,
            "offset": offset,
            "length": length,
            "hexdump": hexdump
        }
    except Exception as e:
        logger.error(f"Error getting hexdump for {file_path}: {e}")
        return {"error": f"Hexdump failed: {str(e)}"}


@mcp.tool()
async def analyze_entropy(file_path: str, block_size: int = 256) -> Dict[str, Any]:
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
            "random_regions": entropy_data["random"]
        }
    except Exception as e:
        logger.error(f"Error analyzing entropy for {file_path}: {e}")
        return {"error": f"Entropy analysis failed: {str(e)}"}


@mcp.tool()
async def find_functions(file_path: str, tool: str = "auto") -> Dict[str, Any]:
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
        return {
            "file_path": file_path,
            "tool_used": tool,
            "functions": functions
        }
    except Exception as e:
        logger.error(f"Error finding functions in {file_path}: {e}")
        return {"error": f"Function analysis failed: {str(e)}"}


@mcp.tool()
async def get_file_info(file_path: str) -> Dict[str, Any]:
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
            "executable": os.access(file_path, os.X_OK)
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        return {"error": f"File info failed: {str(e)}"}


@mcp.tool()
async def check_tools() -> Dict[str, Any]:
    """
    Check which reverse engineering tools are available on the system
    """
    try:
        available_tools = analyzer.check_available_tools()
        return {
            "tools": available_tools,
            "summary": {
                "total": len(available_tools),
                "available": len([t for t in available_tools.values() if t["available"]]),
                "recommended": ["ghidra", "r2", "binwalk"]  # Free/open source tools
            }
        }
    except Exception as e:
        logger.error(f"Error checking tools: {e}")
        return {"error": f"Tool check failed: {str(e)}"}


@mcp.tool()
async def analyze_pe_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Windows PE (Portable Executable) file

    Args:
        file_path: Path to the PE file
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        pe_info = analyzer.analyze_pe_file(file_path)
        return {
            "file_path": file_path,
            "pe_info": pe_info
        }
    except Exception as e:
        logger.error(f"Error analyzing PE file {file_path}: {e}")
        return {"error": f"PE analysis failed: {str(e)}"}


@mcp.tool()
async def analyze_directmedia_file(file_path: str) -> Dict[str, Any]:
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
                "offsets_found": len(result["analysis"]["offsets"])
            },
            "extraction_summary": {
                "sections_processed": len(result["extracted_sections"]),
                "total_text_bytes": result["total_extracted_size"]
            }
        }

        # Add sample extracted content
        if result["extracted_sections"]:
            samples = []
            for section in result["extracted_sections"][:3]:
                if "records" in section and section["records"]:
                    for record in section["records"][:2]:
                        text = record.get("text_content", "")
                        if text and len(text) > 10:
                            samples.append(text[:200] + "..." if len(text) > 200 else text)

            if samples:
                response["sample_content"] = samples

        # Save extracted content to file
        output_file = Path(file_path).parent / f"{Path(file_path).stem}_extracted.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Directmedia Decompression Results for {file_path}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Analysis Summary:\n")
            f.write(f"- File size: {result['analysis']['file_size']:,} bytes\n")
            f.write(f"- Magic number: 0x{result['analysis']['magic_number']:08x}\n")
            f.write(f"- Compression type: {result['analysis']['compression_type'].name}\n")
            f.write(f"- Offsets found: {len(result['analysis']['offsets'])}\n")
            f.write(f"- Sections extracted: {len(result['extracted_sections'])}\n")
            f.write(f"- Total text bytes: {result['total_extracted_size']:,}\n\n")

            # Write all extracted text
            all_text_parts = []
            for section in result["extracted_sections"]:
                if "records" in section and section["records"]:
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
        return {"error": f"Directmedia analysis failed: {str(e)}"}


@mcp.tool()
async def decompress_directmedia_library(library_path: str, volume_filter: Optional[str] = None) -> Dict[str, Any]:
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
                        "text_bytes": result["total_extracted_size"]
                    }

                    total_text_extracted += result["total_extracted_size"]
                    processed_volumes += 1
                    results.append(volume_result)

                except Exception as e:
                    results.append({
                        "volume": volume_dir.name,
                        "error": str(e)
                    })

        return {
            "library_path": library_path,
            "volumes_processed": processed_volumes,
            "total_volumes_found": len(volume_dirs),
            "total_text_extracted": total_text_extracted,
            "results": results,
            "batch_status": "completed"
        }

    except Exception as e:
        logger.error(f"Error in batch Directmedia decompression: {e}")
        return {"error": f"Batch decompression failed: {str(e)}"}


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Reversing MCP Server - Free RE Tools + Directmedia Decompression")
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

