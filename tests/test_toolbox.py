"""Tests for the autodiscovery toolbox (src/reversing_mcp/toolbox.py).

Hermetic: detectors run against monkeypatched env/process tables, installers
are never executed (dispatch + refusal paths only). No network, no spawns.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from reversing_mcp import toolbox


def test_probe_never_raises_and_covers_registry() -> None:
    out = toolbox.probe()
    assert out["success"] is True
    assert set(out["tools"]) == set(toolbox.DETECTORS)
    assert out["ready"] + (out["total"] - out["ready"]) == out["total"]
    for name, t in out["tools"].items():
        assert t["status"] in ("ready", "missing", "broken", "license", "platform_blocked", "installed"), name


def test_ida_gloms_running_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox, "_running_process", lambda names: {"pid": 4242, "exe": "C:/fake/ida64.exe"})
    out = toolbox.detect_ida()
    assert out["status"] == "ready" and out["pid"] == 4242


def test_ida_missing_without_instance_or_install(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(toolbox, "_running_process", lambda names: None)
    monkeypatch.setenv("IDA_DIR", str(tmp_path))
    for p in (r"C:\Program Files\IDA Pro 9.0\ida64.exe", r"C:\Program Files\IDA Free\ida.exe"):
        if Path(p).is_file():
            pytest.skip("real IDA install present - glom path covers this machine")
    out = toolbox.detect_ida()
    assert out["status"] == "missing" and "IDA_DIR" in out["note"]


def test_install_dispatch_and_refusals() -> None:
    assert toolbox.install("nope")["success"] is False
    ida = toolbox.install("ida")
    assert ida["success"] is False and "ONBOARDING" in ida["error"]
    hop = toolbox.install("hopper")
    assert hop["success"] is False
    assert set(toolbox.INSTALLERS) <= set(toolbox.DETECTORS)


def test_ollama_states(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import httpx

    class _Tags:
        status_code = 200

        def json(self):
            return {"models": [{"name": "m"}]}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Tags())
    assert toolbox.detect_ollama()["status"] == "ready"

    def _boom(*a, **k):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "get", _boom)
    # Hide every install trace so nothing can spawn: empty PATH lookup,
    # empty LOCALAPPDATA, no matching processes.
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(toolbox, "_running_process", lambda names: None)
    missing = toolbox.detect_ollama()
    assert missing["status"] == "missing" and "Ollama.Ollama" in (missing["install"] or "")
    assert toolbox.start_ollama()["success"] is False
    assert (
        toolbox.pull_ollama_model("evil;model")[  # odd names refused, never shelled
            "success"
        ]
        is False
    )


def test_policy_roundtrip() -> None:
    before = toolbox.get_policy()["policy"]
    try:
        out = toolbox.set_policy({"reva_headless": False, "nope": True})
        assert out["policy"]["reva_headless"] is False and "nope" not in out["policy"]
    finally:
        toolbox.set_policy(before)


def test_ensure_without_autostart_is_safe() -> None:
    before = toolbox.get_policy()["policy"]
    toolbox.set_policy({"reva_headless": False})
    try:
        out = toolbox.ensure(autostart=True)
        assert out["success"] is True and out["started"] == {}
        assert isinstance(out["ready"], int)
    finally:
        toolbox.set_policy(before)
