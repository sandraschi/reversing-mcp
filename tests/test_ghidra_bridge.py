"""Ghidra forwarding bridge: lifecycle, discovery and forwarding against a fake ReVa.

The agent always drives through a stdio mcp-reva child. These tests swap the
StdioTransport for an in-memory FastMCP server standing in for mcp-reva, and
stub the mcp-reva/Ghidra discovery so start's guards pass, so the real Client
session path is exercised without a JVM or a running Ghidra.
"""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import FastMCP

from reversing_mcp import ghidra_bridge as gb


def _fake_reva() -> FastMCP:
    srv = FastMCP("fake-reva")

    @srv.tool
    def get_functions(programPath: str) -> str:
        """List functions in a program.

        Second line that should not appear in the summary."""
        return f"main @ 0x401000 in {programPath}"

    @srv.tool
    def get_decompilation(functionName: str) -> str:
        """Decompile one function to C pseudocode."""
        return "int main(void) {\n  return 0;\n}" + ("/" * 200)

    @srv.tool
    def boom() -> str:
        """Always fails."""
        raise ValueError("kaputt")

    return srv


async def _wait_ready(bridge: gb.GhidraBridge, timeout: float = 10.0) -> dict:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        st = bridge.status()
        if st["state"] in ("ready", "error"):
            return st
        await asyncio.sleep(0.05)
    raise AssertionError(f"bridge never settled: {bridge.status()}")


@pytest.fixture
def fake_reva(monkeypatch):
    """Make start() succeed its guards and connect to an in-memory ReVa."""
    server = _fake_reva()
    # StdioTransport(command=..., args=..., env=..., keep_alive=..., log_file=...)
    # is what the bridge builds; the fake ignores the kwargs and is a valid
    # Client transport (FastMCP in-memory) in its place.
    monkeypatch.setattr(gb, "StdioTransport", lambda **kw: server)
    monkeypatch.setattr(gb._reva, "find_mcp_reva", lambda: "C:/fake/mcp-reva.exe")
    monkeypatch.setattr(gb._reva, "find_ghidra_run", lambda: {"dir": "C:/fake/ghidra"})
    return server


def test_headless_session_full_cycle(fake_reva, monkeypatch):
    monkeypatch.setattr(gb, "MAX_TEXT_CHARS", 40)

    async def run():
        b = gb.GhidraBridge()
        started = await b.start("headless", confirm=True)
        assert started["success"] and started["state"] == "starting"
        assert started["gui_window"] is False

        st = await _wait_ready(b)
        assert st["state"] == "ready", st
        assert st["tool_count"] == 3
        assert st["gui_window"] is False

        busy = await b.start("headless", confirm=True)
        assert busy["success"] is False and busy["busy"] is True

        listing = b.list_tools("functions")
        assert listing["total"] == 1
        assert listing["tools"][0]["name"] == "get_functions"
        assert listing["tools"][0]["summary"] == "List functions in a program."

        page = b.list_tools(None, offset=0, limit=2)
        assert page["total"] == 3 and len(page["tools"]) == 2 and page["next_offset"] == 2

        desc = b.describe("get_functions")
        assert desc["success"] and "programPath" in desc["input_schema"]["properties"]

        miss = b.describe("functions")
        assert miss["success"] is False and "get_functions" in miss["did_you_mean"]

        res = await b.call("get_functions", {"programPath": "/prog.exe"})
        assert res["success"], res
        assert res["content"][0]["text"] == "main @ 0x401000 in /prog.exe"

        big = await b.call("get_decompilation", {"functionName": "main"})
        assert big["success"] and len(big["content"][0]["text"]) == 40
        assert big["content"][0]["truncated_from"] > 40 and "note" in big

        err = await b.call("boom", {})
        assert err["success"] is False and "kaputt" in err["content"][0]["text"]

        unknown = await b.call("nope", {})
        assert unknown["success"] is False

        stopped = await b.stop()
        assert stopped["success"] and "terminated" in stopped["message"]
        assert b.status()["state"] == "stopped"
        assert (await b.stop())["message"].startswith("No Ghidra session")

    asyncio.run(run())


def test_watch_mode_opens_and_closes_window(fake_reva, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        gb._reva, "start", lambda mode, confirm, bridge_url: calls.append(f"start:{mode}") or {"success": True}
    )
    monkeypatch.setattr(gb._reva, "stop", lambda: calls.append("stop") or {"success": True})

    async def run():
        b = gb.GhidraBridge()
        started = await b.start("watch", confirm=True)
        assert started["success"] and started["gui_window"] is True
        assert "start:gui" in calls

        st = await _wait_ready(b)
        assert st["state"] == "ready" and st["gui_window"] is True

        stopped = await b.stop()
        assert stopped["success"] and "window closed" in stopped["message"]
        assert "stop" in calls

    asyncio.run(run())


def test_watch_window_failure_is_nonfatal(fake_reva, monkeypatch):
    """A Ghidra window that won't open must not block the stdio session."""
    monkeypatch.setattr(gb._reva, "start", lambda mode, confirm, bridge_url: {"success": False, "error": "no GUI here"})

    async def run():
        b = gb.GhidraBridge()
        started = await b.start("watch", confirm=True)
        assert started["success"] and started["gui_window"] is False
        assert "Ghidra window did not open" in started["message"]
        st = await _wait_ready(b)
        assert st["state"] == "ready"
        await b.stop()

    asyncio.run(run())


def test_not_ready_and_validation():
    async def run():
        b = gb.GhidraBridge()
        assert b.status()["state"] == "stopped" and "hint" in b.status()
        for out in (b.list_tools(), b.describe("x"), await b.call("x", {})):
            assert out["success"] is False and out["state"] == "stopped"
        refused = await b.start("headless", confirm=False)
        assert refused["success"] is False and "confirm=True" in refused["error"]
        bad = await b.start("telepathy", confirm=True)
        assert bad["success"] is False and "Unknown mode" in bad["error"]

    asyncio.run(run())


def test_gui_alias_maps_to_watch(fake_reva, monkeypatch):
    """mode='gui' is accepted as an alias for watch (back-compat)."""
    monkeypatch.setattr(gb._reva, "start", lambda mode, confirm, bridge_url: {"success": True})
    monkeypatch.setattr(gb._reva, "stop", lambda: {"success": True})

    async def run():
        b = gb.GhidraBridge()
        started = await b.start("gui", confirm=True)
        assert started["success"] and started["mode"] == "watch"
        await _wait_ready(b)
        await b.stop()

    asyncio.run(run())


def test_connect_failure_reports_error(monkeypatch):
    class Broken:
        async def __aenter__(self):
            raise ConnectionError("mcp-reva did not come up")

        async def __aexit__(self, *a):
            return False

        async def close(self):
            return None

        def is_connected(self):
            return False

    monkeypatch.setattr(gb, "StdioTransport", lambda **kw: object())
    monkeypatch.setattr(gb, "Client", lambda *a, **kw: Broken())
    monkeypatch.setattr(gb._reva, "find_mcp_reva", lambda: "C:/fake/mcp-reva.exe")
    monkeypatch.setattr(gb._reva, "find_ghidra_run", lambda: {"dir": "C:/fake/ghidra"})

    async def run():
        b = gb.GhidraBridge()
        out = await b.start("headless", confirm=True)
        assert out["success"] and out["state"] == "starting"
        st = await _wait_ready(b, timeout=20.0)
        assert st["state"] == "error"
        assert "mcp-reva failed to come up" in st["error"]
        assert b.list_tools()["success"] is False
        assert (await b.stop())["success"]

    asyncio.run(run())


def test_headless_missing_launcher(monkeypatch):
    monkeypatch.setattr(gb._reva, "find_mcp_reva", lambda: None)

    async def run():
        out = await gb.GhidraBridge().start("headless", confirm=True)
        assert out["success"] is False and "mcp-reva not found" in out["error"]

    asyncio.run(run())


def test_missing_ghidra_dir(monkeypatch):
    monkeypatch.setattr(gb._reva, "find_mcp_reva", lambda: "C:/fake/mcp-reva.exe")
    monkeypatch.setattr(gb._reva, "find_ghidra_run", lambda: {"dir": None})

    async def run():
        out = await gb.GhidraBridge().start("headless", confirm=True)
        assert out["success"] is False and "GHIDRA_INSTALL_DIR" in out["error"]

    asyncio.run(run())
