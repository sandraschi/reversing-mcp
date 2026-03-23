"""
Directmedia / Digitale Bibliothek — .DKI decoder (in-repo).

Digibib5.exe embeds zlib inflate; TEXT.DKI blobs are commonly zlib-wrapped, sometimes after a
short header. This module autodetects zlib/gzip/raw-deflate placements without external packages.
"""

from __future__ import annotations

import gzip
import os
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any


@dataclass
class DKIDecodeAttempt:
    strategy: str
    ok: bool
    detail: str = ""


@dataclass
class DKIDecodeResult:
    success: bool
    raw_uncompressed: bytes
    text_preview: str
    encoding_guess: str
    attempts: list[DKIDecodeAttempt] = field(default_factory=list)
    error: str | None = None
    strategy_used: str | None = None


def _is_zlib_header(data: bytes, i: int) -> bool:
    if i + 1 >= len(data):
        return False
    cmf, flg = data[i], data[i + 1]
    if ((cmf << 8) | flg) % 31 != 0:
        return False
    if cmf & 0x0F != 8:
        return False
    return True


def _decode_text_from_bytes(data: bytes) -> tuple[str, str]:
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            t = data.decode(enc)
            if sum(ch.isprintable() or ch in "\n\r\t" for ch in t) / max(len(t), 1) > 0.85:
                return t, enc
        except UnicodeDecodeError:
            continue
    t = data.decode("latin-1", errors="replace")
    return t, "latin-1/replace"


def _plausible_text(data: bytes) -> bool:
    if len(data) < 8:
        return False
    sample = data[: min(4096, len(data))]
    printable = sum(32 <= b < 127 or b in (9, 10, 13) for b in sample)
    return printable / len(sample) > 0.65


def _try_zlib(data: bytes, wbits: int = zlib.MAX_WBITS) -> bytes | None:
    try:
        return zlib.decompress(data, wbits)
    except zlib.error:
        return None


def _try_gzip(data: bytes) -> bytes | None:
    try:
        return gzip.decompress(data)
    except OSError:
        return None


def _zlib_stream_starts(data: bytes, max_hits: int = 48) -> list[int]:
    out: list[int] = []
    for i in range(len(data) - 6):
        if _is_zlib_header(data, i) and i not in out:
            out.append(i)
            if len(out) >= max_hits:
                break
    return out


def decode_dki_bytes(data: bytes) -> DKIDecodeResult:
    attempts: list[DKIDecodeAttempt] = []
    if not data:
        return DKIDecodeResult(
            success=False,
            raw_uncompressed=b"",
            text_preview="",
            encoding_guess="",
            attempts=attempts,
            error="empty file",
        )

    candidates: list[tuple[str, bytes]] = []

    for name, fn in (
        ("zlib_whole", lambda d: _try_zlib(d)),
        ("gzip_whole", _try_gzip),
    ):
        got = fn(data)
        attempts.append(DKIDecodeAttempt(name, got is not None))
        if got and _plausible_text(got):
            candidates.append((name, got))

    for skip in (4, 8, 12, 16, 20, 24, 32, 40, 48, 64):
        if len(data) <= skip:
            continue
        got = _try_zlib(data[skip:])
        name = f"zlib_after_skip_{skip}"
        attempts.append(DKIDecodeAttempt(name, got is not None))
        if got and _plausible_text(got):
            candidates.append((name, got))

    for skip in (0, 4, 8, 12, 16):
        if len(data) <= skip:
            continue
        got = _try_zlib(data[skip:], wbits=-zlib.MAX_WBITS)
        name = f"raw_deflate_skip_{skip}"
        attempts.append(DKIDecodeAttempt(name, got is not None))
        if got and _plausible_text(got):
            candidates.append((name, got))

    for off in _zlib_stream_starts(data):
        got = _try_zlib(data[off:])
        name = f"zlib_from_offset_0x{off:x}"
        attempts.append(DKIDecodeAttempt(name, got is not None))
        if got and _plausible_text(got):
            candidates.append((name, got))

    if not candidates:
        best: tuple[str, bytes] | None = None
        for off in _zlib_stream_starts(data, max_hits=96):
            got = _try_zlib(data[off:])
            if got and (best is None or len(got) > len(best[1])):
                best = (f"zlib_largest_from_0x{off:x}", got)
        if best and len(best[1]) > 64:
            candidates.append(best)

    if not candidates:
        return DKIDecodeResult(
            success=False,
            raw_uncompressed=b"",
            text_preview="",
            encoding_guess="",
            attempts=attempts,
            error=(
                "DKI decode failed: no zlib/gzip payload matched text heuristics. "
                "If this volume uses another codec, capture a TEXT.DKI sample and extend directmedia_dki.py."
            ),
        )

    strategy, raw = max(candidates, key=lambda x: len(x[1]))
    text, enc = _decode_text_from_bytes(raw)
    preview = text[:8000] + ("…" if len(text) > 8000 else "")
    return DKIDecodeResult(
        success=True,
        raw_uncompressed=raw,
        text_preview=preview,
        encoding_guess=enc,
        attempts=attempts,
        strategy_used=strategy,
    )


def decode_dki_path(path: Path) -> DKIDecodeResult:
    p = path.expanduser()
    if not p.is_file():
        return DKIDecodeResult(
            success=False,
            raw_uncompressed=b"",
            text_preview="",
            encoding_guess="",
            error=f"not a file: {p}",
        )
    data = p.read_bytes()
    return decode_dki_bytes(data)


def result_to_mcp_dict(path: Path | str, r: DKIDecodeResult) -> dict[str, Any]:
    out: dict[str, Any] = {
        "success": r.success,
        "file_path": str(path),
        "strategy_used": r.strategy_used,
        "encoding_guess": r.encoding_guess,
        "uncompressed_bytes": len(r.raw_uncompressed),
        "text_preview": r.text_preview,
        "attempts": [{"strategy": a.strategy, "ok": a.ok, "detail": a.detail} for a in r.attempts],
    }
    if r.error:
        out["error"] = r.error
    return out


def legacy_extract_for_server(path: Path) -> dict[str, Any]:
    """
    Response shape expected by server.analyze_directmedia_file / batch decompressor.
    """
    p = path.expanduser()
    if not p.is_file():
        return {"success": False, "error": f"File not found: {p}"}

    raw_file = p.read_bytes()
    magic = int.from_bytes(raw_file[:4].ljust(4, b"\x00"), "little")

    r = decode_dki_bytes(raw_file)
    if not r.success:
        return {
            "success": False,
            "error": r.error or "decode failed",
            "analysis": {
                "file_size": len(raw_file),
                "magic_number": magic,
                "compression_type": SimpleNamespace(name="none"),
                "offsets": [],
            },
            "extracted_sections": [],
            "total_extracted_size": 0,
        }

    full_text, _ = _decode_text_from_bytes(r.raw_uncompressed)
    ct_name = r.strategy_used or "zlib_autodetect"
    offsets: list[int] = []
    if r.strategy_used and "offset_0x" in r.strategy_used:
        try:
            hex_part = r.strategy_used.split("offset_0x")[1]
            offsets.append(int(hex_part.split("_")[0], 16))
        except (ValueError, IndexError):
            pass

    return {
        "success": True,
        "analysis": {
            "file_size": len(raw_file),
            "magic_number": magic,
            "compression_type": SimpleNamespace(name=ct_name),
            "offsets": offsets,
        },
        "extracted_sections": [{"records": [{"text_content": full_text}]}],
        "total_extracted_size": len(full_text.encode("utf-8", errors="replace")),
        "encoding": r.encoding_guess,
    }


# Default library roots (DBxxx volumes). Override with env DIGITALE_BIBLIOTHEK_ROOT.
DEFAULT_DIGITALE_LIBRARY_ROOTS: tuple[Path, ...] = (
    Path(r"L:\Multimedia Files\Written Word\Digitale Bibliothek"),
)


def resolve_digitale_library_root(explicit: str | None) -> tuple[Path | None, list[str]]:
    """Resolve Digitale Bibliothek install / library folder containing DB* volume dirs."""
    tried: list[str] = []
    if explicit:
        p = Path(os.path.expandvars(explicit)).expanduser()
        rp = p.resolve()
        tried.append(str(rp))
        if p.is_dir():
            return rp, tried
        return None, tried

    env = (os.environ.get("DIGITALE_BIBLIOTHEK_ROOT") or "").strip()
    if env:
        p = Path(os.path.expandvars(env)).expanduser()
        rp = p.resolve()
        tried.append(str(rp))
        if p.is_dir():
            return rp, tried

    for c in DEFAULT_DIGITALE_LIBRARY_ROOTS:
        rp = c.resolve()
        tried.append(str(rp))
        if c.is_dir():
            return rp, tried

    return None, tried
