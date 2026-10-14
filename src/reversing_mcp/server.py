#!/usr/bin/env python3
"""
Reversing MCP Server - static binary analysis and Directmedia tools.

For interactive Ghidra analysis over MCP, run the ReVa (reverse-engineering-assistant)
server separately and connect it in your MCP client. See docs/GHIDRA.md and
CURSOR_HANDOFF.md in this repository.
"""

import asyncio
import json
import os
import tempfile
import time
from collections import deque
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastmcp import FastMCP
from prefab_ui.app import PrefabApp
from prefab_ui.components import Badge, Card, CardContent, CardHeader, CardTitle, Text
from pydantic import BaseModel, Field

from . import clickerlab as _clickerlab
from . import engines as _engines
from . import gym as _gym
from . import rea_bridge
from . import reva as _reva
from . import toolbox as _toolbox
from .analyzers import BinaryAnalyzer
from .digibib_research import build_research_snapshot, resolve_digibib_exe
from .directmedia_dki import (
    decode_dki_path,
    legacy_extract_for_server,
    resolve_digitale_library_root,
    result_to_mcp_dict,
)
from .logging_config import get_logger
from .transport import run_server

logger = get_logger("reversing_mcp")

# Built-in .DKI decoder (zlib/gzip heuristics); no external directmedia-mcp wheel required
directmedia_available = True

# Initialize MCP server
mcp = FastMCP("ReversingMCP", version="0.4.0")

_READ_ONLY = {"readonly": True}
_MUTATING = {}
_DESTRUCTIVE = {}

SKILLS_DIR = Path(__file__).parent / "skills"


class AnalysisResult(BaseModel):
    """Result of binary analysis"""

    tool: str = Field(description="Tool used for analysis")
    file_path: str = Field(description="Path to analyzed file")
    file_size: int = Field(description="File size in bytes")
    file_type: str = Field(description="Detected file type")
    architecture: str | None = Field(description="CPU architecture if detected")
    endianness: str | None = Field(description="Endianness (little/big)")
    analysis: dict[str, Any] = Field(description="Tool-specific analysis results")


class StringResult(BaseModel):
    """String extraction result"""

    offset: int = Field(description="Offset in file")
    string: str = Field(description="Extracted string")
    encoding: str = Field(description="String encoding")
    length: int = Field(description="String length")


# Global analyzer instances
analyzer = BinaryAnalyzer()


@mcp.tool(annotations=_READ_ONLY)
async def analyze_binary(
    file_path: Annotated[str, Field(description="Path to the binary file to analyze")],
    tools: Annotated[
        list[str] | None,
        Field(description="Tools to use (ida, ghidra, r2, binwalk, static). If None, uses all available."),
    ] = None,
) -> dict[str, Any]:
    """
    Analyze a binary file with multiple reverse engineering tools.

    ## Return Format
    {"file_path": str, "file_size": int, "tools_used": [str], "results": {tool: result}}

    ## Examples
    analyze_binary("file.exe", ["static", "strings"])
    analyze_binary("firmware.bin")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        results = await asyncio.to_thread(analyzer.analyze_file, file_path, tools)
        return {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "tools_used": list(results.keys()),
            "results": results,
            "message": f"Analyzed {file_path} with {len(results)} tool(s): {', '.join(results.keys())}.",
        }
    except Exception as e:
        logger.exception(f"Error analyzing {file_path}")
        return {"error": f"Analysis failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def extract_strings(
    file_path: Annotated[str, Field(description="Path to the binary file")],
    min_length: Annotated[int, Field(description="Minimum string length to extract")] = 4,
    encodings: Annotated[
        list[str] | None, Field(description="Encodings to try (ascii, utf-8, utf-16le, latin-1)")
    ] = None,
) -> list[dict[str, Any]]:
    """
    Extract strings from a binary file.

    ## Return Format
    [{"offset": int, "string": str, "encoding": str, "length": int}]

    ## Examples
    extract_strings("file.exe", min_length=8)
    extract_strings("file.bin", encodings=["ascii", "utf-16le"])
    """
    if not os.path.exists(file_path):
        return [{"error": f"File not found: {file_path}"}]

    if encodings is None:
        encodings = ["ascii", "utf-8", "utf-16le", "latin-1"]

    try:
        strings = await asyncio.to_thread(analyzer.extract_strings, file_path, min_length, encodings)
        return [s.model_dump() for s in strings]
    except Exception as e:
        logger.exception(f"Error extracting strings from {file_path}")
        return [{"error": f"String extraction failed: {e!s}"}]


@mcp.tool(annotations=_READ_ONLY)
async def get_hexdump(
    file_path: Annotated[str, Field(description="Path to the binary file")],
    offset: Annotated[int, Field(description="Starting offset in bytes")] = 0,
    length: Annotated[int, Field(description="Number of bytes to dump")] = 256,
) -> dict[str, Any]:
    """
    Get hexadecimal dump of a binary file.

    ## Return Format
    {"file_path": str, "offset": int, "length": int, "hexdump": str}

    ## Examples
    get_hexdump("file.exe", offset=0, length=512)
    get_hexdump("firmware.bin", offset=1024)
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        hexdump = await asyncio.to_thread(analyzer.get_hexdump, file_path, offset, length)
        return {
            "file_path": file_path,
            "offset": offset,
            "length": length,
            "hexdump": hexdump,
            "message": f"Hexdump of {file_path} at offset {offset} ({length} bytes).",
        }
    except Exception as e:
        logger.exception(f"Error getting hexdump for {file_path}")
        return {"error": f"Hexdump failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def analyze_entropy(
    file_path: Annotated[str, Field(description="Path to the binary file")],
    block_size: Annotated[int, Field(description="Block size for entropy calculation")] = 256,
) -> dict[str, Any]:
    """
    Analyze entropy of a binary file (detects compressed/encrypted sections).

    ## Return Format
    {"file_path": str, "block_size": int, "overall_entropy": float, "entropy_map": [...], "compressed_regions": [...], "random_regions": [...]}

    ## Examples
    analyze_entropy("file.exe")
    analyze_entropy("packed.bin", block_size=512)
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        entropy_data = await asyncio.to_thread(analyzer.analyze_entropy, file_path, block_size)
        return {
            "file_path": file_path,
            "block_size": block_size,
            "overall_entropy": entropy_data["overall"],
            "entropy_map": entropy_data["map"],
            "compressed_regions": entropy_data["compressed"],
            "random_regions": entropy_data["random"],
            "message": f"Entropy of {file_path}: {entropy_data['overall']:.2f} overall, "
            f"{len(entropy_data['compressed'])} compressed and {len(entropy_data['random'])} random regions.",
        }
    except Exception as e:
        logger.exception(f"Error analyzing entropy for {file_path}")
        return {"error": f"Entropy analysis failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def find_functions(
    file_path: Annotated[str, Field(description="Path to the binary file")],
    tool: Annotated[str, Field(description="Tool to use (ida, ghidra, r2, auto)")] = "auto",
) -> dict[str, Any]:
    """
    Find functions in a binary file.

    ## Return Format
    {"file_path": str, "tool_used": str, "functions": [...]}

    ## Examples
    find_functions("file.exe")
    find_functions("file.exe", tool="ghidra")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        functions = await asyncio.to_thread(analyzer.find_functions, file_path, tool)
        return {
            "file_path": file_path,
            "tool_used": tool,
            "functions": functions,
            "message": f"Found {len(functions)} function(s) in {file_path} via {tool}.",
        }
    except Exception as e:
        logger.exception(f"Error finding functions in {file_path}")
        return {"error": f"Function analysis failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def get_file_info(
    file_path: Annotated[str, Field(description="Path to the file to analyze")],
) -> dict[str, Any]:
    """
    Get basic information about a file.

    ## Return Format
    {"path": str, "size": int, "modified": float, "type": str, "permissions": str, "readable": bool, "writable": bool, "executable": bool}

    ## Examples
    get_file_info("file.exe")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        stat = os.stat(file_path)
        file_type = await asyncio.to_thread(analyzer.detect_file_type, file_path)
        return {
            "path": file_path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "type": file_type,
            "permissions": oct(stat.st_mode)[-3:],
            "readable": os.access(file_path, os.R_OK),
            "writable": os.access(file_path, os.W_OK),
            "executable": os.access(file_path, os.X_OK),
            "message": f"{file_path}: {stat.st_size} bytes, {file_type}.",
        }
    except Exception as e:
        logger.exception(f"Error getting file info for {file_path}")
        return {"error": f"File info failed: {e!s}"}


@mcp.resource("config://tools")
def _tools_resource() -> dict[str, Any]:
    """List available RE tools as a config resource."""
    return {"tools": analyzer.check_available_tools()}


@mcp.resource("skill://primary")
def _primary_skill_resource() -> str:
    """Reversing-expert skill content (skill-first chat preprompt)."""
    skill_path = SKILLS_DIR / "primary" / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return "Reversing MCP: static binary analysis (analyze_binary, extract_strings, get_hexdump, analyze_entropy, find_functions), PE/DKI tools, REA sidecar (rea_investigate). Triage with check_tools() then analyze_binary()."


@mcp.prompt()
def reversing_help(topic: str = "overview") -> str:
    """Get reversing guidance for a specific topic."""
    topics = {
        "pe": "PE files: check DOS header at offset 0, NT headers at offset 0x3C. Use analyze_pe_file().",
        "strings": "Strings: extract_strings() with min_length=8 filters noise. Check utf-16le for wide strings.",
        "entropy": "Entropy: analyze_entropy(). Values > 7.5 suggest compression/encryption; < 5 is plain text/code.",
        "dki": "DKI decode: decode_dki_file() for single files, decompress_directmedia_library() for batch.",
    }
    return topics.get(topic, "Use check_tools() then analyze_binary() for a full overview.")


@mcp.tool(annotations=_READ_ONLY)
async def check_tools() -> dict[str, Any]:
    """
    Check which reverse engineering tools are available on the system.

    ## Return Format
    {"tools": {name: {available: bool, version: str, path: str}}, "summary": {"total": int, "available": int, "recommended": [str], "premium": [str]}, "notes": {...}}

    ## Examples
    check_tools()
    """
    try:
        available_tools = await asyncio.to_thread(analyzer.check_available_tools)

        # Add Directmedia status
        available_tools["directmedia"] = {
            "name": "Directmedia DKI (built-in)",
            "available": directmedia_available,
            "version": "0.4",
            "description": "Heuristic zlib/gzip .DKI decode (analyze_directmedia_file, decode_dki_file)",
        }

        return {
            "tools": available_tools,
            "summary": {
                "total": len(available_tools),
                "available": len([t for t in available_tools.values() if t["available"]]),
                "recommended": ["ghidra", "r2", "binwalk"],
                "premium": ["ida"],
            },
            "message": f"{len([t for t in available_tools.values() if t['available']])}/{len(available_tools)} engines available.",
            "notes": {
                "ghidra_mcp": (
                    "Ghidra MCP is not bundled here. Install ReVa (reverse-engineering-assistant) "
                    "and add it to your MCP client; see docs/GHIDRA.md."
                ),
                "rea_sidecar": (
                    "REA (rea-agents) is an optional sidecar for JS/Electron, .NET, APK, firmware, "
                    "browser, and agent-driven native queries. Setup: just setup-rea, then restart "
                    "the agent. Query via rea_investigate(); guide: docs/REA.md."
                ),
                "directmedia_setup": "Install directmedia-mcp for .DKI file analysis",
                "digibib5": (
                    "Digitale Bibliothek 5: digibib_research_snapshot() for static prelude; "
                    "see docs/DIRECTMEDIA_REVERSING_TOOLKIT.md"
                ),
            },
        }
    except Exception as e:
        logger.exception("Error checking tools")
        return {"error": f"Tool check failed: {e!s}"}


@mcp.tool(app=True, annotations={"readOnlyHint": True, "openWorldHint": False})
async def show_tools_card() -> PrefabApp:
    """
    SHOW_TOOLS_CARD - Engine inventory as an in-chat Prefab card.

    Fleet Prefab pattern (cf. arxiv-mcp depot cards): status-class tools render
    inline instead of returning raw dicts. check_tools() remains the
    machine-readable twin.

    ## Return Format
    PrefabApp card rendered inline in the conversation (title + per-engine badges).

    ## Examples
    `show_tools_card()` -> PrefabApp with available/missing engine badges.
    """
    tools = await asyncio.to_thread(analyzer.check_available_tools)
    # css_class is a declared Component field (populate_by_name); pyright
    # misresolves the pydantic alias init - verified at runtime. See below.
    with Card(css_class="max-w-xl") as view:  # pyright: ignore[reportCallIssue]
        with CardHeader():
            CardTitle("Reversing engines")
        with CardContent():
            for key, info in tools.items():
                ok = bool(info.get("available"))
                Badge("available" if ok else "missing", variant="secondary")
                Text(f"{info.get('name', key)}", css_class="text-sm mt-2")
                detail = info.get("version") or info.get("path") or ""
                if detail:
                    Text(str(detail)[:120], css_class="text-xs text-muted-foreground break-all")
    return PrefabApp(view=view, title="Reversing engines")


@mcp.tool(annotations=_MUTATING)
async def gym(
    operation: Annotated[
        str,
        Field(
            description="Gym op: start, status, advance, stop, list, elicit, clicker_start, clicker_status, clicker_stop, correlate."
        ),
    ] = "list",
    run_id: Annotated[str | None, Field(description="Run id (status/advance/stop/elicit/clicker_*).")] = None,
    target: Annotated[str | None, Field(description="Local .exe/.lnk path (start).")] = None,
    test_files: Annotated[list[str] | None, Field(description="Test data files (start).")] = None,
    notes: Annotated[str, Field(description="Operator notes (start).")] = "",
    decision: Annotated[str | None, Field(description="Gate decision: go|no-go (advance at gate).")] = None,
    session_id: Annotated[str | None, Field(description="Clicker session id (clicker_status/clicker_stop).")] = None,
    mode: Annotated[str, Field(description="Clicker mode: rip (B1 BFS) or tour (B2 draft executor).")] = "rip",
    tour_rel: Annotated[
        str | None,
        Field(description="Run-relative tour YAML (clicker_start tour mode, e.g. elicitation/tour-draft.yaml)."),
    ] = None,
    step_cap: Annotated[int, Field(description="Max driver actions per clicker session.")] = 200,
    time_cap_s: Annotated[int, Field(description="Wall-clock cap per clicker session (seconds).")] = 600,
    confirm: Annotated[
        bool,
        Field(description="Required true for clicker_start / oracle advance: executes the target binary."),
    ] = False,
    accept_local: Annotated[
        bool,
        Field(
            description="Required true for clicker_start / oracle advance: logged opt-out from VM isolation (spec section 1)."
        ),
    ] = False,
    duration_s: Annotated[
        int, Field(description="Oracle capture duration in seconds (advance into oracle_capture).")
    ] = 60,
) -> dict[str, Any]:
    """
    GYM - Drive a Reversing Gym cloning run (stages 0/1/4 in G1) + ClickerLab (1b/3).

    PORTMANTEAU PATTERN RATIONALE: One entry for the whole run lifecycle so agents
    can triage a clone candidate without learning five endpoints. `advance` starts the
    next stage in a background worker and returns at once (`status: "running"`); poll
    `status` until `running_stage` is null. Stages are resumable: failed, stopped or
    interrupted (backend restarted) stages are retried by the next `advance`.

    ClickerLab: `elicit` builds stage-1b artifacts (format stubs, features.json,
    tour draft, prior-art leads - static, no execution). `clicker_start` launches a
    stage-3 session (rip = B1 UIA BFS, tour = B2 draft executor); it executes the
    target, so it needs confirm=True plus accept_local=True (logged VM opt-out),
    and `clicker_stop` kills the target tree. Needs `uv sync --extra clicker`.

    ## Return Format
    `{"success": bool, "run_id"?, "stage"?, "message"?, ...stage payload}`.
    `advance` while a stage runs -> `{success: False, busy: True, stage}`. `stop` marks the
    running stage stopped and kills the engine's process tree (DiE / capa) within about a
    second. Advance past assessment requires `decision="go"|"no-go"`. Advancing
    into oracle_capture executes the target: needs confirm=True +
    accept_local=True (+duration_s); stages 3,5,6,7,8 refuse honestly
    (pending-spec) instead of pretending.

    ## Examples
    `gym(operation="start", target="D:/apps/prog.exe")`
    `gym(operation="advance", run_id="abc123")`
    `gym(operation="status", run_id="abc123")`
    `gym(operation="elicit", run_id="abc123")`
    `gym(operation="clicker_start", run_id="abc123", mode="rip", confirm=True, accept_local=True)`
    """
    op = (operation or "").lower()
    if op == "start":
        if not target:
            return {"success": False, "error": "start requires target (local .exe/.lnk path)."}
        return await asyncio.to_thread(_gym.create_run, target, test_files, notes)
    if op == "status":
        if not run_id:
            return {"success": False, "error": "status requires run_id."}
        return await asyncio.to_thread(_gym.get_run, run_id)
    if op == "advance":
        if not run_id:
            return {"success": False, "error": "advance requires run_id."}
        return await asyncio.to_thread(_gym.advance_run, run_id, decision, True, confirm, accept_local, duration_s)
    if op == "stop":
        if not run_id:
            return {"success": False, "error": "stop requires run_id."}
        return await asyncio.to_thread(_gym.stop_run, run_id)
    if op == "list":
        return await asyncio.to_thread(_gym.list_runs)
    if op == "elicit":
        if not run_id:
            return {"success": False, "error": "elicit requires run_id (and triage done)."}
        return await asyncio.to_thread(_clickerlab.elicit_run, run_id)
    if op == "clicker_start":
        if not run_id:
            return {"success": False, "error": "clicker_start requires run_id."}
        return await asyncio.to_thread(
            _clickerlab.clicker_start, run_id, mode, tour_rel, step_cap, time_cap_s, confirm, accept_local
        )
    if op == "clicker_status":
        if not run_id or not session_id:
            return {"success": False, "error": "clicker_status requires run_id and session_id."}
        return await asyncio.to_thread(_clickerlab.clicker_status, run_id, session_id)
    if op == "clicker_stop":
        if not run_id or not session_id:
            return {"success": False, "error": "clicker_stop requires run_id and session_id."}
        return await asyncio.to_thread(_clickerlab.clicker_stop, run_id, session_id)
    if op == "correlate":
        if not run_id or not session_id:
            return {"success": False, "error": "correlate requires run_id and session_id."}
        return await asyncio.to_thread(_clickerlab.correlate_session, run_id, session_id)
    return {
        "success": False,
        "error": (
            f"Unknown gym operation '{operation}'. "
            "Valid: start, status, advance, stop, list, elicit, clicker_start, clicker_status, clicker_stop, correlate."
        ),
    }


@mcp.tool(annotations=_MUTATING)
async def reva(
    operation: Annotated[str, Field(description="ReVa op: probe, start, stop.")] = "probe",
    mode: Annotated[str, Field(description="Start mode: headless (mcp-reva) or gui (Ghidra + plugin).")] = "headless",
    confirm: Annotated[bool, Field(description="Required true for start: spawns a JVM + MCP listener.")] = False,
) -> dict[str, Any]:
    """
    REVA - Probe and manage the ReVa Ghidra MCP server lifecycle.

    ReVa (reverse-engineering-assistant) is a separate server; this tool owns
    its process lifecycle so agents and the Status page share one path.
    `probe` reports mcp-reva presence, Ghidra dir, the managed process and
    bridge reachability (bridge-down is normal, not an error). `start` needs
    confirm=True; without mcp-reva/Ghidra it refuses with the install hint
    (docs/REVA.md). `stop` kills the managed tree and is idempotent.

    ## Return Format
    `{"success": bool, ...probe fields | pid/mode/message}`. Start while
    running -> `{success: False, busy: True, pid}`.

    ## Examples
    `reva(operation="probe")`
    `reva(operation="start", mode="headless", confirm=True)`
    `reva(operation="stop")`
    """
    op = (operation or "").lower()
    if op == "probe":
        return await asyncio.to_thread(_reva.status, _GHIDRA_BRIDGE_URL)
    if op == "start":
        return await asyncio.to_thread(_reva.start, mode, confirm, _GHIDRA_BRIDGE_URL)
    if op == "stop":
        return await asyncio.to_thread(_reva.stop)
    return {"success": False, "error": f"Unknown reva operation '{operation}'. Valid: probe, start, stop."}


@mcp.tool(annotations=_MUTATING)
async def toolbox(
    operation: Annotated[str, Field(description="Toolbox op: probe, install, ensure, policy.")] = "probe",
    name: Annotated[
        str | None, Field(description="Tool name for install (ghidra, reva, capa, die, frida, r2).")
    ] = None,
) -> dict[str, Any]:
    """
    TOOLBOX - Autodiscovery, install and autostart for the disassembly toolchain.

    [RATIONALE] One entry so agents stop hand-editing env and hand-installing
    engines: probe reports ghidra/reva/capa/die/frida/r2/hopper/ida/java/
    tesseract/node with ready/missing/broken states; install fetches the rest
    (winget, GitHub releases, pip venv); ensure re-runs boot discovery.
    IDA/Hopper: running instances are glommed onto; licensing is not checked.

    ## Return Format
    `{"success": bool, ...}` - probe adds `tools`, `ready`, `total`; install
    adds `tool` plus outcome.

    ## Examples
    `toolbox(operation="probe")`
    `toolbox(operation="install", name="capa")`
    `toolbox(operation="ensure")`
    """
    op = (operation or "").lower()
    if op == "probe":
        return await asyncio.to_thread(_toolbox.probe)
    if op == "install":
        if not name:
            return {"success": False, "error": "install requires name."}
        return await asyncio.to_thread(_toolbox.install, name)
    if op == "ensure":
        return await asyncio.to_thread(_toolbox.ensure, True)
    if op == "policy":
        return _toolbox.get_policy()
    return {
        "success": False,
        "error": f"Unknown toolbox operation '{operation}'. Valid: probe, install, ensure, policy.",
    }


@mcp.tool(annotations=_MUTATING)
async def engine(
    operation: Annotated[str, Field(description="Engine op: die, capa, frida_trace, frida_script.")] = "die",
    file_path: Annotated[str | None, Field(description="Binary to analyze (die, capa).")] = None,
    target: Annotated[str | None, Field(description="Executable to spawn (frida_*). Executes it!")] = None,
    args: Annotated[list[str] | None, Field(description="Command-line args for the spawned target.")] = None,
    pid: Annotated[int | None, Field(description="Attach to a running process instead of spawning.")] = None,
    functions: Annotated[
        list[str] | None, Field(description="Hooks as 'module!export', e.g. 'kernel32.dll!CreateFileW' (frida_trace).")
    ] = None,
    arg0_filter: Annotated[
        str | None, Field(description="Keep only calls whose arg 0 string contains this (frida_trace), e.g. '.dki'.")
    ] = None,
    source: Annotated[
        str | None, Field(description="Frida JS agent source; use send() for results (frida_script).")
    ] = None,
    duration_s: Annotated[int, Field(description="Session length 1-120 s (frida_*).")] = 10,
    max_events: Annotated[int, Field(description="Event cap 1-5000 (frida_*).")] = 2000,
    timeout_s: Annotated[int, Field(description="Engine timeout (die 5-300 s, capa 30-1800 s).")] = 600,
    confirm: Annotated[
        bool, Field(description="Required true for frida_*: spawning/attaching runs or instruments a process.")
    ] = False,
) -> dict[str, Any]:
    """
    ENGINE - Run an external RE engine: Detect It Easy, capa, or Frida.

    PORTMANTEAU PATTERN RATIONALE: Static identification (DiE: compiler/packer;
    capa: what the code can do) and dynamic tracing (Frida: what it actually does
    at runtime) are one triage toolbox. One tool keeps the surface small; each op
    is a thin wrapper over engines.py, run off the event loop.

    ## Return Format
    die: `{success, detections[{type,name,version,string}], packed, filetypes, message}`
    capa: `{success, capabilities[{name,namespace,matches,attack,mbc}], count, top_namespaces, message}`
    frida_*: `{success, mode, pid, events[], event_count, dropped, hooked, hook_errors, process_exited, elapsed_s}`
    Failure: `{success: False, error}` (missing engine -> install hint, see docs/ENGINES.md).

    ## Examples
    `engine(operation="die", file_path="D:/apps/prog.exe")`
    `engine(operation="capa", file_path="D:/apps/prog.exe", timeout_s=1800)`
    `engine(operation="frida_trace", target="D:/apps/prog.exe", functions=["kernel32.dll!CreateFileW"], arg0_filter=".dki", confirm=True)`

    ## Notes
    - capa is slow on large binaries (Digibib5 4.7 MB: ~42 min); raise timeout_s.
    - frida_* executes the target: VM or a target you trust only (docs/FRIDA.md).
    """
    op = (operation or "").lower()
    if op in ("die", "capa"):
        if not file_path:
            return {"success": False, "error": f"{op} requires file_path."}
        fn = _engines.run_die if op == "die" else _engines.run_capa
        return await asyncio.to_thread(fn, file_path, timeout_s)
    if op in ("frida_trace", "frida_script"):
        if not confirm:
            return {
                "success": False,
                "error": f"{op} spawns or instruments a process. Re-run with confirm=True (VM or trusted target only).",
            }
        if op == "frida_trace":
            return await asyncio.to_thread(
                _engines.frida_trace, functions or [], target, args, pid, arg0_filter, duration_s, max_events
            )
        return await asyncio.to_thread(_engines.frida_script, source or "", target, args, pid, duration_s, max_events)
    return {
        "success": False,
        "error": f"Unknown engine operation '{operation}'. Valid: die, capa, frida_trace, frida_script.",
    }


@mcp.tool(annotations=_READ_ONLY)
async def rea_investigate(
    target: Annotated[
        str | None,
        Field(
            description="Absolute path to target (binary, .asar, or app dir). Not needed for providers/capabilities/doctor."
        ),
    ] = None,
    kind: Annotated[
        str,
        Field(
            description="Query kind: auto, javascript, native_overview, native_search, native_function, native_decompile, native_xrefs, native_trace, providers, capabilities, doctor."
        ),
    ] = "auto",
    provider: Annotated[
        str | None, Field(description="Native provider: hopper, ghidra, ida. Omit for auto-select.")
    ] = None,
    query: Annotated[str | None, Field(description="Search text (native_search, native_trace).")] = None,
    symbol: Annotated[str | None, Field(description="Function name or address (native_function).")] = None,
    address: Annotated[str | None, Field(description="Address for decompile/xrefs (e.g. 0x1000, main).")] = None,
    snapshot_path: Annotated[str | None, Field(description="Snapshot file to read/write cached REA results.")] = None,
    timeout_s: Annotated[
        int, Field(description="Subprocess timeout 10-900s (default 180). Large binaries need more.")
    ] = 180,
) -> dict[str, Any]:
    """
    REA_INVESTIGATE - Delegate one query to the REA sidecar (`rea` CLI).

    PORTMANTEAU PATTERN RATIONALE: Single entry point for everything reversing-mcp
    does not do natively: JS/Electron app graphs, .NET/APK/firmware/browser targets,
    and agent-driven native pseudocode/search/xrefs via Hopper/Ghidra/IDA. Triage
    with analyze_binary() first, then hand off. Full guide: docs/REA.md.

    ## Return Format
    success=True: {success, kind, command, exit_code, stdout_bytes, result|result_text, truncated?, hint?}
    success=False: {success: False, error, kind, ...}. Large outputs truncate with a
    snapshot_path hint instead of parsing hundreds of MB into memory.

    ## Examples
    rea_investigate("D:/apps/notes", kind="javascript")
    rea_investigate("prog.exe", kind="native_overview", provider="ghidra")
    rea_investigate("prog.exe", kind="native_search", query="decrypt", provider="ghidra")
    rea_investigate(None, kind="providers")
    """
    if kind not in rea_bridge.REA_KINDS:
        return {"success": False, "error": f"Unknown kind '{kind}'. Valid: {', '.join(rea_bridge.REA_KINDS)}."}
    try:
        # Blocking subprocess (up to 900 s) - keep it off the event loop.
        out = await asyncio.to_thread(
            rea_bridge.run_rea,
            kind,
            target,
            provider=provider,
            query=query,
            symbol=symbol,
            address=address,
            snapshot_path=snapshot_path,
            timeout_s=timeout_s,
        )
        if out.get("success"):
            out["message"] = f"REA {out.get('kind')} complete (exit {out.get('exit_code', 0)})."
        return out
    except Exception as e:
        logger.exception(f"REA investigate failed for {target}")
        return {"success": False, "error": f"REA investigate failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def digibib_research_snapshot(exe_path: str | None = None) -> dict[str, Any]:
    """
    DIGIBIB_RESEARCH_SNAPSHOT - Static research bundle for Digibib5.exe / Directmedia viewer work.

    PORTMANTEAU PATTERN RATIONALE: Single entry point for the Digitale Bibliothek 5 mission:
    file metadata, PE summary, entropy, and keyword-filtered strings (DKI, decompress, …)
    before interactive Ghidra/ReVa decompilation.

    Args:
        exe_path: Optional absolute path to Digibib5.exe. If omitted, uses repo fixture
            tests/fixtures/exe files/Digibib5.exe then the standard Program Files install path.

    Returns:
        success, exe_path, file_info, directmedia_string_hits, counts, entropy, tools,
        next_steps, viewer_roadmap; or error + paths_searched when not found.

    Examples:
        digibib_research_snapshot()
        digibib_research_snapshot("D:\\\\Dev\\\\repos\\\\reversing-mcp\\\\tests\\\\fixtures\\\\exe files\\\\Digibib5.exe")
    """
    resolved, tried = resolve_digibib_exe(exe_path)
    if resolved is None:
        return {
            "success": False,
            "error": "Digibib5.exe not found",
            "paths_searched": tried,
            "hint": "Copy Digibib5.exe into tests/fixtures/exe files/ or pass exe_path.",
        }
    try:
        snap = await asyncio.to_thread(build_research_snapshot, analyzer, resolved)
        snap["message"] = f"Digibib snapshot for {resolved} complete."
        return snap
    except Exception as e:
        logger.exception("digibib_research_snapshot failed")
        return {"success": False, "error": f"Snapshot failed: {e!s}", "exe_path": str(resolved)}


@mcp.tool(annotations=_READ_ONLY)
async def analyze_pe_file(
    file_path: Annotated[str, Field(description="Path to the PE file")],
) -> dict[str, Any]:
    """
    Analyze a Windows PE (Portable Executable) file.

    ## Return Format
    {"file_path": str, "pe_info": {...}}

    ## Examples
    analyze_pe_file("file.exe")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        pe_info = await asyncio.to_thread(analyzer.analyze_pe_file, file_path)
        return {
            "file_path": file_path,
            "pe_info": pe_info,
            "message": f"PE analysis of {file_path} complete ({pe_info.get('num_sections', '?')} sections).",
        }
    except Exception as e:
        logger.exception(f"Error analyzing PE file {file_path}")
        return {"error": f"PE analysis failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def decode_dki_file(
    file_path: Annotated[str, Field(description="Path to a .DKI (e.g. volume Data/TEXT.DKI)")],
) -> dict[str, Any]:
    """
    DECODE_DKI_FILE - Decompress a Directmedia .DKI using built-in zlib/gzip autodetection.

    PORTMANTEAU PATTERN RATIONALE: Explicit decode report (strategy, preview, attempts) without
    also writing sidecar .txt files.

    ## Return Format
    {"success": bool, "strategy_used": str, "encoding_guess": str, "text_preview": str, "attempts": [...]} or {"success": False, "error": str}

    ## Examples
    decode_dki_file("C:/DB001/Data/TEXT.DKI")
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}
    r = await asyncio.to_thread(decode_dki_path, Path(file_path))
    out = result_to_mcp_dict(file_path, r)
    out["message"] = f"DKI decode of {file_path}: {'success' if out.get('success') else 'failed'}."
    return out


@mcp.tool(annotations=_MUTATING)
async def analyze_directmedia_file(
    file_path: Annotated[str, Field(description="Path to the .DKI file to analyze")],
) -> dict[str, Any]:
    """
    Analyze a Directmedia .DKI file and extract text content.

    Uses the in-repo heuristic decoder (zlib/gzip / header skip). Writes *_extracted.txt
    next to the .DKI on success.

    ## Return Format
    {"file_path": str, "analysis": {...}, "extraction_summary": {...}, "sample_content": [str], "output_file": str, "extraction_status": str} or {"error": str}

    ## Examples
    analyze_directmedia_file("C:/DB001/Data/TEXT.DKI")
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        result = legacy_extract_for_server(Path(file_path))
        if not result.get("success"):
            return {
                "error": result.get("error", "DKI decode failed"),
                "file_path": file_path,
                "extraction_status": "failed",
            }

        # Format the response for MCP
        response = {
            "file_path": file_path,
            "analysis": {
                "file_size": result["analysis"]["file_size"],
                "magic_number": f"0x{result['analysis']['magic_number']:08x}",
                "compression_type": result["analysis"]["compression_type"].name,
                "offsets_found": len(result["analysis"]["offsets"]),
            },
            "extraction_summary": {
                "sections_processed": len(result["extracted_sections"]),
                "total_text_bytes": result["total_extracted_size"],
            },
        }

        # Add sample extracted content
        if result["extracted_sections"]:
            samples = []
            for section in result["extracted_sections"][:3]:
                if section.get("records"):
                    for record in section["records"][:2]:
                        text = record.get("text_content", "")
                        if text and len(text) > 10:
                            samples.append(text[:200] + "..." if len(text) > 200 else text)

            if samples:
                response["sample_content"] = samples

        # Save extracted content to file
        output_file = Path(file_path).parent / f"{Path(file_path).stem}_extracted.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Directmedia Decompression Results for {file_path}\n")
            f.write("=" * 60 + "\n\n")
            f.write("Analysis Summary:\n")
            f.write(f"- File size: {result['analysis']['file_size']:,} bytes\n")
            f.write(f"- Magic number: 0x{result['analysis']['magic_number']:08x}\n")
            f.write(f"- Compression type: {result['analysis']['compression_type'].name}\n")
            f.write(f"- Offsets found: {len(result['analysis']['offsets'])}\n")
            f.write(f"- Sections extracted: {len(result['extracted_sections'])}\n")
            f.write(f"- Total text bytes: {result['total_extracted_size']:,}\n\n")

            # Write all extracted text
            all_text_parts = []
            for section in result["extracted_sections"]:
                if section.get("records"):
                    for record in section["records"]:
                        text = record.get("text_content", "")
                        if text and len(text) > 5:
                            all_text_parts.append(text)

            if all_text_parts:
                f.write("EXTRACTED TEXT CONTENT:\n")
                f.write("-" * 30 + "\n\n")
                for i, text in enumerate(all_text_parts, 1):
                    f.write(f"[{i}] {text}\n\n")

        response["output_file"] = str(output_file)
        response["extraction_status"] = "success"
        response["message"] = (
            f"Extracted {result['total_extracted_size']:,} text bytes from "
            f"{len(result['extracted_sections'])} section(s) of {file_path}."
        )

        return response

    except Exception as e:
        logger.exception(f"Error analyzing Directmedia file {file_path}")
        return {"error": f"Directmedia analysis failed: {e!s}"}


@mcp.tool(annotations=_MUTATING)
async def decompress_directmedia_library(
    library_path: Annotated[
        str | None,
        Field(
            description="Path to Directmedia library directory (DB* folders). If omitted, uses env DIGITALE_BIBLIOTHEK_ROOT."
        ),
    ] = None,
    volume_filter: Annotated[str | None, Field(description="Filter for volume names (e.g. DB002 or *philo*)")] = None,
) -> dict[str, Any]:
    """
    Batch decompress all Directmedia volumes in a library.

    ## Return Format
    {"library_path": str, "volumes_processed": int, "total_volumes_found": int, "total_text_extracted": int, "results": [...], "batch_status": str} or {"error": str}

    ## Examples
    decompress_directmedia_library()
    decompress_directmedia_library(volume_filter="DB002")
    """
    if not directmedia_available:
        return {"error": "Directmedia decoder unavailable"}

    resolved, paths_searched = resolve_digitale_library_root(library_path)
    if resolved is None:
        return {
            "error": "Digitale Bibliothek library directory not found",
            "paths_searched": paths_searched,
            "hint": "Set DIGITALE_BIBLIOTHEK_ROOT or pass library_path to your DB* parent folder.",
        }

    try:
        lib_path = resolved
        results = []

        # Find all DBxxx directories
        volume_dirs = [d for d in lib_path.iterdir() if d.is_dir() and d.name.startswith("DB")]

        if volume_filter:
            if "*" in volume_filter:
                # Simple glob matching
                import fnmatch

                volume_dirs = [d for d in volume_dirs if fnmatch.fnmatch(d.name, volume_filter)]
            else:
                volume_dirs = [d for d in volume_dirs if volume_filter in d.name]

        processed_volumes = 0
        total_text_extracted = 0

        for volume_dir in volume_dirs[:5]:  # Limit to first 5 volumes for safety
            data_dir = volume_dir / "Data"
            if not data_dir.exists():
                continue

            text_dki = data_dir / "TEXT.DKI"
            if text_dki.exists():
                try:
                    result = legacy_extract_for_server(text_dki)
                    if not result.get("success"):
                        results.append({"volume": volume_dir.name, "error": result.get("error", "decode failed")})
                        continue

                    volume_result = {
                        "volume": volume_dir.name,
                        "file_path": str(text_dki),
                        "sections_extracted": len(result["extracted_sections"]),
                        "text_bytes": result["total_extracted_size"],
                    }

                    total_text_extracted += result["total_extracted_size"]
                    processed_volumes += 1
                    results.append(volume_result)

                except Exception as e:
                    results.append({"volume": volume_dir.name, "error": str(e)})

        return {
            "library_path": str(lib_path),
            "volumes_processed": processed_volumes,
            "total_volumes_found": len(volume_dirs),
            "total_text_extracted": total_text_extracted,
            "results": results,
            "batch_status": "completed",
            "message": f"Processed {processed_volumes}/{len(volume_dirs)} volumes, "
            f"{total_text_extracted:,} text bytes extracted.",
        }

    except Exception as e:
        logger.exception("Error in batch Directmedia decompression")
        return {"error": f"Batch decompression failed: {e!s}"}


@mcp.tool(annotations=_READ_ONLY)
async def help(level: str = "basic", topic: str | None = None) -> dict[str, Any]:
    """
    Get comprehensive help information about Reversing MCP tools and capabilities.

    Args:
        level: Help detail level ("basic", "intermediate", "advanced")
        topic: Optional specific topic to focus on

    Returns:
        Formatted help documentation
    """

    if level not in ["basic", "intermediate", "advanced"]:
        level = "basic"

    # Basic help - essential getting started
    if level == "basic":
        help_content = {
            "level": "basic",
            "description": "Essential tools and quick start guide",
            "ghidra_note": (
                "Ghidra MCP is provided by a separate server (ReVa / reverse-engineering-assistant). "
                "Add it in your MCP client; use its tools for decompilation and listings. "
                "This server covers static analysis and Directmedia."
            ),
            "quick_start": [
                "1. Check available tools: check_tools()",
                "2. Analyze a binary: analyze_binary('file.exe', ['static', 'strings'])",
                "3. Extract strings: extract_strings('file.exe', min_length=8)",
                "4. Get hex dump: get_hexdump('file.exe', offset=0, length=256)",
                "5. For Ghidra: connect ReVa MCP (see docs/GHIDRA.md)",
                "6. Digibib5 / Directmedia: digibib_research_snapshot() (see docs/DIRECTMEDIA_REVERSING_TOOLKIT.md)",
                "7. For JS/Electron/.NET/APK/firmware or agent-driven native: rea_investigate(path) (see docs/REA.md)",
            ],
            "essential_tools": [
                "analyze_binary - Full binary analysis",
                "extract_strings - Find text in binaries",
                "get_hexdump - View raw bytes",
                "analyze_entropy - Detect compression/encryption",
                "check_tools - See what's available",
                "rea_investigate - REA sidecar delegate (JS/Electron/native via provider)",
                "digibib_research_snapshot - Static bundle for Digibib5.exe / viewer roadmap",
            ],
            "next_steps": "Use level='intermediate' for detailed tool descriptions",
        }

    # Intermediate help - detailed tool descriptions
    elif level == "intermediate":
        help_content = {
            "level": "intermediate",
            "description": "Detailed tool descriptions and workflows",
            "tool_categories": {
                "binary_analysis": [
                    "analyze_binary(file_path, tools) - Analyze with multiple tools",
                    "extract_strings(file_path, min_length, encodings) - Find printable strings",
                    "get_hexdump(file_path, offset, length) - Raw byte viewer",
                    "analyze_entropy(file_path, block_size) - Detect packed/encrypted sections",
                    "find_functions(file_path, tool) - Locate functions in binaries",
                    "digibib_research_snapshot(exe_path?) - Digibib5 / Directmedia static prelude + roadmap",
                ],
                "file_info": [
                    "get_file_info(file_path) - Basic file metadata",
                    "analyze_pe_file(file_path) - Windows PE analysis",
                    "decode_dki_file(path) - Directmedia .DKI zlib/gzip decode report",
                    "file_type detection, permissions, timestamps",
                ],
                "ghidra_tools": [
                    "Use the ReVa MCP server (reverse-engineering-assistant) for Ghidra-backed tools.",
                    "Discover tools via your client's tool list or ReVa's tool_search when available.",
                ],
                "ghidra_requirements": (
                    "Install ReVa for Ghidra MCP (assistant or headless mode per Ghidra version). "
                    "See docs/GHIDRA.md and CURSOR_HANDOFF.md."
                ),
            },
            "workflows": {
                "malware_analysis": [
                    "1. check_tools() - Verify local RE tools",
                    "2. analyze_binary(file.exe, ['static', 'strings', 'ghidra']) - Static + headless Ghidra if installed",
                    "3. Use ReVa MCP for interactive decompilation and xrefs in Ghidra",
                ],
                "firmware_research": [
                    "1. get_hexdump(file.bin, 0, 1024) - Check headers",
                    "2. analyze_entropy(file.bin) - Find packed sections",
                    "3. extract_strings(file.bin) - Find embedded strings",
                    "4. binwalk analysis for embedded filesystems",
                ],
                "agent_re": [
                    "1. analyze_binary(path) - Triage first (type, strings, entropy)",
                    "2. rea_investigate(path) - Auto-route to JS/native; no provider flags needed",
                    "3. rea_investigate(path, kind='native_search', query='decrypt') - Follow-up specifics",
                ],
            },
            "next_steps": "Use level='advanced' for technical details and Ghidra deep-dive",
        }

    # Advanced help - technical details and Ghidra expertise
    else:  # level == "advanced"
        help_content = {
            "level": "advanced",
            "description": "Technical architecture, Ghidra deep-dive, and expert references",
            "architecture": {
                "core_components": {
                    "BinaryAnalyzer": "Multi-tool analysis orchestrator supporting IDA, Ghidra headless, radare2",
                    "Ghidra MCP": (
                        "Interactive Ghidra analysis is a separate concern: run ReVa MCP alongside this server. "
                        "analyze_binary(..., ['ghidra']) may still use headless Ghidra when installed."
                    ),
                    "Directmedia Decompressor": "Legacy .DKI format reverse engineering",
                },
                "tool_detection": {
                    "automatic_discovery": "Scans common installation paths",
                    "fallback_handling": "Graceful degradation when tools unavailable",
                    "version_detection": "Extracts version info for compatibility",
                },
            },
            "ghidra_expertise": {
                "background": {
                    "developer": "National Security Agency (NSA) - United States Government",
                    "purpose": "Professional reverse engineering and malware analysis framework",
                    "license": "Apache License 2.0 (free and open source)",
                    "first_release": "2019, evolved from IDA Pro acquisition",
                    "current_version": "Ghidra 11.x / 12.x (12.0+ for PyGhidra 3.x headless scripting)",
                },
                "technical_capabilities": {
                    "decompiler": "Industry-leading retargetable decompiler with multi-architecture support",
                    "disassembler": "Supports 90+ processor architectures and instruction sets",
                    "analysis_engine": "Auto-analysis with function detection, data flow analysis, type inference",
                    "scripting": "Java-based scripting with full API access to analysis results",
                    "collaboration": "Multi-user analysis with version control integration",
                },
                "integration_architecture": {
                    "reva_mcp": "ReVa (reverse-engineering-assistant) exposes Ghidra as MCP; connect it in your client.",
                    "headless_note": "Ghidra 12.0+: ReVa headless (`mcp-reva`). Older: assistant mode with Ghidra GUI.",
                    "companion_server": "reversing-mcp stays focused on static tools + Directmedia without GUI coupling.",
                    "see_ghidra_docs": "docs/GHIDRA.md in this repo for setup and headless options.",
                },
                "competitive_advantages": {
                    "vs_ida_pro": "Free alternative with comparable analysis quality, though steeper learning curve",
                    "vs_binary_ninja": "More comprehensive enterprise features, better collaboration tools",
                    "vs_ghidra_online": "Local deployment maintains security, no cloud dependencies",
                    "vs_radare2": "GUI-first approach with professional-grade decompiler",
                },
                "use_cases": {
                    "malware_analysis": "Signature development, behavior analysis, IOC extraction",
                    "firmware_re": "Embedded system analysis, IoT device security research",
                    "vulnerability_research": "Patch analysis, exploit development, security assessments",
                    "digital_forensics": "Evidence analysis, timeline reconstruction, artifact extraction",
                },
            },
            "references": {
                "official_resources": {
                    "homepage": "https://ghidra-sre.org/",
                    "documentation": "https://ghidra-sre.org/Help/start.html",
                    "github": "https://github.com/NationalSecurityAgency/ghidra",
                    "wiki": "https://github.com/NationalSecurityAgency/ghidra/wiki",
                    "api_docs": "https://ghidra-sre.org/Help/api/",
                },
                "community_resources": {
                    "reddit": "r/ReverseEngineering, r/Ghidra",
                    "discord": "Ghidra Discord community server",
                    "tutorials": "John Hammond, LiveOverflow, Azeria Labs Ghidra guides",
                    "books": "'The Ghidra Book' by Chris Eagle and Kara Nance",
                    "blogs": "NSA Ghidra blog, OpenSecurityResearch Ghidra posts",
                },
                "academic_citations": {
                    "papers": "IEEE Security & Privacy, Black Hat, DEF CON presentations",
                    "research": "NSA Research Directorate publications on binary analysis",
                    "comparisons": "Independent studies comparing Ghidra vs commercial tools",
                },
            },
            "expert_workflows": {
                "automated_analysis": [
                    "1. Batch processing with custom Ghidra scripts",
                    "2. CI/CD integration for continuous security scanning",
                    "3. API-driven analysis for large-scale malware processing",
                    "4. Custom plugin development for specialized analysis",
                ],
                "collaboration_setup": [
                    "1. Shared repository configuration for team analysis",
                    "2. Version control integration with Git",
                    "3. Review workflows for analysis validation",
                    "4. Automated diffing for patch analysis",
                ],
            },
            "troubleshooting": {
                "common_issues": {
                    "memory_usage": "Large binaries may require increased heap size (-Xmx8G)",
                    "analysis_time": "Complex binaries can take hours; for batch use analyzeHeadless or PyGhidra (see docs/GHIDRA.md)",
                    "false_positives": "Decompiler may produce incorrect code; always verify manually",
                    "plugin_conflicts": "Third-party plugins can cause stability issues",
                },
                "performance_tuning": {
                    "headless_flags": "-analysisTimeoutPerFile, -max-cpu, -commit",
                    "memory_settings": "-Xmx, -Xms for JVM heap configuration",
                    "parallel_processing": "Multiple Ghidra instances for batch analysis",
                },
            },
        }

    # Add topic-specific filtering if requested
    if topic:
        if topic.lower() == "ghidra":
            if level == "advanced":
                # Return only Ghidra-specific advanced content
                return {
                    "topic": "ghidra",
                    "level": "advanced",
                    **help_content["ghidra_expertise"],
                    **help_content["references"],
                }
            return {"error": f"Topic '{topic}' only available in advanced level"}
        if topic.lower() in ["binary", "analysis"]:
            return {
                "topic": topic,
                "level": level,
                "tools": help_content.get("tool_categories", {}).get("binary_analysis", []),
                "workflows": help_content.get("workflows", {}),
            }

    help_content["message"] = f"Reversing MCP help ({level} level)."
    return help_content


@mcp.tool(annotations=_DESTRUCTIVE)
async def shutdown(confirm: bool = False) -> dict:
    """
    Gracefully shut down the Reversing MCP server.

    Requires confirm=True to prevent accidental termination.
    """
    if not confirm:
        return {"success": False, "message": "Shutdown requires confirm=True"}
    import os
    import threading

    threading.Thread(target=lambda: os._exit(0), daemon=True).start()
    return {"success": True, "message": "Server shutting down"}


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Reversing MCP Server - Free RE Tools + Directmedia Decompression")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Set log level
    import logging

    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

    logger.info("Starting Reversing MCP Server")

    # Run MCP server
    run_server(mcp, server_name="ReversingMCP")


# ASGI app for uvicorn (e.g. web_sota: uvicorn reversing_mcp.server:app)
# Mounts MCP at /mcp; add more routes here if needed.
try:
    import platform

    from fastapi import BackgroundTasks, File, HTTPException, UploadFile
    from fastapi import FastAPI as _FastAPI
    from fastapi.middleware.cors import CORSMiddleware as _CORSMiddleware
    from fastapi.responses import Response

    _http_app = _FastAPI(title="Reversing MCP HTTP", version="0.4.0")

    _http_app.add_middleware(
        _CORSMiddleware,
        allow_origins=[
            "http://localhost:10751",
            "http://127.0.0.1:10751",
            "http://localhost:10750",
            "http://127.0.0.1:10750",
            "tauri://localhost",
            "http://tauri.localhost",
            "https://tauri.localhost",
        ],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _start_time = __import__("time").time()

    @_http_app.get("/health")
    async def _health() -> dict:
        tools = await mcp.list_tools()
        return {
            "status": "ok",
            "version": "0.4.0",
            "tool_count": len(tools),
        }

    @_http_app.get("/api/v1/diagnostics")
    async def _diagnostics() -> dict:
        tools = await mcp.list_tools()
        uptime = int(__import__("time").time() - _start_time)
        return {
            "status": "ok",
            "server": "ReversingMCP",
            "version": "0.4.0",
            "uptime_seconds": uptime,
            "tool_count": len(tools),
            "tools": [{"name": t.name} for t in tools],
            "system": {
                "platform": platform.system(),
                "windows": platform.system() == "Windows",
                "python": platform.python_version(),
            },
            "errors": [],
        }

    @_http_app.post("/api/shutdown")
    async def _shutdown():
        import os

        os._exit(0)

    @_http_app.get("/api/v1/digibib/find")
    async def _digibib_find():
        """Find Digibib5.exe in known locations."""
        from .digibib_research import resolve_digibib_exe

        resolved, tried = resolve_digibib_exe(None)
        return {"found": resolved is not None, "path": str(resolved) if resolved else None, "paths_searched": tried}

    @_http_app.get("/api/v1/digibib/snapshot")
    async def _digibib_snapshot(exe_path: str | None = None):
        """Run DigiBib research snapshot."""
        from .digibib_research import build_research_snapshot, resolve_digibib_exe

        resolved, tried = resolve_digibib_exe(exe_path)
        if resolved is None:
            return {"success": False, "error": "Digibib5.exe not found", "paths_searched": tried}
        return await asyncio.to_thread(build_research_snapshot, analyzer, resolved)

    @_http_app.get("/api/v1/digibib/check-idr")
    async def _digibib_check_idr():
        """Check if IDR (Interactive Delphi Reconstructor) is installed."""
        import shutil

        idr_path = shutil.which("Idr.exe") or shutil.which("IDR.exe")
        alt_paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "IDR" / "Idr.exe",
            Path(r"C:\Tools\IDR\Idr.exe"),
            Path(r"C:\Program Files\IDR\Idr.exe"),
        ]
        if idr_path:
            return {"installed": True, "path": idr_path, "version": "27_01_2019"}
        for p in alt_paths:
            if p.exists():
                return {"installed": True, "path": str(p), "version": "27_01_2019"}
        return {"installed": False, "install_hint": "Run: just install-idr"}

    @_http_app.get("/api/v1/digibib/decode-dki")
    async def _digibib_decode_dki(path: str):
        """Decode a DKI file using the heuristic decoder."""
        r = await asyncio.to_thread(decode_dki_path, Path(path))
        return result_to_mcp_dict(path, r)

    @_http_app.get("/api/v1/digibib/directmedia-strings")
    async def _digibib_directmedia_strings(exe_path: str | None = None):
        """Extract strings matching Directmedia keywords from Digibib5.exe."""
        from .digibib_research import filter_directmedia_strings, resolve_digibib_exe

        resolved, tried = resolve_digibib_exe(exe_path)
        if resolved is None:
            return {"success": False, "error": "Digibib5.exe not found", "paths_searched": tried}
        strings = await asyncio.to_thread(analyzer.extract_strings, str(resolved), min_length=5)
        hits = filter_directmedia_strings(strings)
        return {"success": True, "hits": hits[:200], "total": len(hits)}

    @_http_app.get("/api/skills")
    async def _list_skills():
        skills_dir = SKILLS_DIR
        if skills_dir.exists():
            names = [d.name for d in skills_dir.iterdir() if d.is_dir()]
            return {"skills": names}
        return {"skills": []}

    @_http_app.get("/api/skills/{name}")
    async def _get_skill(name: str):
        skill_path = SKILLS_DIR / name / "SKILL.md"
        if skill_path.exists():
            return {"name": name, "content": skill_path.read_text(encoding="utf-8")}
        return {"error": "Skill not found"}

    @_http_app.get("/skill/{name}")
    async def _get_skill_alias(name: str):
        """Skill content as raw text (chat-skills-prefab standard §5)."""
        skill_path = SKILLS_DIR / name / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return "not found"

    # --- Transplanted 2026-10-11 from reversing-webapp/api/main.py (Next.js app retired;
    # Vite web_sota is the surviving frontend and already calls these routes).
    # Adaptations: .dict() -> .model_dump() (pydantic v2), chat history order fixed
    # (history first, new message last), chat model fallback auto-picks instead of
    # hardcoded "llama2". No duplicate /health or /mcp mount (both exist above).

    _GHIDRA_BRIDGE_URL = os.getenv("GHIDRA_BRIDGE_URL", "http://127.0.0.1:8089")
    _OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    _selected_ollama_model: str | None = None

    class _AnalysisRequest(BaseModel):
        file_path: str
        tools: list[str] | None = None

    class _GhidraStatus(BaseModel):
        available: bool
        installed: bool = False
        version: str | None = None
        bridge_running: bool = False
        bridge_url: str | None = None
        connected_instance: str | None = None

    class _GhidraConnectRequest(BaseModel):
        instance_id: str
        mode: str = "tcp"

    class _AnalysisResponse(BaseModel):
        file_path: str
        file_size: int
        tools_used: list[str]
        results: dict[str, Any]
        analysis_score: float
        language_hint: str
        entropy_score: float
        functions: int
        strings: int
        has_pdb: bool
        is_obfuscated: bool

    class _LLMProviderBody(BaseModel):
        provider: str = "ollama"

    class _LLMSelectBody(BaseModel):
        provider: str = "ollama"
        model: str = ""

    class _ChatRequest(BaseModel):
        message: str
        history: list[dict[str, str]] = []
        system: str | None = None
        model: str | None = None

    def _analysis_score(results: dict[str, Any]) -> float:
        score = 0.0
        if "file_info" in results:
            score += 20
        if results.get("strings"):
            score += 20
        if "entropy_analysis" in results:
            score += 20
        if "pe_analysis" in results:
            score += 20
        if results.get("functions"):
            score += 20
        return min(score, 100.0)

    def _language_hint(results: dict[str, Any]) -> str:
        text = " ".join(str(s) for s in results.get("strings", [])).lower()
        hints = {
            "c/c++": ["printf", "scanf", "malloc", "free", "iostream", "std::"],
            "python": ["import ", "def ", "class ", "python", "pip"],
            "java": ["java", "public static void main", "system.out", "import java"],
            "csharp": ["using system", "console.writeline", "namespace", ".net"],
            "go": ["package main", "import (", "fmt.printf", "golang"],
            "rust": ["fn main", "println!", "cargo", "rust"],
            "javascript": ["function ", "console.log", "node.js", "npm"],
        }
        for lang, indicators in hints.items():
            if any(i in text for i in indicators):
                return lang.title()
        return "Unknown"

    def _has_pdb(results: dict[str, Any]) -> bool:
        text = " ".join(str(s) for s in results.get("strings", [])).lower()
        return ".pdb" in text

    def _is_obfuscated(results: dict[str, Any]) -> bool:
        if results.get("entropy_analysis", {}).get("overall_entropy", 0.0) > 7.5:
            return True
        if len(results.get("strings", [])) < 3:
            return True
        text = " ".join(str(s) for s in results.get("strings", [])).lower()
        return any(w in text for w in ["obfuscated", "packed", "encrypted", "compressed"])

    def _analysis_response(file_path: str, file_size: int, tool_list: list[str], results: dict[str, Any]):
        return _AnalysisResponse(
            file_path=file_path,
            file_size=file_size,
            tools_used=tool_list,
            results=results,
            analysis_score=_analysis_score(results),
            language_hint=_language_hint(results),
            entropy_score=results.get("entropy_analysis", {}).get("overall_entropy", 0.0),
            functions=len(results.get("functions", [])),
            strings=len(results.get("strings", [])),
            has_pdb=_has_pdb(results),
            is_obfuscated=_is_obfuscated(results),
        )

    @_http_app.get("/tools/status")
    async def _web_tools_status():
        """Engine inventory for Status/Tools pages (backed by check_tools data)."""
        try:
            # Probes shell out (REA alone ~8s); keep them off the event loop.
            tools = await asyncio.to_thread(analyzer.check_available_tools)
            ghidra = tools.get("ghidra", {})
            return {
                "tools": {
                    "file": {"available": True},
                    "strings": {"available": True},
                    "entropy": {"available": True},
                    "pefile": {"available": True},
                    "ghidra_mcp": {
                        "available": False,
                        "installed": bool(ghidra.get("available")),
                        "version": ghidra.get("version"),
                        "note": f"Bridge: {_GHIDRA_BRIDGE_URL}",
                    },
                    "rea": tools.get("rea", {"available": False}),
                },
                # Full check_tools() inventory (ida/r2/binwalk too) for Help -> Engines.
                "engines": tools,
            }
        except Exception as e:
            logger.exception("Error checking tools status")
            raise HTTPException(status_code=500, detail=f"Tools status check failed: {e!s}") from e

    @_http_app.post("/analyze/upload")
    async def _analyze_upload(
        background_tasks: BackgroundTasks, file: UploadFile = File(...), tools: str | None = None
    ):
        """Analyze an uploaded file (Analyze page)."""
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        tool_list = tools.split(",") if tools else ["file", "strings", "entropy"]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        try:
            results = await asyncio.to_thread(analyzer.analyze_file, temp_file_path, tool_list)
            response = _analysis_response(file.filename, len(content), tool_list, results)
            background_tasks.add_task(os.unlink, temp_file_path)
            return response.model_dump()
        except Exception as e:
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
            logger.exception(f"Error analyzing uploaded file {file.filename}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e!s}") from e

    @_http_app.post("/analyze/file")
    async def _analyze_path(request: _AnalysisRequest):
        """Analyze a file by server-side path."""
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        try:
            tool_list = request.tools or ["file", "strings", "entropy"]
            results = await asyncio.to_thread(analyzer.analyze_file, request.file_path, tool_list)
            response = _analysis_response(request.file_path, os.path.getsize(request.file_path), tool_list, results)
            return response.model_dump()
        except Exception as e:
            logger.exception(f"Error analyzing file {request.file_path}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {e!s}") from e

    async def _ghidra_request(path: str, method: str = "GET", params: dict | None = None, data: dict | None = None):
        """Proxy to the Ghidra MCP bridge (ReVa/bridge on :8089). Returns None when down."""
        import httpx

        url = f"{_GHIDRA_BRIDGE_URL}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "GET":
                    r = await client.get(url, params=params)
                else:
                    r = await client.post(url, json=data)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                # Bridge-down is the normal state when ReVa is not running - debug, not error.
                logger.debug(f"Ghidra bridge down ({path}): {e}")
                return None

    @_http_app.get("/ghidra/status")
    async def _ghidra_status():
        """Ghidra install + bridge health for Dashboard/Settings/Status pages."""
        installed = False
        version = None
        bridge_running = False
        connected_instance = None
        try:
            # Ghidra-only probe, off the event loop: the full inventory blocks ~8s
            # on the REA probe and froze every request behind the dashboard.
            g: dict[str, Any] = {}
            await asyncio.to_thread(analyzer._check_ghidra, g)
            installed = bool(g.get("available"))
            version = g.get("version")
            status = await _ghidra_request("/status")
            if status:
                bridge_running = True
                connected_instance = status.get("connected_instance")
        except Exception as e:
            logger.debug("Ghidra status probe failed (%s); reporting bridge as down", e)
        return _GhidraStatus(
            available=bridge_running,
            installed=installed,
            version=version,
            bridge_running=bridge_running,
            bridge_url=_GHIDRA_BRIDGE_URL,
            connected_instance=connected_instance,
        ).model_dump()

    @_http_app.get("/ghidra/instances")
    async def _ghidra_instances():
        instances = await _ghidra_request("/instances")
        if instances is None:
            raise HTTPException(status_code=503, detail="Ghidra bridge unavailable")
        return instances

    @_http_app.post("/ghidra/connect")
    async def _ghidra_connect(request: _GhidraConnectRequest):
        result = await _ghidra_request("/connect", method="POST", data=request.model_dump())
        if result is None:
            raise HTTPException(status_code=502, detail="Failed to connect to Ghidra")
        return result

    @_http_app.get("/ghidra/functions")
    async def _ghidra_functions():
        functions = await _ghidra_request("/functions")
        if functions is None:
            raise HTTPException(status_code=502, detail="Ghidra not connected or error fetching functions")
        return functions

    @_http_app.post("/ghidra/decompile")
    async def _ghidra_decompile(function_name: str):
        result = await _ghidra_request("/decompile", method="POST", data={"function_name": function_name})
        if result is None:
            raise HTTPException(status_code=502, detail="Decompilation failed")
        return result

    @_http_app.post("/ghidra/disassemble")
    async def _ghidra_disassemble(address: str):
        result = await _ghidra_request("/disassemble", method="POST", data={"address": address})
        if result is None:
            raise HTTPException(status_code=502, detail="Disassembly failed")
        return result

    @_http_app.post("/start_ghidra")
    async def _start_ghidra():
        # Legacy stub kept for compat; the Status page uses /api/v1/reva/* now.
        return {
            "ok": True,
            "message": "Use POST /api/v1/reva/start (headless mcp-reva or Ghidra GUI) - see docs/REVA.md.",
        }

    # --- ReVa lifecycle (real start button for the Status page) ---

    class _RevaStartBody(BaseModel):
        mode: str = "headless"
        confirm: bool = False

    @_http_app.get("/api/v1/reva")
    async def _reva_status():
        """ReVa probe: mcp-reva presence, Ghidra dir, managed process, bridge reachability."""
        import asyncio

        return await asyncio.to_thread(_reva.status, _GHIDRA_BRIDGE_URL)

    @_http_app.post("/api/v1/reva/start")
    async def _reva_start(body: _RevaStartBody):
        """Start ReVa headless (mcp-reva) or the Ghidra GUI. Confirm-gated."""
        import asyncio

        return await asyncio.to_thread(_reva.start, body.mode, body.confirm, _GHIDRA_BRIDGE_URL)

    @_http_app.post("/api/v1/reva/stop")
    async def _reva_stop():
        """Stop the managed ReVa process (whole tree). Idempotent."""
        import asyncio

        return await asyncio.to_thread(_reva.stop)

    # --- Toolbox: autodiscovery / install / autostart ---

    class _ToolboxInstallBody(BaseModel):
        name: str

    class _ToolboxPolicyBody(BaseModel):
        updates: dict = {}

    @_http_app.get("/api/v1/toolbox")
    async def _toolbox_probe():
        """Full toolchain inventory (ghidra, reva, capa, die, frida, r2, hopper, ida, java, tesseract, node)."""
        import asyncio

        return await asyncio.to_thread(_toolbox.probe)

    @_http_app.post("/api/v1/toolbox/rescan")
    async def _toolbox_rescan():
        import asyncio

        return await asyncio.to_thread(_toolbox.probe)

    @_http_app.post("/api/v1/toolbox/install")
    async def _toolbox_install(body: _ToolboxInstallBody):
        """Install one toolbox entry (winget / GitHub release / pip venv). May take minutes."""
        import asyncio

        return await asyncio.to_thread(_toolbox.install, body.name)

    @_http_app.get("/api/v1/toolbox/policy")
    async def _toolbox_policy_get():
        return _toolbox.get_policy()

    @_http_app.post("/api/v1/toolbox/policy")
    async def _toolbox_policy_set(body: _ToolboxPolicyBody):
        return _toolbox.set_policy(body.updates)

    @_http_app.post("/api/v1/toolbox/ensure")
    async def _toolbox_ensure():
        """Discover, export env, start policy services. Idempotent."""
        import asyncio

        return await asyncio.to_thread(_toolbox.ensure, True)

    @_http_app.on_event("startup")
    async def _toolbox_boot():
        """Daemon boot only: toolbox ensure (discover + autostart policy services)."""
        import asyncio

        await asyncio.to_thread(_toolbox.ensure, True)

    async def _ollama_tags() -> dict:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{_OLLAMA_BASE}/api/tags")
            r.raise_for_status()
            return r.json()

    async def _ollama_running() -> list[str]:
        """Models currently resident in VRAM (never evict these by defaulting elsewhere)."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{_OLLAMA_BASE}/api/ps")
                r.raise_for_status()
                return [m.get("name", "") for m in r.json().get("models", [])]
        except Exception:
            return []

    _MODEL_PREFERENCE = ("qwen3.8:27b", "gemma4:12b")

    async def _pick_model() -> str | None:
        """Resident-first default (chat standard §1.7): running model in preference order,
        else highest-preference installed model. Never tags[0] blindly... except there is
        nothing else to go on, in which case first installed beats no model."""
        try:
            running = await _ollama_running()
            for preferred in _MODEL_PREFERENCE:
                for name in running:
                    if name == preferred or name.startswith(preferred.split(":")[0] + ":"):
                        return name
            if running:
                return running[0]
            tags = await _ollama_tags()
            installed = [m.get("name", m.get("model", "")) for m in tags.get("models", [])]
            for preferred in _MODEL_PREFERENCE:
                for name in installed:
                    if name == preferred or name.startswith(preferred.split(":")[0] + ":"):
                        return name
            return installed[0] if installed else None
        except Exception:
            return None

    @_http_app.post("/llm/list_providers")
    async def _llm_providers():
        """Available LLM providers (Ollama local today; cloud keys live in Settings)."""
        return {"providers": [{"id": "ollama", "name": "Ollama"}]}

    @_http_app.post("/llm/list_models")
    async def _llm_models(body: _LLMProviderBody | None = None):
        provider = body.provider if body else "ollama"
        if provider != "ollama":
            return {"models": []}
        try:
            data = await _ollama_tags()
            models = [m.get("name", m.get("model", "")) for m in data.get("models", [])]
            return {"models": models}
        except Exception as e:
            logger.exception("Ollama list_models failed")
            return {"models": [], "error": str(e)}

    @_http_app.post("/llm/select_model")
    async def _llm_select(body: _LLMSelectBody | None = None):
        global _selected_ollama_model
        if not body:
            body = _LLMSelectBody()
        if body.provider == "ollama" and body.model:
            _selected_ollama_model = body.model
        return {"ok": True, "provider": body.provider, "model": body.model}

    @_http_app.post("/llm/load_model")
    async def _llm_load(body: _LLMSelectBody | None = None):
        """Ollama loads on first use; selecting is sufficient."""
        return await _llm_select(body)

    @_http_app.post("/llm/unload_model")
    async def _llm_unload(body: dict | None = None):
        global _selected_ollama_model
        _selected_ollama_model = None
        return {"ok": True}

    @_http_app.post("/llm/status")
    async def _llm_status():
        try:
            await _ollama_tags()
            healthy = True
        except Exception:
            healthy = False
        return {"provider": "ollama", "model": _selected_ollama_model, "healthy": healthy, "base_url": _OLLAMA_BASE}

    @_http_app.post("/llm/health")
    async def _llm_health(body: _LLMProviderBody | None = None):
        provider = body.provider if body else "ollama"
        if provider != "ollama":
            return {"healthy": False, "error": "Unknown provider"}
        try:
            await _ollama_tags()
            return {"healthy": True, "provider": "ollama"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    @_http_app.get("/api/llm/discover")
    async def _llm_discover():
        """Provider detection for Settings/Chat (chat standard §1.7): Ollama presence,
        resident-first default model, full installed list. No hardcoded fallbacks."""
        try:
            data = await _ollama_tags()
            installed = [m.get("name", m.get("model", "")) for m in data.get("models", [])]
            running = await _ollama_running()
            default = await _pick_model()
            return {
                "provider": "ollama",
                "detected": True,
                "base_url": _OLLAMA_BASE,
                "default_model": default,
                "running": running,
                "models": installed,
            }
        except Exception as e:
            return {"provider": "ollama", "detected": False, "base_url": _OLLAMA_BASE, "error": str(e)}

    @_http_app.get("/api/llm/providers")
    async def _llm_providers_get():
        """GET alias of provider discovery (Settings page calls this shape)."""
        return await _llm_discover()

    @_http_app.post("/api/v1/chat")
    async def _chat(request: _ChatRequest):
        """Send message history to the selected Ollama model; returns reply.
        History first, new message last. Model: explicit selection, else resident-first
        auto-pick, else 409 (never a hardcoded ghost model)."""
        import httpx

        model = request.model or _selected_ollama_model or await _pick_model()
        if not model:
            raise HTTPException(
                status_code=409,
                detail="No Ollama model available. Start Ollama and pull a model, then retry.",
            )
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.extend({"role": h.get("role", "user"), "content": h.get("content", "")} for h in request.history)
        messages.append({"role": "user", "content": request.message})
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(
                    f"{_OLLAMA_BASE}/api/chat",
                    json={"model": model, "messages": messages, "stream": False},
                )
                r.raise_for_status()
                data = r.json()
                reply = data.get("message", {}).get("content", "")
                return {"reply": reply, "model": model}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Chat error")
            raise HTTPException(status_code=502, detail=f"Ollama chat failed: {e!s}") from e

    # --- In-repo activity log (folded 2026-10-11 from web_sota/backend/server.py;
    # that standalone app bound forbidden port 8000 and was never started by any
    # launcher. Same shapes the Logging page already calls.)

    class _ActivityLog:
        def __init__(self, max_entries: int = 2000):
            self.max_entries = max_entries
            self._entries: deque = deque(maxlen=max_entries)

        def add(self, level: str, kind: str, detail: str, meta: dict | None = None) -> str:
            eid = f"{time.time():.6f}.{uuid4().hex[:6]}"
            self._entries.append(
                {
                    "id": eid,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                    "level": level.upper(),
                    "kind": kind,
                    "detail": detail,
                    "meta": meta or {},
                }
            )
            return eid

        def query(self, limit=50, offset=0, level=None, kind=None, search=None, sort="desc", after_id=None):
            entries = list(self._entries)
            if after_id:
                try:
                    at = float(after_id.split(".")[0])
                    entries = [e for e in entries if float(e["id"].split(".")[0]) > at]
                except (ValueError, IndexError):
                    pass
            if level:
                lo = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
                ml = lo.get(level.upper(), 1)
                entries = [e for e in entries if lo.get(e["level"], 1) >= ml]
            if kind:
                entries = [e for e in entries if e["kind"] == kind]
            if search:
                q = search.lower()
                entries = [e for e in entries if q in e["detail"].lower()]
            entries.sort(key=lambda e: e["id"], reverse=(sort == "desc"))
            total = len(entries)
            return {
                "entries": entries[offset : offset + limit],
                "total": total,
                "limit": limit,
                "offset": offset,
                "max_entries": self.max_entries,
                "sort": sort,
            }

        def stats(self):
            levels: dict[str, int] = {}
            kinds: dict[str, int] = {}
            for e in self._entries:
                levels[e["level"]] = levels.get(e["level"], 0) + 1
                kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
            return {"total": len(self._entries), "max_entries": self.max_entries, "levels": levels, "kinds": kinds}

        def export(self, format="json", **filters):
            result = self.query(limit=self.max_entries, **filters)
            if format == "csv":
                import csv
                import io

                buf = io.StringIO()
                w = csv.writer(buf)
                w.writerow(["id", "timestamp", "level", "kind", "detail", "meta"])
                for e in result["entries"]:
                    w.writerow([e["id"], e["timestamp"], e["level"], e["kind"], e["detail"], json.dumps(e["meta"])])
                return buf.getvalue()
            return json.dumps(result["entries"], indent=2)

        def clear(self):
            self._entries.clear()

    _activity_log = _ActivityLog()
    _activity_log.add("INFO", "server", "Reversing MCP HTTP backend started")

    @_http_app.get("/api/docs/{name}")
    async def _docs_get(name: str):
        """Serve a repo doc as JSON for the in-app Help viewer (no GitHub round-trip).

        Allowlisted to docs/*.md only: basename match, no separators, resolved
        path must stay under docs/. Unknown names 404.
        """
        import re

        from fastapi.responses import JSONResponse

        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_\-]*\.md", name or ""):
            return JSONResponse(status_code=404, content={"success": False, "error": f"Unknown doc: {name}"})
        docs_dir = Path(__file__).resolve().parents[2] / "docs"
        target = (docs_dir / name).resolve()
        if docs_dir not in target.parents or not target.is_file():
            return JSONResponse(status_code=404, content={"success": False, "error": f"Unknown doc: {name}"})
        try:
            return {"success": True, "name": name, "content": target.read_text(encoding="utf-8", errors="replace")}
        except OSError as e:
            return JSONResponse(status_code=500, content={"success": False, "error": str(e)[:200]})

    @_http_app.get("/api/logs")
    async def _logs(
        limit: int = 50,
        offset: int = 0,
        level: str | None = None,
        kind: str | None = None,
        search: str | None = None,
        sort: str = "desc",
        after_id: str | None = None,
    ):
        return _activity_log.query(
            limit=limit, offset=offset, level=level, kind=kind, search=search, sort=sort, after_id=after_id
        )

    @_http_app.get("/api/logs/stats")
    async def _logs_stats():
        return _activity_log.stats()

    @_http_app.get("/api/logs/export")
    async def _logs_export(
        format: str = "json", level: str | None = None, kind: str | None = None, search: str | None = None
    ):
        content = _activity_log.export(format=format, level=level, kind=kind, search=search)
        media = "text/csv" if format == "csv" else "application/json"
        return Response(
            content=content, media_type=media, headers={"Content-Disposition": f'attachment; filename="logs.{format}"'}
        )

    @_http_app.delete("/api/logs")
    async def _logs_clear():
        _activity_log.clear()
        return {"success": True, "message": "Logs cleared."}

    # --- Fleet-standard LLM surface (aliases + discovery gaps closed 2026-10-11) ---

    @_http_app.get("/api/llm/models")
    async def _llm_models_get(provider: str = "ollama"):
        """Live model list per provider (Settings dropdown)."""
        if provider != "ollama":
            return {"provider": provider, "models": [], "source": "none"}
        try:
            data = await _ollama_tags()
            models = [m.get("name", m.get("model", "")) for m in data.get("models", [])]
            return {"provider": provider, "models": models, "source": "live"}
        except Exception as e:
            return {"provider": provider, "models": [], "source": "none", "error": str(e)}

    @_http_app.get("/api/llm/onboarding")
    async def _llm_onboarding():
        """Fresh-install starter facts + recommended path (under-hero cue)."""
        disc = await _llm_discover()
        if disc.get("detected") and disc.get("models"):
            return {
                "ready": True,
                "path": "chat",
                "reason": f"Ollama detected with {len(disc.get('models', []))} model(s); default {disc.get('default_model')}.",
                "default_model": disc.get("default_model"),
                "models": disc.get("models", []),
            }
        if disc.get("detected"):
            return {
                "ready": False,
                "path": "settings",
                "reason": "Ollama is serving but has no models. Pull one, then chat.",
                "default_model": None,
                "models": [],
                "action": "pull",
                "action_label": "Pull qwen3.8:27b",
                "action_endpoint": "/api/llm/ollama/pull",
            }
        gpus = await _llm_gpus()
        names = ", ".join(g.get("name", "?") for g in gpus) if gpus else ""
        ollama = await asyncio.to_thread(_toolbox.detect_ollama)
        status = ollama.get("status")
        if status == "installed":
            return {
                "ready": False,
                "path": "settings",
                "reason": f"Ollama is installed{f' (GPU: {names})' if names else ''} but not serving. Start it, pull a model, then chat.",
                "default_model": None,
                "models": [],
                "gpus": gpus,
                "action": "start",
                "action_label": "Start Ollama",
                "action_endpoint": "/api/llm/ollama/start",
            }
        return {
            "ready": False,
            "path": "settings",
            "reason": f"{'GPU detected (' + names + ') but n' if names else 'N'}o Ollama installed. Install it, pull a model, then chat.",
            "default_model": None,
            "models": [],
            "gpus": gpus,
            "action": "install",
            "action_label": "Install Ollama",
            "action_endpoint": "/api/llm/ollama/install",
        }

    @_http_app.post("/api/llm/ollama/start")
    async def _ollama_start():
        """Launch `ollama serve` detached (installed-but-idle → serving)."""
        import asyncio

        return await asyncio.to_thread(_toolbox.start_ollama)

    @_http_app.post("/api/llm/ollama/install")
    async def _ollama_install():
        """Install Ollama via winget (Ollama.Ollama). Minutes, never silent."""
        import asyncio

        return await asyncio.to_thread(_toolbox.install, "ollama")

    class _OllamaPullBody(BaseModel):
        model: str = "qwen3.8:27b"

    @_http_app.post("/api/llm/ollama/pull")
    async def _ollama_pull(body: _OllamaPullBody):
        """Pull a model in the background (GBs take minutes; poll /api/llm/discover)."""
        import asyncio

        return await asyncio.to_thread(_toolbox.pull_ollama_model, body.model)

    @_http_app.get("/api/llm/gpus")
    async def _llm_gpus():
        """NVIDIA GPU inventory for VRAM-aware model defaults (empty when absent)."""
        import shutil
        import subprocess

        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi is None:
            return []
        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                [nvidia_smi, "--query-gpu=index,name,memory.total", "--format=csv,noheader,nounits"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            gpus = []
            for line in (proc.stdout or "").splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3 and parts[2].isdigit():
                    gpus.append(
                        {"index": int(parts[0]), "name": parts[1], "total_mb": int(parts[2]), "vramMb": int(parts[2])}
                    )
            return gpus
        except (subprocess.SubprocessError, OSError):
            logger.exception("nvidia-smi probe failed")
            return []

    @_http_app.post("/api/llm/chat")
    async def _llm_chat(body: dict):
        """Backend chat proxy (OpenAI-style {provider, model, messages}) — the ONLY
        path Chat uses besides the legacy /api/v1/chat shape. Keys never leave the server
        (Ollama-only today; cloud providers phase 2)."""
        provider = body.get("provider", "ollama")
        if provider != "ollama":
            raise HTTPException(status_code=501, detail=f"Provider '{provider}' not wired yet (Ollama only).")
        messages = body.get("messages", [])
        text = ""
        history = []
        if messages and messages[-1].get("role") == "user":
            text = messages[-1].get("content", "")
            history = messages[:-1]
        req = _ChatRequest(
            message=text,
            history=history,
            system=next((m.get("content") for m in messages if m.get("role") == "system"), None),
            model=body.get("model"),
        )
        out = await _chat(req)
        return {"content": out["reply"], "model": out["model"], "provider": provider}

    @_http_app.get("/api/capabilities")
    async def _capabilities():
        """Fleet-standard capability surface (ports, features, tool inventory)."""
        tools = await mcp.list_tools()
        return {
            "name": "reversing-mcp",
            "version": "0.4.0",
            "ports": {"backend": 10750, "frontend": 10751},
            "features": {
                "chat": True,
                "skills": True,
                "llm_discover": True,
                "diagnostics": True,
                "logs": True,
                "rea_sidecar": True,
                "elicitation": True,
                "clicker": True,
                "reva": True,
                "toolbox": True,
            },
            "tools": sorted([t.name for t in tools]),
            "tool_docs": sorted(
                ({"name": t.name, "description": t.description or ""} for t in tools),
                key=lambda d: d["name"],
            ),
        }

    # --- Reversing Gym G1 (stages 0/1/4; blocking work off the event loop) ---

    class _GymStartBody(BaseModel):
        target: str
        test_files: list[str] | None = None
        notes: str = ""

    class _GymAdvanceBody(BaseModel):
        decision: str | None = None
        confirm: bool = False
        accept_local: bool = False
        duration_s: int = 60

    @_http_app.post("/api/v1/gym/runs")
    async def _gym_start(body: _GymStartBody):
        import asyncio

        return await asyncio.to_thread(_gym.create_run, body.target, body.test_files, body.notes or "")

    @_http_app.get("/api/v1/gym/runs")
    async def _gym_list():
        import asyncio

        return await asyncio.to_thread(_gym.list_runs)

    @_http_app.get("/api/v1/gym/runs/{run_id}")
    async def _gym_get(run_id: str):
        import asyncio

        return await asyncio.to_thread(_gym.get_run, run_id)

    @_http_app.post("/api/v1/gym/runs/{run_id}/advance")
    async def _gym_advance(run_id: str, body: _GymAdvanceBody | None = None):
        """advance_run with oracle gates: confirm + accept_local execute the target."""
        import asyncio

        b = body or _GymAdvanceBody()
        return await asyncio.to_thread(
            _gym.advance_run, run_id, b.decision, True, b.confirm, b.accept_local, b.duration_s
        )

    @_http_app.post("/api/v1/gym/runs/{run_id}/stop")
    async def _gym_stop(run_id: str):
        import asyncio

        return await asyncio.to_thread(_gym.stop_run, run_id)

    @_http_app.get("/api/v1/gym/runs/{run_id}/artifacts/{rel_path:path}")
    async def _gym_artifact(run_id: str, rel_path: str):
        import asyncio

        return await asyncio.to_thread(_gym.read_artifact, run_id, rel_path)

    # --- ClickerLab: G1b elicitation + G3 clicker sessions ---

    class _ClickerStartBody(BaseModel):
        mode: str = "rip"
        tour_rel: str | None = None
        step_cap: int = 200
        time_cap_s: int = 600
        confirm: bool = False
        accept_local: bool = False

    @_http_app.post("/api/v1/gym/runs/{run_id}/elicitation")
    async def _gym_elicit(run_id: str):
        """Stage 1b: format stubs, features.json, tour draft, prior-art leads (static)."""
        import asyncio

        return await asyncio.to_thread(_clickerlab.elicit_run, run_id)

    @_http_app.get("/api/v1/clicker/engines")
    async def _clicker_engines():
        """G3 driver readiness: pywinauto / Pillow / yaml presence."""
        return _clickerlab.clicker_engines()

    @_http_app.post("/api/v1/gym/runs/{run_id}/clicker/sessions")
    async def _clicker_session_start(run_id: str, body: _ClickerStartBody):
        """Start a clicker session (executes the target - confirm + accept_local gates)."""
        import asyncio

        return await asyncio.to_thread(
            _clickerlab.clicker_start,
            run_id,
            body.mode,
            body.tour_rel,
            body.step_cap,
            body.time_cap_s,
            body.confirm,
            body.accept_local,
        )

    @_http_app.get("/api/v1/gym/runs/{run_id}/clicker/sessions/{session_id}")
    async def _clicker_session_get(run_id: str, session_id: str):
        import asyncio

        return await asyncio.to_thread(_clickerlab.clicker_status, run_id, session_id)

    @_http_app.post("/api/v1/gym/runs/{run_id}/clicker/sessions/{session_id}/stop")
    async def _clicker_session_stop(run_id: str, session_id: str):
        import asyncio

        return await asyncio.to_thread(_clickerlab.clicker_stop, run_id, session_id)

    @_http_app.post("/api/v1/gym/runs/{run_id}/clicker/sessions/{session_id}/correlate")
    async def _clicker_session_correlate(run_id: str, session_id: str):
        """Tier 3 section 5 MVP: bundle strings -> seed map (map.md). May take minutes with REA."""
        import asyncio

        return await asyncio.to_thread(_clickerlab.correlate_session, run_id, session_id)

    _http_app.mount("/mcp", mcp.http_app(path="/"))
    app = _http_app
except ImportError:
    pass  # no app when fastapi not installed; uvicorn reversing_mcp.server:app will fail


if __name__ == "__main__":
    main()
