"""External engine wrappers: Detect It Easy (diec), capa, Frida.

Same contract as rea_bridge: argv lists only (no shell=True), never raise on
engine-side failure, soft-degrade to available=False when a tool is missing.
All functions here block (subprocess / Frida session) - async callers must run
them via asyncio.to_thread.

Discovery order for each tool: env var, then PATH, then the fleet tools dir
(D:\\Dev\\tools\\<name>). Docs: docs/DIE.md, docs/CAPA.md, docs/FRIDA.md.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import psutil

from .dependencies import require
from .logging_config import get_logger

logger = get_logger("reversing_mcp.engines")

FLEET_TOOLS_DIR = Path(r"D:\Dev\tools")

# How often a running engine checks its cancel event.
CANCEL_POLL_S = 0.5


class Cancelled(Exception):
    """The caller's cancel event fired; the engine process tree was killed."""


def kill_tree(pid: int) -> None:
    """Kill a process and all its descendants (uv/pip launchers spawn python children)."""
    try:
        parent = psutil.Process(pid)
        procs = [*parent.children(recursive=True), parent]
    except psutil.NoSuchProcess:
        return
    for p in procs:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass
    psutil.wait_procs(procs, timeout=5)


def run_cancellable(
    cmd: list[str], timeout_s: float, cancel: threading.Event | None = None
) -> subprocess.CompletedProcess[str]:
    """subprocess.run(capture_output, text) that also stops when `cancel` is set.

    On timeout or cancel the whole process tree is killed (not just the launcher), then
    subprocess.TimeoutExpired or Cancelled is raised.
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            out, err = proc.communicate(timeout=CANCEL_POLL_S)
            return subprocess.CompletedProcess(cmd, proc.returncode, out, err)
        except subprocess.TimeoutExpired:
            cancelled = cancel is not None and cancel.is_set()
            if not cancelled and time.monotonic() < deadline:
                continue
            kill_tree(proc.pid)
            proc.communicate()  # reap + drain pipes
            if cancelled:
                raise Cancelled(Path(cmd[0]).name) from None
            raise subprocess.TimeoutExpired(cmd, timeout_s) from None


# ----------------------------------------------------------------- Detect It Easy


def find_diec() -> str | None:
    """Locate diec.exe: DIE_DIR env, PATH, then <fleet tools>/die."""
    candidates: list[Path] = []
    die_dir = os.environ.get("DIE_DIR")
    if die_dir:
        candidates += [Path(die_dir) / "diec.exe", Path(die_dir) / "die" / "diec.exe"]
    on_path = shutil.which("diec")
    if on_path:
        return on_path
    candidates += [FLEET_TOOLS_DIR / "die" / "die" / "diec.exe", FLEET_TOOLS_DIR / "die" / "diec.exe"]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def check_die() -> dict[str, Any]:
    """Probe Detect It Easy. Never raises."""
    info: dict[str, Any] = {"name": "Detect It Easy", "available": False, "version": None, "path": None}
    exe = find_diec()
    if not exe:
        return info
    info["path"] = exe
    try:
        proc = subprocess.run([exe, "--version"], check=False, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            info["available"] = True
            info["version"] = (proc.stdout.strip() or "unknown").splitlines()[0]
    except (subprocess.SubprocessError, OSError):
        logger.exception("diec --version probe failed")
    return info


def run_die(file_path: str, timeout_s: int = 60, cancel: threading.Event | None = None) -> dict[str, Any]:
    """Identify compiler, linker, packer, protector and libraries with `diec -j`.

    Setting `cancel` kills diec and returns {success: False, cancelled: True}.
    """
    exe = find_diec()
    if not exe:
        return (
            require("die", tool="engine:die", detail="Detect It Easy (diec) was not found on PATH or in DIE_DIR.") or {}
        )
    if not Path(file_path).is_file():
        return {"success": False, "error": f"File not found: {file_path}"}
    try:
        proc = run_cancellable([exe, "-j", file_path], max(5, min(timeout_s, 300)), cancel)
    except Cancelled:
        return {"success": False, "cancelled": True, "error": "diec cancelled (process killed)"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"diec timed out after {timeout_s}s"}
    except (subprocess.SubprocessError, OSError) as e:
        return {"success": False, "error": f"diec failed: {e}"}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": "diec returned non-JSON output", "stdout_preview": proc.stdout[:2000]}
    detections: list[dict[str, Any]] = []
    for part in data.get("detects", []):
        for v in part.get("values", []):
            detections.append(
                {
                    "filetype": part.get("filetype"),
                    "type": v.get("type"),
                    "name": v.get("name"),
                    "version": v.get("version") or None,
                    "info": v.get("info") or None,
                    "string": v.get("string"),
                }
            )
    packed = [d for d in detections if d["type"] in ("packer", "protector", "cryptor")]
    summary = ", ".join(d["string"] for d in detections) or "no signature matched"
    return {
        "success": True,
        "file_path": file_path,
        "filetypes": sorted({d["filetype"] for d in detections if d["filetype"]}),
        "detections": detections,
        "packed": bool(packed),
        "message": f"{Path(file_path).name}: {summary}",
    }


# -------------------------------------------------------------------------- capa


def find_capa() -> str | None:
    """Locate capa: CAPA_EXE env, then PATH."""
    explicit = os.environ.get("CAPA_EXE")
    if explicit and Path(explicit).is_file():
        return explicit
    return shutil.which("capa")


def capa_data_dirs() -> tuple[str | None, str | None]:
    """Rules + FLIRT signature dirs. The pip build of capa ships neither; the standalone exe embeds both.

    Order: CAPA_RULES / CAPA_SIGS env, then <fleet tools>/capa-rules and capa-sigs.
    """
    rules = os.environ.get("CAPA_RULES") or str(FLEET_TOOLS_DIR / "capa-rules")
    sigs = os.environ.get("CAPA_SIGS") or str(FLEET_TOOLS_DIR / "capa-sigs")
    return (rules if Path(rules).is_dir() else None, sigs if Path(sigs).is_dir() else None)


def check_capa() -> dict[str, Any]:
    """Probe capa. Never raises."""
    info: dict[str, Any] = {"name": "capa", "available": False, "version": None, "path": None}
    exe = find_capa()
    if not exe:
        return info
    info["path"] = exe
    rules, sigs = capa_data_dirs()
    info["rules"] = rules
    info["sigs"] = sigs
    try:
        proc = subprocess.run([exe, "--version"], check=False, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0:
            info["available"] = True
            info["version"] = (proc.stdout.strip() or proc.stderr.strip() or "unknown").splitlines()[0]
    except (subprocess.SubprocessError, OSError):
        logger.exception("capa --version probe failed")
    return info


def summarize_capa(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Reduce capa's (large) JSON to one row per matched rule."""
    rows: list[dict[str, Any]] = []
    for name, rule in (data.get("rules") or {}).items():
        meta = rule.get("meta") or {}
        matches = rule.get("matches") or []
        rows.append(
            {
                "name": meta.get("name", name),
                "namespace": meta.get("namespace"),
                "matches": len(matches),
                "attack": [a.get("id") for a in meta.get("attack") or [] if isinstance(a, dict) and a.get("id")],
                "mbc": [m.get("id") for m in meta.get("mbc") or [] if isinstance(m, dict) and m.get("id")],
            }
        )
    rows.sort(key=lambda r: (r["namespace"] or "~", r["name"]))
    return rows


def run_capa(file_path: str, timeout_s: int = 600, cancel: threading.Event | None = None) -> dict[str, Any]:
    """Run capa on a binary and return matched capabilities (namespace, ATT&CK, MBC).

    Setting `cancel` kills the capa process tree and returns {success: False, cancelled: True}.
    """
    exe = find_capa()
    if not exe:
        return require("capa", tool="engine:capa", detail="capa was not found on PATH or in CAPA_EXE.") or {}
    if not Path(file_path).is_file():
        return {"success": False, "error": f"File not found: {file_path}"}
    rules, sigs = capa_data_dirs()
    cmd = [exe, "-j"]
    if rules:
        cmd += ["-r", rules]
    if sigs:
        cmd += ["-s", sigs]
    cmd.append(file_path)
    timeout_s = max(30, min(timeout_s, 1800))
    try:
        proc = run_cancellable(cmd, timeout_s, cancel)
    except Cancelled:
        return {"success": False, "cancelled": True, "error": "capa cancelled (process tree killed)"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"capa timed out after {timeout_s}s (large binaries take minutes)"}
    except (subprocess.SubprocessError, OSError) as e:
        return {"success": False, "error": f"capa failed: {e}"}
    if proc.returncode != 0:
        tail = (proc.stderr or "")[-1500:]
        hint = ""
        if "rules not found" in tail or "signature path" in tail:
            hint = " Rules/signatures missing: set CAPA_RULES and CAPA_SIGS (docs/CAPA.md)."
        return {"success": False, "error": f"capa exit {proc.returncode}.{hint}", "stderr_tail": tail}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": "capa returned non-JSON output", "stdout_preview": proc.stdout[:2000]}
    rows = summarize_capa(data)
    namespaces = sorted({(r["namespace"] or "").split("/")[0] for r in rows if r["namespace"]})
    return {
        "success": True,
        "file_path": file_path,
        "capabilities": rows,
        "count": len(rows),
        "top_namespaces": namespaces,
        "message": f"{Path(file_path).name}: {len(rows)} capabilities matched across {len(namespaces)} areas.",
    }


# ------------------------------------------------------------------------- Frida

FRIDA_MAX_DURATION_S = 120
FRIDA_MAX_EVENTS = 5000

_TRACE_AGENT = r"""
const hooks = __HOOKS__;
const filter = __FILTER__;
for (const spec of hooks) {
  const bang = spec.indexOf('!');
  const mod = spec.slice(0, bang), fn = spec.slice(bang + 1);
  let addr;
  try { addr = Process.getModuleByName(mod).getExportByName(fn); }
  catch (e) { send({type: 'hook_error', spec, error: String(e)}); continue; }
  Interceptor.attach(addr, {
    onEnter(args) {
      let arg0 = null;
      try { arg0 = fn.endsWith('W') ? args[0].readUtf16String() : args[0].readUtf8String(); } catch (e) {}
      if (filter && !(arg0 && arg0.toLowerCase().includes(filter))) return;
      send({type: 'call', fn: spec, arg0, args: [1, 2, 3].map(i => args[i].toString()),
            tid: Process.getCurrentThreadId(), t: Date.now()});
    }
  });
  send({type: 'hooked', spec});
}
"""


_ORACLE_AGENT = r"""
// Stage-2 oracle: file-API trace with offsets. Tracks HANDLE->path on
// CreateFileW, records ReadFile/WriteFile (path, offset, size, head bytes),
// drops the mapping on CloseHandle. Overlapped I/O honored; otherwise the
// per-handle running offset is used. Sends JSON, never raw buffers.
const handles = {};
function hkey(h) { return h.toString(); }
function hexhead(ptr, n) {
  try {
    if (ptr.isNull()) return null;
    const bytes = ptr.readByteArray(Math.min(n, 64));
    if (!bytes) return null;
    return Array.from(new Uint8Array(bytes)).map(b => b.toString(16).padStart(2, '0')).join('');
  } catch (e) { return null; }
}
function hook(mod, fn, enter, leave) {
  let addr;
  try { addr = Process.getModuleByName(mod).getExportByName(fn); }
  catch (e) { send({type: 'hook_error', spec: mod + '!' + fn, error: String(e)}); return; }
  Interceptor.attach(addr, { onEnter(args) { try { enter(args); } catch (e) {} },
                             onLeave(retval) { try { leave(retval); } catch (e) {} } });
  send({type: 'hooked', spec: mod + '!' + fn});
}
const pending = {};
hook('kernel32.dll', 'CreateFileW',
  (args) => {
    try { pending.CreateFileW = args[0].readUtf16String(); } catch (e) { pending.CreateFileW = null; }
  },
  (retval) => {
    const h = retval.toString();
    if (h !== '-1' && h !== '0xffffffff' && pending.CreateFileW) handles[hkey(retval)] = {path: pending.CreateFileW, off: 0};
    send({type: 'file_open', path: pending.CreateFileW, handle: h});
  });
function rwHook(fn, op) {
  hook('kernel32.dll', fn,
    (args) => {
      const h = hkey(args[0]);
      const st = handles[h] || {path: null, off: 0};
      // OVERLAPPED layout: Internal, InternalHigh, Offset, OffsetHigh, hEvent
      let off = st.off, explicit = false;
      try {
        const ov = args[4];
        if (!ov.isNull()) { const lo = ov.add(8).readU32(), hi = ov.add(12).readU32(); off = hi * 4294967296 + lo; explicit = true; }
      } catch (e) {}
      let n = 0;
      try { n = args[2].toInt32(); } catch (e) {}
      pending[op] = {h, path: st.path, off, n, buf: args[1], explicit};
    },
    (retval) => {
      const p = pending[op];
      if (!p) return;
      // NOTE: count reported is REQUESTED bytes (transferred count needs the
      // out-param read onLeave; kept simple on purpose - see docs/FRIDA.md).
      send({type: 'file_io', op, path: p.path, handle: p.h, offset: p.off,
            requested: p.n, head: hexhead(p.buf, 64), explicit_off: p.explicit,
            tid: Process.getCurrentThreadId(), t: Date.now()});
      const st = handles[p.h];
      if (st && !p.explicit) st.off = p.off + p.n;
      pending[op] = null;
    });
}
rwHook('ReadFile', 'read');
rwHook('WriteFile', 'write');
hook('kernel32.dll', 'CloseHandle',
  (args) => { pending.CloseHandle = hkey(args[0]); },
  (retval) => {
    const h = pending.CloseHandle;
    const st = handles[h];
    // CloseHandle covers events/mutexes too: only file handles count.
    send({type: 'file_close', handle: h, path: st ? st.path : null, known: !!st});
    delete handles[h];
  });
"""


def build_oracle_agent() -> str:
    """Stage-2 file-API trace agent (no placeholders)."""
    return _ORACLE_AGENT


def check_frida() -> dict[str, Any]:
    """Probe the frida Python binding. Never raises."""
    try:
        import frida  # optional extra (dynamic)

        return {"name": "Frida", "available": True, "version": frida.__version__, "path": frida.__file__}
    except ImportError:
        return {"name": "Frida", "available": False, "version": None, "path": None}


def build_trace_agent(functions: list[str], arg0_filter: str | None) -> str:
    """JS agent hooking `module!export` specs, optionally filtering on a substring of arg 0."""
    return _TRACE_AGENT.replace("__HOOKS__", json.dumps(functions)).replace(
        "__FILTER__", json.dumps(arg0_filter.lower() if arg0_filter else None)
    )


def _run_frida(
    source: str,
    target: str | None,
    args: list[str] | None,
    pid: int | None,
    duration_s: int,
    max_events: int,
) -> dict[str, Any]:
    """Spawn or attach, load `source`, collect send() payloads until timeout, exit or max_events."""
    try:
        import frida  # optional extra (dynamic)
    except ImportError:
        return require("frida", tool="engine:frida", detail="Frida is not importable in this venv.") or {}
    if (target is None) == (pid is None):
        return {"success": False, "error": "Pass exactly one of target (spawn) or pid (attach)."}
    if target is not None and not Path(target).is_file():
        return {"success": False, "error": f"Target not found: {target}"}
    duration_s = max(1, min(duration_s, FRIDA_MAX_DURATION_S))
    max_events = max(1, min(max_events, FRIDA_MAX_EVENTS))

    events: list[Any] = []
    status: dict[str, Any] = {"hooked": [], "hook_errors": [], "script_errors": [], "dropped": 0}
    done = threading.Event()

    def on_message(message: Any, _data: Any) -> None:
        if message.get("type") == "error":
            status["script_errors"].append(message.get("description"))
            return
        payload = message.get("payload")
        if isinstance(payload, dict) and payload.get("type") == "hooked":
            status["hooked"].append(payload.get("spec"))
        elif isinstance(payload, dict) and payload.get("type") == "hook_error":
            status["hook_errors"].append(payload)
        elif len(events) < max_events:
            events.append(payload)
        else:
            status["dropped"] += 1
            done.set()

    spawned_pid: int | None = None
    session = None
    exited = threading.Event()
    process_exited = False
    started = time.monotonic()
    try:
        if target is not None:
            spawned_pid = frida.spawn([target, *(args or [])])
            session = frida.attach(spawned_pid)
        elif pid is not None:
            session = frida.attach(pid)
        else:  # unreachable: exactly-one check above
            return {"success": False, "error": "Pass exactly one of target (spawn) or pid (attach)."}
        session.on("detached", lambda *_a: (exited.set(), done.set()))
        script = session.create_script(source)
        script.on("message", on_message)
        script.load()
        if spawned_pid is not None:
            frida.resume(spawned_pid)
        done.wait(duration_s)
        # Read before cleanup: our own detach() below also fires "detached".
        process_exited = exited.is_set()
    except Exception as e:
        logger.exception("Frida session failed")
        return {"success": False, "error": f"Frida failed: {e}", "events": events, **status}
    finally:
        if session is not None:
            try:
                session.detach()
            except Exception:
                logger.debug("Frida detach failed (process probably gone)")
        if spawned_pid is not None:
            try:
                frida.kill(spawned_pid)
            except Exception:
                logger.debug("Frida kill failed (process probably gone)")
    return {
        "success": True,
        "mode": "spawn" if target is not None else "attach",
        "pid": spawned_pid if spawned_pid is not None else pid,
        "elapsed_s": round(time.monotonic() - started, 2),
        "process_exited": process_exited,
        "event_count": len(events),
        "events": events,
        **status,
    }


def frida_trace(
    functions: list[str],
    target: str | None = None,
    args: list[str] | None = None,
    pid: int | None = None,
    arg0_filter: str | None = None,
    duration_s: int = 10,
    max_events: int = 2000,
) -> dict[str, Any]:
    """Hook `module!export` functions and log calls (arg 0 read as a string)."""
    bad = [f for f in functions if "!" not in f]
    if not functions or bad:
        return {"success": False, "error": f"functions must be 'module!export' specs, got {bad or functions}"}
    return _run_frida(build_trace_agent(functions, arg0_filter), target, args, pid, duration_s, max_events)


def frida_oracle(
    target: str | None = None,
    args: list[str] | None = None,
    pid: int | None = None,
    duration_s: int = 60,
    max_events: int = 4000,
    cancel: threading.Event | None = None,
) -> dict[str, Any]:
    """Stage-2 oracle: file-API trace (open/read/write/close with offsets).

    Runs in stop-responsive slices (default 5 s): each slice spawns fresh, so
    stop_run lands within seconds instead of at duration end. Events carry
    (path, offset, requested, head-hex); transferred counts are intentionally
    requested-bytes (see agent note). Never raises.
    """
    if (target is None) == (pid is None):
        return {"success": False, "error": "Pass exactly one of target (spawn) or pid (attach)."}
    if target is not None and not Path(target).is_file():
        return {"success": False, "error": f"Target not found: {target}"}
    try:
        import frida
    except ImportError:
        return require("frida", tool="engine:frida", detail="Install the dynamic extra, then retry.") or {}
    duration_s = max(5, min(duration_s, FRIDA_MAX_DURATION_S))
    max_events = max(1, min(max_events, FRIDA_MAX_EVENTS))
    source = build_oracle_agent()
    events: list[Any] = []
    hooked: set[str] = set()
    hook_errors: list[Any] = []
    script_errors: list[str] = []
    dropped = 0
    slices = 0
    session = None
    spawned_pid: int | None = None
    exited = threading.Event()
    started = time.monotonic()
    exited_before_cleanup = False

    def on_message(message: Any, _data: Any) -> None:
        if message.get("type") == "error":
            script_errors.append(str(message.get("description"))[:300])
            return
        payload = message.get("payload")
        if isinstance(payload, dict) and payload.get("type") == "hooked":
            hooked.add(str(payload.get("spec")))
        elif isinstance(payload, dict) and payload.get("type") == "hook_error":
            hook_errors.append(payload)
        elif len(events) < max_events:
            events.append(payload)
        else:
            nonlocal dropped
            dropped += 1

    try:
        # One session for the whole capture: spawn once (or attach), then
        # reload the agent per slice so stop lands within seconds.
        if target is not None:
            spawned_pid = frida.spawn([target, *(args or [])])
            session = frida.attach(spawned_pid)
        elif pid is not None:
            session = frida.attach(pid)
        else:
            return {
                "success": False,
                "error": "Neither target nor pid provided.",
            }
        session.on("detached", lambda *_a: exited.set())
        remaining = duration_s
        while remaining > 0:
            if cancel is not None and cancel.is_set():
                return {
                    "success": False,
                    "cancelled": True,
                    "error": "Cancelled by stop.",
                    "events": events,
                    "event_count": len(events),
                }
            if exited.is_set():
                break
            quantum = min(5, remaining)
            remaining -= quantum
            slices += 1
            script = session.create_script(source)
            script.on("message", on_message)
            try:
                script.load()
                if slices == 1 and spawned_pid is not None:
                    frida.resume(spawned_pid)
                time.sleep(quantum)
            finally:
                try:
                    script.unload()
                except Exception as e:
                    logger.debug("agent unload failed: %s", e)
            if exited.is_set():
                break
        # Read BEFORE cleanup kills the spawned target (finally below).
        exited_before_cleanup = exited.is_set()
    except Exception as e:
        logger.debug("oracle session failed: %s", e)
        return {"success": False, "error": f"Oracle failed: {e}", "events": events, "event_count": len(events)}
    finally:
        if session is not None:
            try:
                session.detach()
            except Exception as e:
                logger.debug("oracle detach failed (process probably gone): %s", e)
        if spawned_pid is not None:
            try:
                frida.kill(spawned_pid)
            except Exception as e:
                logger.debug("oracle kill failed (process probably gone): %s", e)
    return {
        "success": True,
        "mode": "spawn" if target is not None else "attach",
        "pid": spawned_pid if spawned_pid is not None else pid,
        "elapsed_s": round(time.monotonic() - started, 2),
        "process_exited": exited_before_cleanup,
        "slices": slices,
        "event_count": len(events),
        "events": events,
        "hooked": sorted(hooked),
        "hook_errors": hook_errors,
        "script_errors": script_errors,
        "dropped": dropped,
        "message": f"Oracle: {len(events)} file events in {slices} slice(s).",
    }


def frida_script(
    source: str,
    target: str | None = None,
    args: list[str] | None = None,
    pid: int | None = None,
    duration_s: int = 10,
    max_events: int = 2000,
) -> dict[str, Any]:
    """Run a caller-supplied Frida JS agent; returns its send() payloads."""
    if not source.strip():
        return {"success": False, "error": "source is empty"}
    return _run_frida(source, target, args, pid, duration_s, max_events)
