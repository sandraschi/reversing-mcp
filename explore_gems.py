#!/usr/bin/env python3
"""
Historical Gems Explorer

Quick investigation of legacy file formats to assess reverse engineering potential.
This script helps identify promising targets for future preservation efforts.
"""

import json
import logging
import struct
from collections import Counter
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Constants for magic values
HEADER_READ_SIZE = 512
PE_SIGNATURE_SIZE = 4
PE_OFFSET_SIZE = 4
MIN_PE_HEADER_SIZE = 64
RIFF_TYPE_OFFSET = 8
RIFF_TYPE_SIZE = 4
MIN_INTERESTING_SIZE = 100
MAX_INTERESTING_SIZE = 100 * 1024 * 1024  # 100MB
MODERATE_ENTROPY_THRESHOLD = 3.0
HIGH_ENTROPY_THRESHOLD = 7.0
LARGE_FILE_THRESHOLD_MB = 10
HIGH_PRESERVATION_SCORE = 7
MEDIUM_PRESERVATION_SCORE = 5

# Sample file signatures and format detectors
FORMAT_SIGNATURES = {
    # E-book and document formats
    "PDF": b"%PDF-",
    "PS": b"%!PS-Adobe-",
    "RTF": b"{\\rtf1",
    "DOC": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",  # OLE2 signature
    "XLS": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",  # OLE2 signature
    # Archive formats
    "ZIP": b"PK\x03\x04",
    "RAR": b"Rar!\x1a\x07",
    "TAR": b"ustar",  # At offset 257
    "GZ": b"\x1f\x8b",
    # Image formats
    "PNG": b"\x89PNG\r\n\x1a\n",
    "GIF": b"GIF87a",  # or GIF89a
    "JPEG": b"\xff\xd8\xff",
    "BMP": b"BM",
    "TIFF": b"II*\x00",  # Little-endian TIFF
    # Audio formats
    "WAV": b"RIFF",
    "MP3": b"ID3",  # or \xff\xfb
    "FLAC": b"fLaC",
    # Video formats
    "AVI": b"RIFF",
    "MP4": b"ftyp",
    "MOV": b"moov",
    # Scientific/Research formats
    "FITS": b"SIMPLE  =",  # Astronomical data
    "CDF": b"CDF\x01",  # Common Data Format
    "HDF": b"\x89HDF\r\n\x1a\n",  # HDF5
    "NetCDF": b"CDF\x02",
    # Database formats
    "SQLite": b"SQLite format 3\x00",
    "DBF": b"\x03",  # dBase III header
    # Programming/Executable
    "ELF": b"\x7fELF",
    "PE": b"MZ",  # DOS header, followed by PE
    "MachO": b"\xfe\xed\xfa\xce",  # 32-bit big-endian
}


def detect_file_format(file_path: Path) -> tuple[str, str]:
    """
    Attempt to detect file format based on signatures.
    Returns (format_name, confidence_level)
    """
    try:
        with file_path.open("rb") as f:
            header = f.read(HEADER_READ_SIZE)

            # Check primary signatures
            for format_name, signature in FORMAT_SIGNATURES.items():
                if header.startswith(signature):
                    return format_name, "HIGH"

            # Check for specific format variations
            if header.startswith(b"GIF89a"):
                return "GIF", "HIGH"

            # Check RIFF formats
            if (header.startswith(b"RIFF") and
                len(header) > RIFF_TYPE_OFFSET + RIFF_TYPE_SIZE):
                riff_type = header[RIFF_TYPE_OFFSET:RIFF_TYPE_OFFSET + RIFF_TYPE_SIZE]
                if riff_type in (b"WAVE", b"AVI "):
                    return "WAV" if riff_type == b"WAVE" else "AVI", "HIGH"

            # PE file detection
            if (header.startswith(b"MZ") and len(header) >= MIN_PE_HEADER_SIZE):
                pe_offset = struct.unpack("<I", header[60:64])[0]
                if (pe_offset < len(header) - PE_SIGNATURE_SIZE and
                    header[pe_offset:pe_offset + PE_SIGNATURE_SIZE] == b"PE\x00\x00"):
                    return "PE", "HIGH"

            return "UNKNOWN", "LOW"

    except OSError as e:
        logger.exception("Error reading file %s", file_path)
        return f"ERROR: {e!s}", "ERROR"


def analyze_file_structure(file_path: Path) -> dict:
    """Perform basic structural analysis of a file."""
    analysis = {
        "path": str(file_path),
        "size": file_path.stat().st_size,
        "format": "UNKNOWN",
        "confidence": "LOW",
        "entropy": 0.0,
        "sections": [],
        "metadata": {},
    }

    # Detect format
    analysis["format"], analysis["confidence"] = detect_file_format(file_path)

    # Calculate basic entropy
    try:
        with file_path.open("rb") as f:
            data = f.read()
            if data:
                byte_counts = Counter(data)
                total_bytes = len(data)
                entropy = 0
                for count in byte_counts.values():
                    p = count / total_bytes
                    if p > 0:
                        entropy -= p * (p.bit_length() - 1)  # Approximation
                analysis["entropy"] = entropy
    except OSError:
        logger.exception("Could not calculate entropy")

    return analysis


def scan_directory_for_gems(directory: Path, max_files: int = 100) -> list[dict]:
    """
    Scan a directory for interesting legacy files.
    Returns analysis of files that might be worth reverse engineering.
    """
    interesting_files = []
    scanned = 0

    logger.info("Scanning directory: %s", directory)
    logger.info("Max files to analyze: %s", max_files)

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        if scanned >= max_files:
            break

        # Skip common modern files
        if file_path.suffix.lower() in [
            ".txt",
            ".md",
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".xml",
        ]:
            continue

        # Skip very small or very large files
        size = file_path.stat().st_size
        if size < MIN_INTERESTING_SIZE or size > MAX_INTERESTING_SIZE:
            continue

        analysis = analyze_file_structure(file_path)
        scanned += 1

        # Consider it interesting if:
        # - Unknown format with decent entropy (likely compressed/encoded)
        # - Old format signatures
        # - High entropy suggesting compression
        interesting = (
            (analysis["confidence"] == "LOW" and analysis["entropy"] > MODERATE_ENTROPY_THRESHOLD)
            or analysis["format"] in ["ELF", "PE", "CDF", "FITS", "HDF", "DBF"]
            or analysis["entropy"] > HIGH_ENTROPY_THRESHOLD
        )

        if interesting:
            interesting_files.append(analysis)
        logger.info(
            "Found interesting file: %s (%s, entropy: %.2f)",
            file_path.name, analysis["format"], analysis["entropy"]
        )

    return interesting_files


def assess_preservation_value(analysis: dict) -> dict:
    """Assess the digital preservation value of a file format."""
    format_scores = {
        "FITS": 9,  # Astronomical data - very valuable
        "CDF": 8,  # Scientific data format
        "HDF": 8,  # Scientific data format
        "DBF": 7,  # Legacy database
        "ELF": 6,  # Executable format (some preservation value)
        "PE": 6,  # Windows executable
        "UNKNOWN": 5,  # Mystery format - could be valuable
    }

    score = format_scores.get(analysis["format"], 3)

    # Adjust for entropy (high entropy suggests compression/encryption = more complex)
    if analysis["entropy"] > HIGH_ENTROPY_THRESHOLD:
        score += 2

    # Adjust for file size (larger files often more complex)
    size_mb = analysis["size"] / (1024 * 1024)
    if size_mb > LARGE_FILE_THRESHOLD_MB:
        score += 1

    complexity = ("HIGH" if score > HIGH_PRESERVATION_SCORE else
                  "MEDIUM" if score > MEDIUM_PRESERVATION_SCORE else "LOW")
    recommendation = ("HIGH PRIORITY" if score > HIGH_PRESERVATION_SCORE else
                     "CONSIDER" if score > MEDIUM_PRESERVATION_SCORE else "SKIP")

    return {
        "file": analysis["path"],
        "format": analysis["format"],
        "preservation_score": score,
        "complexity": complexity,
        "recommendation": recommendation,
    }


def main():
    """Main exploration function."""
    logger.info("Historical Gems Explorer")
    logger.info("=" * 50)

    # Default directories to scan
    scan_dirs = [
        Path("C:/Windows/System32").resolve(),  # System files (be careful!)
        Path("C:/Program Files").resolve(),  # Program files
        Path("D:/").resolve(),  # Data drive
    ]

    # Filter to existing directories
    existing_dirs = [d for d in scan_dirs if d.exists() and d.is_dir()]

    if not existing_dirs:
        logger.error("No directories found to scan. Please specify directories to explore.")
        return

    logger.info("Will scan %s directories for legacy file formats...", len(existing_dirs))

    all_findings = []
    for directory in existing_dirs:
        try:
            findings = scan_directory_for_gems(directory, max_files=50)
            all_findings.extend(findings)
        except PermissionError:
            logger.warning("Permission denied accessing: %s", directory)
        except Exception:
            logger.exception("Error scanning %s", directory)

    if not all_findings:
        logger.info("No interesting legacy files found in scanned directories.")
        logger.info("Try scanning directories with older software or data archives.")
        return

    logger.info("\nFound %s potentially interesting files", len(all_findings))
    logger.info("=" * 60)

    # Assess preservation value
    assessments = [assess_preservation_value(f) for f in all_findings]

    # Sort by preservation score
    assessments.sort(key=lambda x: x["preservation_score"], reverse=True)

    # Display top findings
    for i, assessment in enumerate(assessments[:10]):  # Top 10
        logger.info(
            "%2d. Format: %s, Complexity: %s, Recommendation: %s, Path: %s",
            i + 1, assessment["format"], assessment["complexity"],
            assessment["recommendation"], assessment["file"]
        )

    # Save detailed results
    output_file = Path("gems_analysis.json")
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "scan_timestamp": str(Path(output_file).stat().st_mtime),
                "directories_scanned": [str(d) for d in existing_dirs],
                "total_files_analyzed": len(all_findings),
                "findings": assessments,
            },
            f,
            indent=2,
        )

    logger.info("\nDetailed results saved to: %s", output_file)
    logger.info("\nNext Steps:")
    logger.info("1. Examine high-priority files manually")
    logger.info("2. Research file format specifications")
    logger.info("3. Consider building preservation tools")
    logger.info("4. Contribute to digital archaeology efforts")


if __name__ == "__main__":
    main()
