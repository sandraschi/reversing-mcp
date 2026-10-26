"""Ghidra forwarding bridge: lifecycle, discovery and forwarding against a fake ReVa.

The fake is an in-memory FastMCP server standing in for ReVa, swapped in for the
GUI transport, so these tests exercise the real Client session path without a
JVM or a running Ghidra.
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
def fake_gui(monkeypatch):
    server = _fake_reva()
    monkeypatch.setattr(gb, "StreamableHttpTransport", lambda url: server)
    return server


def test_gui_session_full_cycle(fake_gui, monkeypatch):
    monkeypatch.setattr(gb, "MAX_TEXT_CHARS", 40)

    async def run():
        b = gb.GhidraBridge()
        started = await b.start("gui", "http://fake/mcp/message")
        assert started["success"] and started["state"] == "starting"

        st = await _wait_ready(b)
        assert st["state"] == "ready", st
        assert st["tool_count"] == 3
        assert st["target"] == "http://fake/mcp/message"

        busy = await b.start("gui")
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
        assert stopped["success"] and "Detached" in stopped["message"]
        assert b.status()["state"] == "stopped"
        assert (await b.stop())["message"].startswith("No Ghidra session")

    asyncio.run(run())


def test_not_ready_and_validation():
    async def run():
        b = gb.GhidraBridge()
        assert b.status()["state"] == "stopped" and "hint" in b.status()
        for out in (b.list_tools(), b.describe("x"), await b.call("x", {})):
            assert out["success"] is False and out["state"] == "stopped"
        refused = await b.start("headless", confirm=False)
        assert refused["success"] is False and "confirm=True" in refused["error"]
        bad = await b.start("telepathy")
        assert bad["success"] is False and "Unknown mode" in bad["error"]

    asyncio.run(run())


def test_gui_unreachable_reports_error(monkeypatch):
    """Nothing listening: the real HTTP transport fails and status says why."""
    monkeypatch.setattr(gb, "INIT_TIMEOUT_S", 5.0)

    async def run():
        b = gb.GhidraBridge()
        out = await b.start("gui", "http://127.0.0.1:9/mcp/message")
        assert out["success"] and out["state"] == "starting"
        st = await _wait_ready(b, timeout=20.0)
        assert st["state"] == "error"
        assert "ReVa server enabled" in st["error"]
        assert b.list_tools()["success"] is False
        assert (await b.stop())["success"]

    asyncio.run(run())


def test_transport_construction_failure_is_structured(monkeypatch):
    class Broken:
        def __init__(self, url):
            raise ValueError("bad url")

    monkeypatch.setattr(gb, "StreamableHttpTransport", Broken)

    async def run():
        b = gb.GhidraBridge()
        out = await b.start("gui", "not a url")
        assert out["success"] is False and "bad url" in out["error"]
        assert b.status()["state"] == "stopped"

    asyncio.run(run())


def test_headless_missing_launcher(monkeypatch):
    monkeypatch.setattr(gb._reva, "find_mcp_reva", lambda: None)

    async def run():
        out = await gb.GhidraBridge().start("headless", confirm=True)
        assert out["success"] is False and "mcp-reva not found" in out["error"]

    asyncio.run(run())
