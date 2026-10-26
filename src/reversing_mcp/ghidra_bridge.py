"""Ghidra forwarding layer: one MCP portmanteau in front of ReVa's ~86 tools.

ReVa (reverse-engineering-assistant) exposes Ghidra as an MCP server. Wiring it
straight into a chat client dumps every Ghidra tool into the tool list and boots
a JVM at client start. This module keeps ReVa behind a single `ghidra` tool on
reversing-mcp instead, and only starts it when asked.

Two backends, one session at a time:

- ``headless``: spawns ``mcp-reva`` (stdio MCP; PyGhidra JVM, ~1-2 min boot) as
  a child over stdin/stdout pipes. Its stderr goes to ``logs/reva-headless.log``.
- ``gui``: attaches to the ReVa plugin inside a running Ghidra GUI over
  streamable HTTP (default ``http://127.0.0.1:8080/mcp/message``, override with
  ``REVA_GUI_URL``). You watch Ghidra while the agent drives it.

Startup runs as a background task so the MCP call that triggers it returns at
once; poll ``status`` until ``state == "ready"``. Nothing is faked: calls made
before ready return a structured error with the current state.
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport

from . import reva as _reva
from .logging_config import get_logger

logger = get_logger("reversing_mcp.ghidra_bridge")

DEFAULT_GUI_URL = os.getenv("REVA_GUI_URL", "http://127.0.0.1:8080/mcp/message")
INIT_TIMEOUT_S = float(os.getenv("REVA_INIT_TIMEOUT", "300"))
CALL_TIMEOUT_S = float(os.getenv("REVA_CALL_TIMEOUT", "600"))
MAX_TEXT_CHARS = int(os.getenv("REVA_MAX_TEXT_CHARS", "60000"))
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


def _first_line(text: str | None, limit: int = 160) -> str:
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    return line if len(line) <= limit else line[: limit - 3] + "..."


def _content_to_dict(block: Any) -> dict[str, Any]:
    """Flatten one MCP content block to JSON-safe output."""
    kind = getattr(block, "type", "unknown")
    if kind == "text":
        return {"type": "text", "text": getattr(block, "text", "")}
    if kind == "image":
        data = getattr(block, "data", "") or ""
        return {"type": "image", "mime_type": getattr(block, "mimeType", None), "bytes_b64": len(data)}
    if kind == "resource":
        res = getattr(block, "resource", None)
        text = getattr(res, "text", None)
        return {"type": "resource", "uri": str(getattr(res, "uri", "")), "text": text}
    return {"type": kind}


class GhidraBridge:
    """Owns at most one ReVa client session. All public methods never raise."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._client: Client | None = None
        self._connect_task: asyncio.Task[None] | None = None
        self._mode: str | None = None
        self._target: str | None = None
        self._state = "stopped"  # stopped | starting | ready | error
        self._error: str | None = None
        self._started_at: float | None = None
        self._ready_at: float | None = None
        self._tools: list[dict[str, Any]] = []
        self._log_path: Path | None = None

    # ---------------------------------------------------------------- status

    def status(self) -> dict[str, Any]:
        now = time.time()
        out: dict[str, Any] = {
            "success": True,
            "state": self._state,
            "mode": self._mode,
            "target": self._target,
            "tool_count": len(self._tools),
            "error": self._error,
            "log_file": str(self._log_path) if self._log_path else None,
        }
        if self._started_at and self._state == "starting":
            out["elapsed_s"] = round(now - self._started_at, 1)
            out["hint"] = "Headless JVM boot takes ~1-2 min. Poll ghidra(operation='status')."
        if self._ready_at and self._started_at:
            out["startup_s"] = round(self._ready_at - self._started_at, 1)
        if self._state == "stopped":
            out["hint"] = (
                "ghidra(operation='start', mode='headless', confirm=True) to boot headless ReVa, "
                "or mode='gui' to attach to a running Ghidra with the ReVa plugin enabled."
            )
        return out

    # ----------------------------------------------------------------- start

    async def start(self, mode: str = "headless", url: str | None = None, confirm: bool = False) -> dict[str, Any]:
        mode = (mode or "headless").lower()
        if mode not in ("headless", "gui"):
            return {"success": False, "error": f"Unknown mode '{mode}'. Valid: headless, gui."}
        async with self._lock:
            if self._state in ("starting", "ready"):
                return {
                    "success": False,
                    "busy": True,
                    "error": f"Ghidra session already {self._state} (mode={self._mode}). Stop it first.",
                    **{k: v for k, v in self.status().items() if k != "success"},
                }
            env: dict[str, str] = {}
            if mode == "headless":
                if not confirm:
                    return {
                        "success": False,
                        "error": "Headless start spawns a JVM (~1-2 GB RAM, 1-2 min boot). Re-run with confirm=True.",
                    }
                exe = _reva.find_mcp_reva()
                if not exe:
                    return {
                        "success": False,
                        "error": "mcp-reva not found (PATH or D:/Dev/tools/reva).",
                        "install_hint": "See D:/Dev/tools/reva/README.md",
                    }
                env = dict(os.environ)
                gdir = _reva.find_ghidra_run()["dir"]
                if not gdir:
                    return {"success": False, "error": "GHIDRA_INSTALL_DIR is not set; headless ReVa needs it."}
                env["GHIDRA_INSTALL_DIR"] = gdir
                target = exe
            else:
                target = url or DEFAULT_GUI_URL
            try:
                if mode == "headless":
                    LOG_DIR.mkdir(parents=True, exist_ok=True)
                    log_path: Path | None = LOG_DIR / "reva-headless.log"
                    transport: Any = StdioTransport(
                        command=target, args=[], env=env, keep_alive=True, log_file=log_path
                    )
                else:
                    log_path = None
                    transport = StreamableHttpTransport(url=target)
                client = Client(transport, init_timeout=INIT_TIMEOUT_S, timeout=CALL_TIMEOUT_S)
            except Exception as e:
                return {"success": False, "mode": mode, "error": f"{type(e).__name__}: {e}"[:400]}

            self._client, self._log_path = client, log_path
            self._mode, self._target = mode, target
            self._state, self._error = "starting", None
            self._started_at, self._ready_at = time.time(), None
            self._tools = []
            self._connect_task = asyncio.create_task(self._connect(self._client))
        logger.info("Ghidra bridge starting (mode=%s, target=%s)", mode, target)
        return {
            "success": True,
            "state": "starting",
            "mode": mode,
            "target": target,
            "message": (
                "Headless ReVa booting; poll ghidra(operation='status') until state='ready'."
                if mode == "headless"
                else "Attaching to Ghidra GUI ReVa plugin; poll ghidra(operation='status')."
            ),
        }

    async def _connect(self, client: Client) -> None:
        try:
            await client.__aenter__()
            tools = await client.list_tools()
            async with self._lock:
                if self._client is not client:  # stopped/replaced while connecting
                    return
                self._tools = [
                    {"name": t.name, "description": t.description or "", "input_schema": t.inputSchema} for t in tools
                ]
                self._state, self._ready_at = "ready", time.time()
            logger.info("Ghidra bridge ready: %d tools (mode=%s)", len(self._tools), self._mode)
        except Exception as e:  # surfaced via status, never raised
            msg = f"{type(e).__name__}: {e}"[:400]
            logger.warning("Ghidra bridge connect failed: %s", msg)
            async with self._lock:
                if self._client is client:
                    self._state, self._error = "error", msg
                    if self._mode == "gui":
                        self._error += (
                            " | Is Ghidra running with a program open and the ReVa server enabled "
                            "(Edit > Tool Options > ReVa)? Override the URL with url=... or REVA_GUI_URL."
                        )
            await self._safe_close(client)

    # ------------------------------------------------------------------ stop

    async def stop(self) -> dict[str, Any]:
        async with self._lock:
            client, task, mode = self._client, self._connect_task, self._mode
            self._client, self._connect_task = None, None
            self._state, self._mode, self._target = "stopped", None, None
            self._tools, self._error = [], None
            self._started_at = self._ready_at = None
        if client is None:
            return {"success": True, "message": "No Ghidra session (nothing to stop)."}
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception) as e:
                logger.debug("Ghidra connect task ended on stop: %r", e)
        await self._safe_close(client)
        logger.info("Ghidra bridge stopped (mode=%s)", mode)
        note = "Headless JVM terminated." if mode == "headless" else "Detached; the Ghidra GUI keeps running."
        return {"success": True, "mode": mode, "message": f"Ghidra session stopped. {note}"}

    @staticmethod
    async def _safe_close(client: Client) -> None:
        try:
            await asyncio.wait_for(client.close(), timeout=15)
        except Exception as e:
            logger.debug("Ghidra client close: %s", e)

    # ------------------------------------------------------------- discovery

    def _not_ready(self) -> dict[str, Any] | None:
        if self._state == "ready" and self._client is not None:
            return None
        return {
            "success": False,
            "error": f"Ghidra session is '{self._state}', not ready.",
            **{k: v for k, v in self.status().items() if k not in ("success", "error")},
            "detail": self._error,
        }

    def list_tools(self, query: str | None = None, offset: int = 0, limit: int = 40) -> dict[str, Any]:
        if (err := self._not_ready()) is not None:
            return err
        q = (query or "").lower().strip()
        terms = q.split()
        hits = [t for t in self._tools if all(term in (t["name"] + " " + t["description"]).lower() for term in terms)]
        offset, limit = max(0, offset), max(1, min(limit, 100))
        page = hits[offset : offset + limit]
        nxt = offset + limit if offset + limit < len(hits) else None
        return {
            "success": True,
            "total": len(hits),
            "offset": offset,
            "next_offset": nxt,
            "tools": [{"name": t["name"], "summary": _first_line(t["description"])} for t in page],
            "hint": "ghidra(operation='describe', tool=...) for full schema, then operation='call'.",
        }

    def describe(self, tool: str | None) -> dict[str, Any]:
        if (err := self._not_ready()) is not None:
            return err
        if not tool:
            return {"success": False, "error": "describe needs tool=<name>."}
        for t in self._tools:
            if t["name"] == tool:
                return {"success": True, **t}
        close = [t["name"] for t in self._tools if tool.lower() in t["name"].lower()][:10]
        return {"success": False, "error": f"Unknown ReVa tool '{tool}'.", "did_you_mean": close}

    # ------------------------------------------------------------------ call

    async def call(
        self, tool: str | None, arguments: dict[str, Any] | None = None, timeout_s: float | None = None
    ) -> dict[str, Any]:
        if (err := self._not_ready()) is not None:
            return err
        if not tool:
            return {"success": False, "error": "call needs tool=<name>."}
        if not any(t["name"] == tool for t in self._tools):
            return self.describe(tool)
        client = self._client
        assert client is not None
        started = time.time()
        try:
            res = await client.call_tool_mcp(tool, arguments or {}, timeout=timeout_s or CALL_TIMEOUT_S)
        except Exception as e:
            msg = f"{type(e).__name__}: {e}"[:400]
            # A dead transport means the session is gone; reflect that in status.
            if not client.is_connected():
                async with self._lock:
                    if self._client is client:
                        self._state, self._error = "error", f"Session lost during call: {msg}"
            return {"success": False, "tool": tool, "error": msg}

        content = [_content_to_dict(b) for b in (res.content or [])]
        truncated = False
        for block in content:
            text = block.get("text")
            if isinstance(text, str) and len(text) > MAX_TEXT_CHARS:
                block["text"] = text[:MAX_TEXT_CHARS]
                block["truncated_from"] = len(text)
                truncated = True
        out: dict[str, Any] = {
            "success": not bool(res.isError),
            "tool": tool,
            "elapsed_s": round(time.time() - started, 2),
            "content": content,
        }
        if res.structuredContent is not None:
            out["structured"] = res.structuredContent
        if truncated:
            out["note"] = f"Text truncated at {MAX_TEXT_CHARS} chars (REVA_MAX_TEXT_CHARS). Narrow the query."
        return out


bridge = GhidraBridge()
