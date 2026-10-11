"""Tests for the REA sidecar bridge (src/reversing_mcp/rea_bridge.py).

Subprocess/which fakes below are declared monkeypatch doubles (no live `rea`
or `npx` required) so the suite stays hermetic on CI / naked clones.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from reversing_mcp import rea_bridge


def test_resolve_kind_dir_and_asar(tmp_path: Path) -> None:
    d = tmp_path / "app"
    d.mkdir()
    assert rea_bridge.resolve_kind("auto", str(d)) == "javascript"
    asar = tmp_path / "app.asar"
    asar.write_bytes(b"asar")
    assert rea_bridge.resolve_kind("auto", str(asar)) == "javascript"
    exe = tmp_path / "prog.exe"
    exe.write_bytes(b"MZ")
    assert rea_bridge.resolve_kind("auto", str(exe)) == "native_overview"
    assert rea_bridge.resolve_kind("native_search", str(exe)) == "native_search"


def test_build_command_requires_args() -> None:
    argv, err = rea_bridge.build_command("native_search", "prog.exe")
    assert argv is None and "query" in (err or "")
    argv, err = rea_bridge.build_command("native_function", "prog.exe")
    assert argv is None and "symbol" in (err or "")
    argv, err = rea_bridge.build_command("native_decompile", "prog.exe")
    assert argv is None and "address" in (err or "")
    argv, err = rea_bridge.build_command("nope", "prog.exe")
    assert argv is None and "Unknown kind" in (err or "")


def test_build_command_shapes() -> None:
    argv, err = rea_bridge.build_command("javascript", "D:/apps/x")
    assert err is None and argv is not None and argv[0] == "analyze-javascript-application"
    argv, err = rea_bridge.build_command("native_search", "p.exe", provider="ghidra", query="search")
    assert err is None and argv is not None and argv[:3] == ["search", "p.exe", "search"]
    assert "--provider" in argv and "ghidra" in argv
    argv, err = rea_bridge.build_command("providers", None)
    assert err is None and argv == ["providers", "--json"]
    argv, err = rea_bridge.build_command("doctor", None, provider="hopper")
    assert err is None and argv == ["doctor", "--provider", "hopper", "--json"]


def test_run_rea_missing_target(tmp_path: Path) -> None:
    out = rea_bridge.run_rea("native_overview", str(tmp_path / "nope.exe"))
    assert not out["success"] and "not found" in out["error"]


def test_run_rea_no_runner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(rea_bridge.shutil, "which", lambda _name: None)
    out = rea_bridge.run_rea("providers")
    assert not out["success"] and "just setup-rea" in out["error"]
    assert rea_bridge.check_rea()["available"] is False


def _fake_proc(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["rea"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_run_rea_json_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(rea_bridge, "find_rea_runner", lambda: ["rea"])
    payload = {"ok": True, "modules": 3}
    monkeypatch.setattr(rea_bridge.subprocess, "run", lambda *a, **k: _fake_proc(stdout=json.dumps(payload)))
    target = tmp_path / "prog.exe"
    target.write_bytes(b"MZ")
    out = rea_bridge.run_rea("native_overview", str(target), provider="ghidra")
    assert out["success"] and out["result"] == payload and out["exit_code"] == 0


def test_run_rea_exit_1_maps_to_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rea_bridge, "find_rea_runner", lambda: ["rea"])
    monkeypatch.setattr(
        rea_bridge.subprocess, "run", lambda *a, **k: _fake_proc(stdout="{}", stderr="bad input", returncode=1)
    )
    out = rea_bridge.run_rea("providers")
    assert not out["success"] and out["exit_code"] == 1 and "bad input" in out["error"]


def test_run_rea_truncates_huge_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rea_bridge, "find_rea_runner", lambda: ["rea"])
    big = "x" * (rea_bridge.MAX_PARSE_BYTES + 1000)
    monkeypatch.setattr(rea_bridge.subprocess, "run", lambda *a, **k: _fake_proc(stdout=big))
    out = rea_bridge.run_rea("providers")
    assert out["success"] and out["truncated"] is True
    assert len(out["stdout_preview"]) == rea_bridge.PREVIEW_CHARS
    assert "snapshot_path" in out["hint"]


def test_run_rea_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rea_bridge, "find_rea_runner", lambda: ["rea"])

    def _boom(*a: object, **k: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="rea", timeout=1)

    monkeypatch.setattr(rea_bridge.subprocess, "run", _boom)
    out = rea_bridge.run_rea("providers", timeout_s=10)
    assert not out["success"] and "timed out" in out["error"]
