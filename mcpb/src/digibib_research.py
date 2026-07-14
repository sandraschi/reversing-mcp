"""
Digibib5.exe / Directmedia (DKI) — static research helpers.

Produces a structured snapshot for agents and humans before ReVa/Ghidra interactive work.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .analyzers import BinaryAnalyzer

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Prefer fixture copy, then typical Windows install.
DEFAULT_DIGIBIB_CANDIDATES: tuple[Path, ...] = (
    _REPO_ROOT / "tests" / "fixtures" / "exe files" / "Digibib5.exe",
    Path(r"C:\Program Files (x86)\Digitale Bibliothek 5\Digibib5.exe"),
)

# Substrings that often surface read/decompress/UI paths in Digibib / Directmedia stacks.
DIRECTMEDIA_KEYWORDS: tuple[str, ...] = (
    "DKI",
    ".dki",
    "Directmedia",
    "directmedia",
    "Huffman",
    "Decompress",
    "decompress",
    "Unpack",
    "unpack",
    "inflate",
    "deflate",
    "zlib",
    "LZ",
    "Bibliothek",
    "Digitale",
    "TEXT.DKI",
    "expand",
    "uncompress",
    "CreateFile",
    "ReadFile",
    "MapViewOfFile",
    "lzx",
    "mspack",
)


def resolve_digibib_exe(explicit: str | None) -> tuple[Path | None, list[str]]:
    """Return first existing Digibib5.exe path, or None with list of paths tried."""
    tried: list[str] = []
    if explicit:
        p = Path(os.path.expandvars(explicit)).expanduser()
        tried.append(str(p.resolve()))
        if p.is_file():
            return p.resolve(), tried
        return None, tried
    for c in DEFAULT_DIGIBIB_CANDIDATES:
        tried.append(str(c.resolve()))
        if c.is_file():
            return c.resolve(), tried
    return None, tried


def filter_directmedia_strings(
    strings: list[Any], keywords: tuple[str, ...] = DIRECTMEDIA_KEYWORDS
) -> list[dict[str, Any]]:
    """Tag strings whose text matches any keyword (case-insensitive)."""
    out: list[dict[str, Any]] = []
    for s in strings:
        if hasattr(s, "model_dump"):
            row = s.model_dump()
        elif isinstance(s, dict):
            row = dict(s)
        else:
            continue
        val = row.get("string") or ""
        if not val:
            continue
        lower = val.lower()
        hit = next((k for k in keywords if k.lower() in lower), None)
        if hit:
            row["keyword_hit"] = hit
            out.append(row)
    out.sort(key=lambda r: (r.get("offset", 0), r.get("string", "")))
    return out


def build_research_snapshot(analyzer: BinaryAnalyzer, exe_path: str | Path) -> dict[str, Any]:
    """Run static extraction: metadata, keyword strings, entropy, tool availability."""
    p = Path(exe_path).resolve()
    if not p.is_file():
        return {"success": False, "error": f"Not a file: {p}"}

    analyzer.check_available_tools()
    info = analyzer.get_file_info(str(p))
    if info.get("error"):
        return {"success": False, "error": str(info["error"]), "exe_path": str(p)}

    strings = analyzer.extract_strings(str(p), min_length=5)
    hits = filter_directmedia_strings(strings)
    entropy = analyzer.analyze_entropy(str(p), block_size=512)
    ghidra = (analyzer.tools_cache or {}).get("ghidra", {})

    pe_summary = None
    pe = info.get("pe_info")
    if isinstance(pe, dict) and pe.get("valid_pe"):
        pe_summary = {k: pe[k] for k in ("valid_pe", "machine", "num_sections") if k in pe}

    return {
        "success": True,
        "exe_path": str(p),
        "file_info": {
            "size": info.get("size"),
            "type": info.get("type"),
            "pe_summary": pe_summary,
        },
        "directmedia_string_hits": hits[:400],
        "directmedia_string_hits_total": len(hits),
        "total_strings_sampled": len(strings),
        "entropy": {
            "overall": entropy.get("overall"),
            "random_region_count": len(entropy.get("random_regions", [])),
            "compressed_region_count": len(entropy.get("compressed_regions", [])),
        },
        "tools": {
            "ghidra_headless_available": bool(ghidra.get("available")),
            "ghidra_hint": ghidra.get("path"),
        },
        "next_steps": [
            "Open the same binary in Ghidra with ReVa MCP; search for symbols/strings from directmedia_string_hits.",
            "Trace xrefs from kernel32 ReadFile/CreateFileW (imports) to locate DKI open/read.",
            "When Ghidra is installed: analyze_binary(str(exe_path), ['ghidra']) for function/string JSON from headless script.",
            "Batch TEXT.DKI: set DIGITALE_BIBLIOTHEK_ROOT or use default L:\\Multimedia Files\\Written Word\\Digitale Bibliothek; call decompress_directmedia_library() or decode_dki_file on DB*/Data/TEXT.DKI.",
            "See docs/DIRECTMEDIA_REVERSING_TOOLKIT.md for viewer milestones.",
        ],
        "viewer_roadmap": [
            "M1 — Freeze static snapshot (this tool + JSON export) as baseline.",
            "M2 — Document DKI read path: functions that open .dki / TEXT.DKI and first bytes read.",
            "M3 — Built-in DKI decode: decode_dki_file / analyze_directmedia_file (zlib heuristics); extend if format differs.",
            "M4 — Modern viewer: stream text/HTML from decoded DKI; validate against original app.",
        ],
    }
