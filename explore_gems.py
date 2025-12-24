#!/usr/bin/env python3
"""
Historical Gems Explorer

Quick investigation of legacy file formats to assess reverse engineering potential.
This script helps identify promising targets for future preservation efforts.
"""

import os
import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

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
    "CDF": b"CDF\x01",     # Common Data Format
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

def detect_file_format(file_path: Path) -> Tuple[str, str]:
    """
    Attempt to detect file format based on signatures.
    Returns (format_name, confidence_level)
    """
    try:
        with open(file_path, 'rb') as f:
            # Read first 512 bytes for signature detection
            header = f.read(512)

            for format_name, signature in FORMAT_SIGNATURES.items():
                if header.startswith(signature):
                    return format_name, "HIGH"

            # Check for variations
            if header.startswith(b"GIF89a"):
                return "GIF", "HIGH"

            # Check for compound formats
            if header.startswith(b"RIFF"):
                # Could be WAV, AVI, etc.
                riff_type = header[8:12]
                if riff_type == b"WAVE":
                    return "WAV", "HIGH"
                elif riff_type == b"AVI ":
                    return "AVI", "HIGH"

            # PE file detection (MZ followed by PE)
            if header.startswith(b"MZ"):
                # Look for PE signature at offset in e_lfanew
                if len(header) >= 64:
                    pe_offset = struct.unpack('<I', header[60:64])[0]
                    if pe_offset < len(header) - 4:
                        if header[pe_offset:pe_offset+4] == b"PE\x00\x00":
                            return "PE", "HIGH"

            return "UNKNOWN", "LOW"

    except Exception as e:
        return f"ERROR: {str(e)}", "ERROR"

def analyze_file_structure(file_path: Path) -> Dict:
    """Perform basic structural analysis of a file."""
    analysis = {
        "path": str(file_path),
        "size": file_path.stat().st_size,
        "format": "UNKNOWN",
        "confidence": "LOW",
        "entropy": 0.0,
        "sections": [],
        "metadata": {}
    }

    # Detect format
    analysis["format"], analysis["confidence"] = detect_file_format(file_path)

    # Calculate basic entropy
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            if data:
                from collections import Counter
                byte_counts = Counter(data)
                total_bytes = len(data)
                entropy = 0
                for count in byte_counts.values():
                    p = count / total_bytes
                    if p > 0:
                        entropy -= p * (p.bit_length() - 1)  # Approximation
                analysis["entropy"] = entropy
    except:
        pass

    return analysis

def scan_directory_for_gems(directory: Path, max_files: int = 100) -> List[Dict]:
    """
    Scan a directory for interesting legacy files.
    Returns analysis of files that might be worth reverse engineering.
    """
    interesting_files = []
    scanned = 0

    print(f"Scanning directory: {directory}")
    print(f"Max files to analyze: {max_files}")

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        if scanned >= max_files:
            break

        # Skip common modern files
        if file_path.suffix.lower() in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
            continue

        # Skip very small or very large files
        size = file_path.stat().st_size
        if size < 100 or size > 100*1024*1024:  # 100 bytes to 100MB
            continue

        analysis = analyze_file_structure(file_path)
        scanned += 1

        # Consider it interesting if:
        # - Unknown format with decent entropy (likely compressed/encoded)
        # - Old format signatures
        # - High entropy suggesting compression
        interesting = (
            analysis["confidence"] == "LOW" and analysis["entropy"] > 3.0 or
            analysis["format"] in ["ELF", "PE", "CDF", "FITS", "HDF", "DBF"] or
            analysis["entropy"] > 7.0  # Very high entropy = likely encrypted/compressed
        )

        if interesting:
            interesting_files.append(analysis)
            print(f"Found interesting file: {file_path.name} ({analysis['format']}, entropy: {analysis['entropy']:.2f})")

    return interesting_files

def assess_preservation_value(analysis: Dict) -> Dict:
    """Assess the digital preservation value of a file format."""
    format_scores = {
        "FITS": 9,    # Astronomical data - very valuable
        "CDF": 8,     # Scientific data format
        "HDF": 8,     # Scientific data format
        "DBF": 7,     # Legacy database
        "ELF": 6,     # Executable format (some preservation value)
        "PE": 6,      # Windows executable
        "UNKNOWN": 5, # Mystery format - could be valuable
    }

    score = format_scores.get(analysis["format"], 3)

    # Adjust for entropy (high entropy suggests compression/encryption = more complex)
    if analysis["entropy"] > 6.0:
        score += 2

    # Adjust for file size (larger files often more complex)
    size_mb = analysis["size"] / (1024*1024)
    if size_mb > 10:
        score += 1

    assessment = {
        "file": analysis["path"],
        "format": analysis["format"],
        "preservation_score": score,
        "complexity": "HIGH" if score > 7 else "MEDIUM" if score > 5 else "LOW",
        "recommendation": "HIGH PRIORITY" if score > 7 else "CONSIDER" if score > 5 else "SKIP"
    }

    return assessment

def main():
    """Main exploration function."""
    print("Historical Gems Explorer")
    print("=" * 50)

    # Default directories to scan
    scan_dirs = [
        Path("C:/Windows/System32").resolve(),  # System files (be careful!)
        Path("C:/Program Files").resolve(),     # Program files
        Path("D:/").resolve(),                   # Data drive
    ]

    # Filter to existing directories
    existing_dirs = [d for d in scan_dirs if d.exists() and d.is_dir()]

    if not existing_dirs:
        print("No directories found to scan. Please specify directories to explore.")
        return

    print(f"Will scan {len(existing_dirs)} directories for legacy file formats...")
    print()

    all_findings = []
    for directory in existing_dirs:
        try:
            findings = scan_directory_for_gems(directory, max_files=50)
            all_findings.extend(findings)
        except PermissionError:
            print(f"Permission denied accessing: {directory}")
        except Exception as e:
            print(f"Error scanning {directory}: {e}")

    if not all_findings:
        print("No interesting legacy files found in scanned directories.")
        print("Try scanning directories with older software or data archives.")
        return

    print(f"\nFound {len(all_findings)} potentially interesting files")
    print("=" * 60)

    # Assess preservation value
    assessments = [assess_preservation_value(f) for f in all_findings]

    # Sort by preservation score
    assessments.sort(key=lambda x: x["preservation_score"], reverse=True)

    # Display top findings
    for i, assessment in enumerate(assessments[:10]):  # Top 10
        print("2d"
              f"Format: {assessment['format']}\n"
              f"Complexity: {assessment['complexity']}\n"
              f"Recommendation: {assessment['recommendation']}\n"
              f"Path: {assessment['file']}\n")

    # Save detailed results
    output_file = Path("gems_analysis.json")
    with open(output_file, 'w') as f:
        json.dump({
            "scan_timestamp": str(Path(output_file).stat().st_mtime),
            "directories_scanned": [str(d) for d in existing_dirs],
            "total_files_analyzed": len(all_findings),
            "findings": assessments
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")
    print("\nNext Steps:")
    print("1. Examine high-priority files manually")
    print("2. Research file format specifications")
    print("3. Consider building preservation tools")
    print("4. Contribute to digital archaeology efforts")

if __name__ == "__main__":
    main()
