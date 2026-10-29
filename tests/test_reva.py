"""Tests for ReVa lifecycle management (src/reversing_mcp/reva.py).

Hermetic: no process is ever spawned (Popen stubbed), no bridge needed
(bridge-down is an asserted honest outcome, not a skip). The managed-process
registry is reset per test.
"""

from __future__ import annotations

from typing import Any

import pytest

from reversing_mcp import reva


@pytest.fixture(autouse=True)
def clean_registry():
    reva._PROC = None
    reva._MODE = None
    yield
    reva._PROC = None
    reva._MODE = None


class _StubProc:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.pid = 1234

    def poll(self) -> None:
        return None


def test_probe_never_raises_and_has_keys() -> None:
    out = reva.probe("http://127.0.0.1:9")
    assert set(out) >= {"mcp_reva", "ghidra", "managed", "bridge", "message"}
    assert out["bridge"]["reachable"] is False
    assert out["managed"]["running"] is False


def test_start_needs_confirm() -> None:
    out = reva.start(mode="headless", confirm=False)
    assert out["success"] is False and "confirm" in out["error"]


def test_start_headless_without_binary_is_honest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reva, "find_mcp_reva", lambda: None)
    out = reva.start(mode="headless", confirm=True)
    assert out["success"] is False
    assert out["error_type"] == "dependency_missing"
    assert out["dependency"] == "reva"
    assert out["mitigation"]["docs"] == "docs/REVA.md"


def test_start_gui_without_ghidra_is_honest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reva, "find_ghidra_run", lambda: {"dir": None, "run_bat": None, "gui_available": False})
    out = reva.start(mode="gui", confirm=True)
    assert out["success"] is False and "GHIDRA_INSTALL_DIR" in out["error"]


def test_start_busy_and_stop_kills_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reva, "find_mcp_reva", lambda: "mcp-reva")
    monkeypatch.setattr(reva, "find_ghidra_run", lambda: {"dir": "C:/ghidra", "run_bat": None, "gui_available": False})
    monkeypatch.setattr(reva.subprocess, "Popen", _StubProc)
    killed: list[int] = []
    monkeypatch.setattr(reva.engines, "kill_tree", lambda pid: killed.append(pid))
    first = reva.start(mode="headless", confirm=True, bridge_url="http://127.0.0.1:8089")
    assert first["success"] and first["pid"] == 1234
    busy = reva.start(mode="headless", confirm=True)
    assert busy["success"] is False and busy.get("busy") is True
    stopped = reva.stop()
    assert stopped["success"] and killed == [1234]
    again = reva.stop()
    assert again["success"] and "nothing to stop" in again["message"]


def test_status_wraps_probe() -> None:
    out = reva.status("http://127.0.0.1:9")
    assert out["success"] is True and "mcp_reva" in out
