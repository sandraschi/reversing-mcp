"""IDA discovery and headless argv, against fake install folders (no IDA needed).

Folder names follow Hex-Rays installer defaults as far as known; real-install
verification is pending a licensed seat (docs/IDA.md).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from reversing_mcp import analyzers
from reversing_mcp.analyzers import BinaryAnalyzer


def _install(root: Path, folder: str, *exes: str) -> Path:
    d = root / folder
    d.mkdir(parents=True)
    for e in exes:
        (d / e).write_bytes(b"MZ")
    return d


@pytest.fixture
def roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("IDA_DIR", raising=False)
    monkeypatch.setattr(analyzers, "IDA_SEARCH_ROOTS", [tmp_path])
    return tmp_path


def _probe() -> dict[str, Any]:
    info: dict[str, Any] = {"available": False, "version": None, "path": None}
    BinaryAnalyzer()._check_ida(info)
    return info


def test_ida9_unified_idat(roots: Path) -> None:
    d = _install(roots, "IDA Professional 9.1", "ida.exe", "idat.exe")
    info = _probe()
    assert info["available"] is True
    assert info["path"] == str(d / "idat.exe") and info["headless"] is True
    assert info["version"] == "9.1" and info["edition"] == "pro"


def test_ida8_prefers_idat64_over_gui(roots: Path) -> None:
    d = _install(roots, "IDA Pro 8.3", "ida64.exe", "idat64.exe", "ida.exe")
    info = _probe()
    assert info["path"] == str(d / "idat64.exe") and info["version"] == "8.3"


def test_newest_install_wins(roots: Path) -> None:
    _install(roots, "IDA Pro 8.3", "idat64.exe")
    d9 = _install(roots, "IDA Professional 9.1", "idat.exe")
    assert _probe()["path"] == str(d9 / "idat.exe")


def test_free_only_is_not_available(roots: Path) -> None:
    _install(roots, "IDA Freeware 9.1", "ida.exe")
    info = _probe()
    assert info["available"] is False
    assert info["edition"] == "free" and "not usable for automation" in info["note"]


def test_free_and_home_picks_home(roots: Path) -> None:
    _install(roots, "IDA Freeware 9.1", "ida.exe")
    d = _install(roots, "IDA Home 9.0", "idat.exe")
    info = _probe()
    assert info["available"] is True and info["edition"] == "home"
    assert info["path"] == str(d / "idat.exe")


def test_ida_dir_env_first(roots: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install(roots, "IDA Professional 9.1", "idat.exe")
    custom = _install(tmp_path / "elsewhere", "IDA 9.2 custom", "idat.exe")
    monkeypatch.setenv("IDA_DIR", str(custom))
    assert _probe()["path"] == str(custom / "idat.exe")


def test_nothing_installed(roots: Path) -> None:
    assert _probe()["available"] is False


def test_headless_argv_has_no_literal_quotes(roots: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    d = _install(roots, "IDA Professional 9.1", "idat.exe")
    seen: dict[str, list[str]] = {}

    def fake_run(cmd: list[str], **_kw: Any) -> subprocess.CompletedProcess[str]:
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(analyzers.subprocess, "run", fake_run)
    a = BinaryAnalyzer()
    a.tools_cache = {"ida": {"available": True, "path": str(d / "idat.exe")}}
    target = str(tmp_path / "some dir" / "prog.exe")
    a._analyze_with_ida(target)
    cmd = seen["cmd"]
    assert cmd[0].endswith("idat.exe") and cmd[1] == "-A"
    assert cmd[2].startswith("-S") and '"' not in cmd[2]
    assert cmd[3] == target
