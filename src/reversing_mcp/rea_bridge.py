"""REA sidecar bridge - subprocess wrapper around the `rea` CLI (rea-agents on npm).

Tier 2 integration: reversing-mcp stays focused on static triage (strings, entropy,
PE, DKI), and delegates JS/Electron, .NET, APK, firmware, browser, and agent-driven
native queries to REA's CLI. Same evidence contracts as REA's MCP server, one
process per invocation.

Upstream docs (checked 2026-10-11, REA moves fast - re-verify before trusting):
- CLI + exit codes: https://github.com/morluto/rea/blob/main/docs/cli.md
- Setup/readiness: https://github.com/morluto/rea/blob/main/docs/installation.md
- Full guide in this repo: docs/REA.md

Safety:
- Allowlisted commands only, argv list (no shell=True).
- Large JS evidence (hundreds of MB for real apps) is truncated with a pointer
  to --snapshot / inspect-analysis-view instead of being parsed into memory.
- Runtime-capable kinds are passed through, never auto-executed beyond what the
  caller asked for. See docs/REA.md section 8 before pointing this at malware.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .dependencies import require
from .logging_config import get_logger

logger = get_logger("reversing_mcp.rea_bridge")

# Kinds exposed through rea_investigate(). Names are ours; values map to REA CLI verbs.
REA_KINDS = (
    "auto",
    "javascript",
    "native_overview",
    "native_search",
    "native_function",
    "native_decompile",
    "native_xrefs",
    "native_trace",
    "providers",
    "capabilities",
    "doctor",
)

# Kinds that never touch a target file.
TARGETLESS_KINDS = {"providers", "capabilities"}

# stdout larger than this is not JSON-parsed (real app evidence can be 100s of MB).
MAX_PARSE_BYTES = 512 * 1024
# Characters of stdout returned when truncating.
PREVIEW_CHARS = 20000


def find_rea_runner() -> list[str] | None:
    """Resolve the REA invocation prefix.

    Prefers a global `rea` install, falls back to npx (downloads on first use).
    Returns None when neither `rea` nor `npx` is on PATH.
    """
    rea_exe = shutil.which("rea")
    if rea_exe:
        return [rea_exe]
    npx_exe = shutil.which("npx")
    if npx_exe:
        return [npx_exe, "-y", "rea-agents@latest"]
    return None


def check_rea() -> dict[str, Any]:
    """Probe REA availability. Never raises - soft-degrades to available=False."""
    runner = find_rea_runner()
    if runner is None:
        return {
            "name": "REA (rea-agents)",
            "available": False,
            "version": None,
            "path": None,
            "description": "Agent-driven RE sidecar (JS/Electron/.NET/APK/firmware/browser/native). "
            "Install Node 22.19+/24.11+/26+ then run: just setup-rea (npx rea-agents setup). "
            "See docs/REA.md.",
        }
    node_exe = shutil.which("node")
    node_version: str | None = None
    if node_exe:
        try:
            proc = subprocess.run(
                [node_exe, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0:
                node_version = proc.stdout.strip()
        except (subprocess.SubprocessError, OSError):
            logger.exception("node --version probe failed")
    version: str | None = None
    try:
        proc = subprocess.run(
            [*runner, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0:
            version = (proc.stdout.strip() or proc.stderr.strip() or "unknown").splitlines()[0][:120]
    except (subprocess.SubprocessError, OSError):
        logger.exception("rea --version probe failed")
    available = version is not None
    return {
        "name": "REA (rea-agents)",
        "available": available,
        "version": version,
        "path": runner[0],
        "node_version": node_version,
        "description": "Agent-driven RE sidecar (JS/Electron/.NET/APK/firmware/browser/native). "
        "See docs/REA.md; query via rea_investigate().",
    }


def resolve_kind(kind: str, target: str | None) -> str:
    """Map `auto` to javascript (dirs/.asar) or native_overview (files)."""
    if kind != "auto":
        return kind
    if target is None:
        return "native_overview"
    p = Path(target)
    if p.is_dir() or p.suffix.lower() == ".asar":
        return "javascript"
    return "native_overview"


def build_command(
    kind: str,
    target: str | None,
    provider: str | None = None,
    query: str | None = None,
    symbol: str | None = None,
    address: str | None = None,
    snapshot_path: str | None = None,
) -> tuple[list[str] | None, str | None]:
    """Build the REA argv for a kind. Returns (argv_tail, error)."""
    if kind not in REA_KINDS:
        return None, f"Unknown kind '{kind}'. Valid: {', '.join(REA_KINDS)}."
    if kind in TARGETLESS_KINDS:
        if kind == "doctor" and provider:
            return ["doctor", "--provider", provider, "--json"], None
        return [kind, "--json"], None
    if kind == "doctor":
        if provider:
            return ["doctor", "--provider", provider, "--json"], None
        return ["doctor", "--json"], None
    if not target:
        return None, f"Kind '{kind}' requires a target path."
    provider_args: list[str] = ["--provider", provider] if provider else []
    snapshot_args: list[str] = ["--snapshot", snapshot_path] if snapshot_path else []
    if kind == "javascript":
        return ["analyze-javascript-application", target, "--json", *snapshot_args], None
    if kind == "native_overview":
        return ["analyze", target, *provider_args, "--json", *snapshot_args], None
    if kind == "native_search":
        if not query:
            return None, "Kind 'native_search' requires query (search text)."
        return ["search", target, query, *provider_args, "--json", *snapshot_args], None
    if kind == "native_function":
        if not symbol:
            return None, "Kind 'native_function' requires symbol (function name or address)."
        return ["function", target, symbol, *provider_args, "--json", *snapshot_args], None
    if kind == "native_decompile":
        if not address:
            return None, "Kind 'native_decompile' requires address (e.g. 0x1000 or main)."
        return ["decompile", target, address, *provider_args, "--json", *snapshot_args], None
    if kind == "native_xrefs":
        if not address:
            return None, "Kind 'native_xrefs' requires address (e.g. 0x1000)."
        return ["xrefs", target, address, *provider_args, "--json", *snapshot_args], None
    # native_trace
    if not query:
        return None, "Kind 'native_trace' requires query (search text to trace from)."
    return ["trace", target, query, *provider_args, "--json", *snapshot_args], None


def run_rea(
    kind: str,
    target: str | None = None,
    provider: str | None = None,
    query: str | None = None,
    symbol: str | None = None,
    address: str | None = None,
    snapshot_path: str | None = None,
    timeout_s: int = 180,
) -> dict[str, Any]:
    """Run one REA CLI invocation and return a structured envelope.

    Never raises on REA-side failure - failures come back as success=False with
    exit_code/stderr_tail. Large outputs are truncated, never fully parsed.
    """
    runner = find_rea_runner()
    if runner is None:
        blocked = require("rea", tool=f"rea_investigate:{kind}", detail="No `rea` shim and no `npx` on PATH.")
        if blocked:
            blocked["kind"] = kind
        return blocked or {"success": False, "error": "REA unavailable.", "kind": kind}
    resolved = resolve_kind(kind, target)
    argv_tail, build_error = build_command(
        resolved,
        target,
        provider=provider,
        query=query,
        symbol=symbol,
        address=address,
        snapshot_path=snapshot_path,
    )
    if argv_tail is None:
        return {"success": False, "error": build_error, "kind": resolved}
    if target is not None and resolved not in TARGETLESS_KINDS and kind != "doctor":
        if not Path(target).exists():
            return {"success": False, "error": f"Target not found: {target}", "kind": resolved}
    timeout_s = max(10, min(timeout_s, 900))
    cmd = [*runner, *argv_tail]
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        logger.warning("REA %s timed out after %ss on %s", resolved, timeout_s, target)
        return {
            "success": False,
            "kind": resolved,
            "error": f"REA timed out after {timeout_s}s (provider still analyzing is possible; "
            "retry with snapshot_path to reuse partial results).",
            "timeout_s": timeout_s,
            "hint": "For large binaries raise timeout_s; for huge JS apps save evidence and project "
            "a summary view per docs/REA.md section 5.",
        }
    except (subprocess.SubprocessError, OSError) as e:
        logger.exception("REA subprocess failed")
        return {"success": False, "kind": resolved, "error": f"REA subprocess error: {e}"}
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    stdout_bytes = len(stdout.encode("utf-8", errors="ignore"))
    stderr_tail = stderr[-2000:] if stderr else ""
    base: dict[str, Any] = {
        "kind": resolved,
        "command": [Path(c).name if c.endswith(".exe") else c for c in argv_tail],
        "exit_code": proc.returncode,
        "stdout_bytes": stdout_bytes,
        "stderr_tail": stderr_tail,
    }
    if proc.returncode != 0:
        base["success"] = False
        base["error"] = (
            "REA reported failure (exit 1: invalid input, permissions, timeout, or provider "
            f"diagnostic - run kind='doctor' to diagnose). {stderr_tail[:500]}"
        )
        if stdout_bytes > 0:
            base["stdout_preview"] = stdout[:PREVIEW_CHARS]
            base["truncated"] = stdout_bytes > PREVIEW_CHARS
        return base
    # Exit 0: completed, but result may carry partial evidence/warnings per REA contract.
    if stdout_bytes > MAX_PARSE_BYTES:
        base["success"] = True
        base["truncated"] = True
        base["stdout_preview"] = stdout[:PREVIEW_CHARS]
        base["hint"] = (
            f"Output is {stdout_bytes:,} bytes (>{MAX_PARSE_BYTES:,} parse cap). Re-run with "
            "snapshot_path to save full evidence, then project a summary/module view "
            "(rea inspect-analysis-view) per docs/REA.md section 5."
        )
        return base
    try:
        base["success"] = True
        base["truncated"] = False
        base["result"] = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError:
        base["success"] = True
        base["truncated"] = False
        base["result_text"] = stdout[:PREVIEW_CHARS]
        base["note"] = "Non-JSON output returned as text (TOON fallback)."
    return base
