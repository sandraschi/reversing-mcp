"""Tests for built-in Directmedia .DKI heuristic decoder."""

from __future__ import annotations

import zlib
from pathlib import Path

import pytest

from reversing_mcp.directmedia_dki import (
    decode_dki_bytes,
    decode_dki_path,
    legacy_extract_for_server,
    resolve_digitale_library_root,
)


def test_decode_plain_zlib_payload() -> None:
    plain = b"The quick brown fox jumps.\n" * 80
    blob = zlib.compress(plain)
    r = decode_dki_bytes(blob)
    assert r.success
    assert r.strategy_used == "zlib_whole"
    assert b"quick brown fox" in r.raw_uncompressed


def test_decode_zlib_after_header() -> None:
    plain = b"Digitale Bibliothek TEXT payload " * 50
    blob = b"DKIHEAD\x00" + zlib.compress(plain)
    r = decode_dki_bytes(blob)
    assert r.success
    assert "skip" in (r.strategy_used or "")
    assert b"TEXT payload" in r.raw_uncompressed


def test_decode_random_fails() -> None:
    r = decode_dki_bytes(b"\x00" * 200 + b"not zlib here" * 20)
    assert not r.success
    assert r.error


def test_legacy_extract_success(tmp_path: Path) -> None:
    p = tmp_path / "t.dki"
    plain = (b"Hello Directmedia " * 60).decode().encode("utf-8")
    p.write_bytes(zlib.compress(plain))
    leg = legacy_extract_for_server(p)
    assert leg["success"]
    assert leg["extracted_sections"][0]["records"][0]["text_content"].startswith(
        "Hello Directmedia"
    )


def test_decode_dki_path_missing(tmp_path: Path) -> None:
    r = decode_dki_path(tmp_path / "nope.dki")
    assert not r.success


def test_resolve_digitale_explicit_ok(tmp_path: Path) -> None:
    d = tmp_path / "lib"
    d.mkdir()
    r, tried = resolve_digitale_library_root(str(d))
    assert r is not None
    assert r.resolve() == d.resolve()
    assert str(d.resolve()) in tried


def test_resolve_digitale_explicit_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    r, tried = resolve_digitale_library_root(str(missing))
    assert r is None
    assert tried


def test_resolve_digitale_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    d = tmp_path / "fromenv"
    d.mkdir()
    monkeypatch.setenv("DIGITALE_BIBLIOTHEK_ROOT", str(d))
    r, _ = resolve_digitale_library_root(None)
    assert r is not None
    assert r.resolve() == d.resolve()
