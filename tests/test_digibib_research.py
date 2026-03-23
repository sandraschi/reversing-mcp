"""Tests for Digibib5 / Directmedia static research helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path

from reversing_mcp.analyzers import BinaryAnalyzer, StringResult
from reversing_mcp.digibib_research import (
    DEFAULT_DIGIBIB_CANDIDATES,
    build_research_snapshot,
    filter_directmedia_strings,
    resolve_digibib_exe,
)


def test_filter_directmedia_strings_keyword_hit():
    strings = [
        StringResult(offset=10, string="MyDecompressorRoutine", encoding="ascii", length=21),
        StringResult(offset=20, string="no match here", encoding="ascii", length=13),
    ]
    hits = filter_directmedia_strings(strings)
    assert len(hits) == 1
    assert hits[0]["keyword_hit"] == "Decompress"
    assert hits[0]["offset"] == 10


def test_resolve_digibib_exe_explicit_missing():
    p, tried = resolve_digibib_exe("__definitely_missing__.exe")
    assert p is None
    assert len(tried) == 1


def test_resolve_digibib_exe_explicit_happy():
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
        f.write(b"MZ")
        path = f.name
    try:
        p, tried = resolve_digibib_exe(path)
        assert p is not None
        assert p == Path(path).resolve()
        assert tried == [str(Path(path).resolve())]
    finally:
        Path(path).unlink(missing_ok=True)


def test_build_research_snapshot_minimal_pe(tmp_path: Path):
    # Small .exe-shaped file; PE parse may fail but snapshot still runs on strings/entropy
    pe_stub = tmp_path / "stub.exe"
    pe_stub.write_bytes(b"MZplaceholder-not-a-real-pe-but-long-enough-for-strings\x00")

    analyzer = BinaryAnalyzer()
    snap = build_research_snapshot(analyzer, pe_stub)
    assert snap.get("success") is True
    assert snap["exe_path"] == str(pe_stub.resolve())
    assert "entropy" in snap
    assert "directmedia_string_hits" in snap


def test_default_fixture_path_documented():
    assert any("Digibib5.exe" in str(p) for p in DEFAULT_DIGIBIB_CANDIDATES)
