"""ReVa lifecycle: probe, start (headless mcp-reva or Ghidra GUI), stop.

ReVa (reverse-engineering-assistant) is the separate MCP server that exposes
Ghidra over HTTP. This module manages it as a child of the backend so the
Status page gets a real start button instead of the old "start Ghidra from
the desktop" stub. Nothing is pretended:

- headless mode needs ``mcp-reva`` on PATH (``pip install
  reverse-engineering-assistant``, docs/REVA.md section 3);
- GUI mode needs ``support/ghidraRun.bat`` under ``GHIDRA_INSTALL_DIR``;
- without either, start refuses with the install hint.

Spawning is confirm-gated (a JVM + MCP listener is heavyweight); stop kills
the whole process tree via :func:`engines.kill_tree` and is idempotent.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any

from . import engines
from .logging_config import get_logger

logger = get_logger("reversing_mcp.reva")

_LOCK = threading.RLock()
_PROC: subprocess.Popen[Any] | None = None
_MODE: str | None = None


#: Fleet ReVa home (own venv - outside uv-sync reach). See D:/Dev/tools/reva/README.md.
REVA_HOME = Path(r"D:\Dev\tools\reva")
REVA_VENV_EXE = REVA_HOME / ".venv" / "Scripts" / "mcp-reva.exe"


def find_mcp_reva() -> str | None:
    """Locate the headless ReVa launcher: PATH first, then the fleet venv."""
    exe = shutil.which("mcp-reva")
    if exe:
        return exe
    if REVA_VENV_EXE.is_file():
        return str(REVA_VENV_EXE)
    return None


def find_ghidra_run() -> dict[str, Any]:
    """Locate Ghidra + its GUI launcher. Never raises."""
    gdir = os.environ.get("GHIDRA_INSTALL_DIR") or os.environ.get("GHIDRA_HOME") or ""
    candidates = [Path(gdir) / "ghidraRun.bat", Path(gdir) / "support" / "ghidraRun.bat"] if gdir else []
    run_bat = next((str(p) for p in candidates if p.is_file()), "")
    return {"dir": gdir or None, "run_bat": run_bat or None, "gui_available": bool(run_bat)}


def probe_bridge(url: str, timeout_s: float = 5.0) -> dict[str, Any]:
    """Check the ReVa/bridge HTTP endpoint. Down is normal - never raises."""
    import httpx

    try:
        r = httpx.get(f"{url.rstrip('/')}/status", timeout=timeout_s)
        r.raise_for_status()
        return {"reachable": True, "url": url, "detail": r.json()}
    except Exception as e:
        return {"reachable": False, "url": url, "detail": str(e)[:160]}


def _managed() -> dict[str, Any]:
    global _PROC, _MODE
    with _LOCK:
        proc, mode = _PROC, _MODE
    if proc is None:
        return {"running": False, "mode": None, "pid": None}
    alive = proc.poll() is None
    if not alive:
        with _LOCK:
            if _PROC is proc:
                _PROC, _MODE = None, None
        return {"running": False, "mode": mode, "pid": proc.pid, "exit_code": proc.returncode}
    return {"running": True, "mode": mode, "pid": proc.pid}


def probe(bridge_url: str) -> dict[str, Any]:
    """Full ReVa state for the Status page. Blocking (bridge HTTP) - to_thread it."""
    exe = find_mcp_reva()
    ghidra = find_ghidra_run()
    return {
        "mcp_reva": {
            "available": exe is not None,
            "path": exe,
            "install_hint": None if exe else "Fleet venv missing: see D:/Dev/tools/reva/README.md",
        },
        "ghidra": ghidra,
        "managed": _managed(),
        "bridge": probe_bridge(bridge_url),
        "message": "ReVa probe complete.",
    }


def start(mode: str = "headless", confirm: bool = False, bridge_url: str = "") -> dict[str, Any]:
    """Start ReVa headless (mcp-reva) or the Ghidra GUI. Never raises."""
    mode = (mode or "headless").lower()
    if not confirm:
        return {
            "success": False,
            "error": "Starting ReVa spawns a JVM + MCP listener. Re-run with confirm=True.",
        }
    if mode not in ("headless", "gui"):
        return {"success": False, "error": f"Unknown ReVa mode '{mode}'. Valid: headless, gui."}
    with _LOCK:
        global _PROC, _MODE
        if _PROC is not None and _PROC.poll() is None:
            return {
                "success": False,
                "busy": True,
                "pid": _PROC.pid,
                "error": f"ReVa already running (mode={_MODE}, pid={_PROC.pid}). Stop it first.",
            }
        if mode == "headless":
            exe = find_mcp_reva()
            if not exe:
                return {
                    "success": False,
                    "error": "mcp-reva not found (PATH or D:/Dev/tools/reva) - headless ReVa unavailable.",
                    "install_hint": "Fleet venv missing: see D:/Dev/tools/reva/README.md",
                }
            env = dict(os.environ)
            if find_ghidra_run()["dir"]:
                env["GHIDRA_INSTALL_DIR"] = find_ghidra_run()["dir"] or ""
            cmd = [exe]
            note = (
                "Headless ReVa starting. Point GHIDRA_BRIDGE_URL at its HTTP endpoint "
                f"(current proxy target: {bridge_url or 'unset'})."
            )
        else:
            ghidra = find_ghidra_run()
            if not ghidra["gui_available"]:
                return {
                    "success": False,
                    "error": "ghidraRun.bat not found - set GHIDRA_INSTALL_DIR to your Ghidra root.",
                }
            env = dict(os.environ)
            cmd = [str(ghidra["run_bat"])]
            note = (
                "Ghidra GUI starting (assistant mode). Open a project, load a binary, then "
                "enable the ReVa plugin listener (Edit -> Tool Options -> ReVa -> server.enabled)."
            )
        try:
            # Never inherit our stdio: under MCP stdio transport any child output
            # on stdout corrupts the JSON-RPC stream to the client.
            _PROC = subprocess.Popen(
                cmd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _MODE = mode
        except OSError as e:
            _PROC, _MODE = None, None
            return {"success": False, "error": f"Failed to spawn {' '.join(cmd)}: {e}"}
        pid = _PROC.pid if _PROC is not None else None
    logger.info("ReVa started (mode=%s, pid=%s)", mode, pid)
    return {"success": True, "mode": mode, "pid": pid, "status": "starting", "message": note}


def stop() -> dict[str, Any]:
    """Stop the managed ReVa process (whole tree). Idempotent, never raises."""
    with _LOCK:
        global _PROC, _MODE
        proc, mode = _PROC, _MODE
        _PROC, _MODE = None, None
    if proc is None or proc.poll() is not None:
        return {"success": True, "message": "ReVa not running (nothing to stop)."}
    engines.kill_tree(proc.pid)
    logger.info("ReVa stopped (mode=%s, pid=%s)", mode, proc.pid)
    return {"success": True, "mode": mode, "pid": proc.pid, "message": f"ReVa (mode={mode}) stopped; tree killed."}


def status(bridge_url: str) -> dict[str, Any]:
    """probe() plus success flag for the MCP surface."""
    out = probe(bridge_url)
    out["success"] = True
    return out
