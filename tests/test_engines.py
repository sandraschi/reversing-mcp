"""Tests for engines.py (DiE, capa, Frida) and the `engine` MCP tool.

Real-engine tests skip when the tool is not installed; the Frida test spawns a
harmless `cmd /c type <tempfile>` and is marked integration.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

from reversing_mcp import engines
from reversing_mcp.server import engine

DIGIBIB = Path(__file__).parent / "fixtures" / "exe files" / "Digibib5.exe"


def test_summarize_capa_shape() -> None:
    """Shape copied from real capa 9.4 JSON (Digibib5 run, 2026-10-12)."""
    data = {
        "meta": {},
        "rules": {
            "check for unmoving mouse cursor": {
                "meta": {
                    "name": "check for unmoving mouse cursor",
                    "namespace": "anti-analysis/anti-vm/vm-detection",
                    "attack": [{"id": "T1497.002", "tactic": "Defense Evasion"}],
                    "mbc": [{"id": "B0009.012"}],
                },
                "source": "...",
                "matches": [[{"type": "absolute", "value": 4207312}, {}], [{"type": "absolute", "value": 1}, {}]],
            },
            "read file on Windows": {
                "meta": {"name": "read file on Windows", "namespace": "host-interaction/file-system/read"},
                "matches": [[{"type": "absolute", "value": 2}, {}]],
            },
        },
    }
    rows = engines.summarize_capa(data)
    assert [r["name"] for r in rows] == ["check for unmoving mouse cursor", "read file on Windows"]
    assert rows[0]["matches"] == 2
    assert rows[0]["attack"] == ["T1497.002"] and rows[0]["mbc"] == ["B0009.012"]
    assert rows[1]["attack"] == []


def test_trace_agent_embeds_hooks_and_filter() -> None:
    js = engines.build_trace_agent(["kernel32.dll!CreateFileW"], ".DKI")
    assert '["kernel32.dll!CreateFileW"]' in js
    assert '".dki"' in js  # filter is lowercased


def test_frida_trace_rejects_bad_specs() -> None:
    assert engines.frida_trace(["CreateFileW"])["success"] is False
    assert engines.frida_trace([])["success"] is False


def test_missing_file_is_honest() -> None:
    assert engines.run_die("Z:/nope/missing.exe")["success"] is False
    assert engines.run_capa("Z:/nope/missing.exe")["success"] is False


@pytest.mark.skipif(engines.find_diec() is None, reason="Detect It Easy not installed")
@pytest.mark.skipif(not DIGIBIB.is_file(), reason="Digibib5 fixture missing")
def test_run_die_identifies_delphi() -> None:
    r = engines.run_die(str(DIGIBIB))
    assert r["success"] is True
    assert r["packed"] is False
    assert any(d["name"] == "Borland Delphi" for d in r["detections"])


@pytest.mark.integration
@pytest.mark.skipif(sys.platform != "win32", reason="spawns cmd.exe")
@pytest.mark.skipif(not engines.check_frida()["available"], reason="frida not installed")
def test_frida_trace_catches_filtered_createfile() -> None:
    with tempfile.NamedTemporaryFile("w", suffix="_probe.dki", delete=False) as f:
        f.write("x")
        probe = f.name
    try:
        cmd = os.path.join(os.environ["SystemRoot"], "System32", "cmd.exe")
        r = engines.frida_trace(
            ["kernel32.dll!CreateFileW"], target=cmd, args=["/c", "type", probe], arg0_filter=".dki", duration_s=10
        )
    finally:
        os.unlink(probe)
    assert r["success"] is True, r
    assert r["hooked"] == ["kernel32.dll!CreateFileW"]
    assert r["event_count"] >= 1
    assert all(".dki" in (e.get("arg0") or "").lower() for e in r["events"])
    assert any(probe.lower() == (e.get("arg0") or "").lower() for e in r["events"])


def test_engine_tool_guards() -> None:
    frida = asyncio.run(engine(operation="frida_trace", target="C:/x.exe", functions=["a!b"]))
    assert frida["success"] is False and "confirm=True" in frida["error"]
    assert asyncio.run(engine(operation="die"))["success"] is False
    bad = asyncio.run(engine(operation="nope"))
    assert bad["success"] is False and "Valid" in bad["error"]
