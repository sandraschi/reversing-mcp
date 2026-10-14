"""ClickerLab: Gym stage 1b (elicitation) + stage 3 (clicker tour).

Spec: docs/GYM_SPEC.md sections 2b/2c. Playbook: docs/ELICITATION_AND_CLICKER.md.
Build order: G1b (no VM, static only) then G3 (executes the target).

Stage 1b is pure static analysis over triage artifacts - safe to run any time.
It writes ``elicitation/`` into the run directory: ``formats/*.md`` stubs,
``features.json``, ``tour-draft.yaml`` and ``prior-art.md``.

Stage 3 executes the target binary. Safety contract (spec section 1 + 7):

- Sessions require ``confirm=True`` (like ``engine`` frida_* ops).
- The clicker belongs in an isolated VM (virtualization-mcp, snapshot before,
  no network, no credentials). Running on this desktop needs an explicit,
  per-session ``accept_local=True`` which is recorded in the session log.
- Step cap (default 200) + wall-clock cap (default 600 s); stop kills the
  whole target process tree via :func:`engines.kill_tree`.
- UIA driving needs ``pywinauto`` (``uv sync --extra clicker``); screenshots
  need ``Pillow``. Both are lazy imports - without them the session refuses
  honestly instead of pretending.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from . import engines
from .logging_config import get_logger

logger = get_logger("reversing_mcp.clickerlab")

# ---------------------------------------------------------------------------
# Shared helpers


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def clicker_engines() -> dict[str, Any]:
    """Probe the optional G3 driver stack. Never raises."""
    out: dict[str, Any] = {}
    try:
        import pywinauto

        out["pywinauto"] = {"available": True, "version": getattr(pywinauto, "__version__", "unknown")}
    except ImportError:
        out["pywinauto"] = {"available": False, "install_hint": "uv sync --extra clicker  (pywinauto>=0.6.8)"}
    try:
        import PIL

        out["pillow"] = {"available": True, "version": getattr(PIL, "__version__", "unknown")}
    except ImportError:
        out["pillow"] = {"available": False, "install_hint": "uv sync --extra clicker  (Pillow>=10)"}
    try:
        import yaml  # noqa: F401

        out["yaml"] = {"available": True}
    except ImportError:  # pragma: no cover - pyyaml ships with most stacks
        out["yaml"] = {"available": False, "install_hint": "pip install pyyaml"}
    drive_ready = bool(out["pywinauto"]["available"])
    return {
        "engines": out,
        "drive_ready": drive_ready,
        "elicitation_ready": True,
        "message": (
            "Clicker drive ready (pywinauto present)."
            if drive_ready
            else "Elicitation ready; live driving needs uv sync --extra clicker (pywinauto)."
        ),
    }


# ---------------------------------------------------------------------------
# Stage 1b: elicitation (static, no execution)


_EXT_RE = re.compile(r"\.([a-zA-Z0-9]{2,4})\b")
_MAGIC_HITS = (
    "MZ",
    "PK",
    "RIFF",
    "ITSF",
    "%PDF",
    "\x89PNG",
    "SQLite format 3",
    "ID3",
    "OggS",
    "BM",
    "GIF8",
    "II*\x00",
    "MM\x00*",
)
_FORMAT_VERBS = ("format", "codec", "compress", "encrypt", "parser", "import", "export", "filter")
_HELP_WORDS = ("help", "about", "tip", "tutorial", "contents", "index", "search", "manual", "guide", "chm", "pdf")
_FILE_IO_VERBS = ("open", "save", "export", "import", "print", "write", "read", "load", "convert")
_DIALOG_WORDS = ("dialog", "window", "view", "options", "settings", "preferences", "wizard", "panel", "tab")
_DECO_WORDS = ("skin", "theme", "toolbar", "splash", "about", "tip of the day", "tip-of-the-day")

#: Candidate public specs for formats apps commonly touch. Leads, not truth.
KNOWN_SPECS: dict[str, dict[str, str]] = {
    "psd": {
        "name": "Adobe Photoshop file format",
        "url": "https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/",
    },
    "tif": {"name": "TIFF 6.0", "url": "https://www.itu.int/itudoc/itu-t/com16/tiff-fx/docs/tiff6.pdf"},
    "tiff": {"name": "TIFF 6.0", "url": "https://www.itu.int/itudoc/itu-t/com16/tiff-fx/docs/tiff6.pdf"},
    "jpg": {"name": "JPEG (ITU-T T.81)", "url": "https://www.w3.org/Graphics/JPEG/itu-t81.pdf"},
    "jpeg": {"name": "JPEG (ITU-T T.81)", "url": "https://www.w3.org/Graphics/JPEG/itu-t81.pdf"},
    "png": {"name": "PNG (RFC 2083)", "url": "https://www.rfc-editor.org/rfc/rfc2083.txt"},
    "pdf": {"name": "PDF 32000-1:2008", "url": "https://www.iso.org/standard/51502.html"},
    "zip": {"name": "APPNOTE.TXT (PKWARE)", "url": "https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT"},
    "chm": {
        "name": "MS ITSF/CHM (MSDN + 7-Zip/chmlib sources)",
        "url": "https://learn.microsoft.com/en-us/previous-versions/windows/desktop/htmlhelp/",
    },
    "xml": {"name": "XML 1.0 (W3C REC)", "url": "https://www.w3.org/TR/xml/"},
    "xlsx": {
        "name": "ECMA-376 OOXML",
        "url": "https://www.ecma-international.org/publications-and-standards/standards/ecma-376/",
    },
    "docx": {
        "name": "ECMA-376 OOXML",
        "url": "https://www.ecma-international.org/publications-and-standards/standards/ecma-376/",
    },
    "db": {"name": "SQLite file format", "url": "https://www.sqlite.org/fileformat.html"},
    "exe": {
        "name": "PE (MS-DOS header + COFF, MS-X)",
        "url": "https://learn.microsoft.com/en-us/windows/win32/debug/pe-format",
    },
    "dll": {
        "name": "PE (MS-DOS header + COFF, MS-X)",
        "url": "https://learn.microsoft.com/en-us/windows/win32/debug/pe-format",
    },
}


def mine_format_candidates(strings: list[str]) -> list[dict[str, Any]]:
    """Playbook A1: extensions, magic bytes and format names from strings.

    Returns candidates sorted by hit count, each with up to 3 context samples
    (80 chars around the hit, per the playbook).
    """
    ext_hits: dict[str, list[str]] = {}
    for s in strings:
        for m in _EXT_RE.finditer(s):
            ext = m.group(1).lower()
            if ext in ("exe", "dll", "00", "040", "000") or ext.isdigit():
                continue  # version noise (.323, .161) per playbook A1
            start = max(0, m.start() - 80)
            ctx = s[start : m.end() + 80 - (m.end() - m.start())][:160].strip()
            ext_hits.setdefault(ext, []).append(ctx)
            if len(ext_hits[ext]) > 50:
                ext_hits[ext] = ext_hits[ext][:50]

    magic: dict[str, int] = {}
    for s in strings:
        for mark in _MAGIC_HITS:
            if mark in s:
                magic[mark] = magic.get(mark, 0) + 1

    names: dict[str, list[str]] = {}
    for s in strings:
        low = s.lower()
        for verb in _FORMAT_VERBS:
            i = low.find(verb)
            if i >= 0:
                names.setdefault(verb, []).append(s[max(0, i - 80) : i + 80].strip())
                if len(names[verb]) > 20:
                    names[verb] = names[verb][:20]
                break

    candidates = [
        {
            "ext": ext,
            "hits": len(ctxs),
            "samples": ctxs[:3],
            "known_spec": KNOWN_SPECS.get(ext),
            "magic_seen": [m for m in magic if m],
        }
        for ext, ctxs in sorted(ext_hits.items(), key=lambda kv: -len(kv[1]))
    ]
    return candidates[:25]


def _word_hit(title_low: str, words: tuple[str, ...]) -> bool:
    """Word-boundary match: substring hits on short verbs ("read" in "thread")
    mis-prioritise everything into file I/O."""
    return re.search(r"\b(" + "|".join(words) + r")\b", title_low) is not None


def _priority(title_low: str) -> tuple[int, str]:
    if _word_hit(title_low, _FILE_IO_VERBS):
        return 1, "file I/O (oracle + tour first)"
    if _word_hit(title_low, _DIALOG_WORDS):
        return 2, "dialogs and views"
    if _word_hit(title_low, _DECO_WORDS):
        return 3, "decoration"
    return 2, "dialogs and views"


def mine_features(strings: list[str]) -> list[dict[str, Any]]:
    """Playbook A3: every help/menu string becomes one feature row."""
    seen: dict[str, dict[str, Any]] = {}
    for s in strings:
        low = s.lower()
        if len(s) < 4 or len(s) > 120:
            continue
        src = None
        if any(w in low for w in _HELP_WORDS):
            src = "help"
        elif re.search(r"[A-Z][a-z]+(\s+[A-Z][a-z]+){0,3}(\.\.\.)?$", s) and any(
            v in low for v in (*_FILE_IO_VERBS, "edit", "view", "tools", "window")
        ):
            src = "menu"
        if src is None:
            continue
        key = re.sub(r"\s+", " ", s).strip(" .&")
        if not key or key.lower() in seen:
            continue
        prio, why = _priority(low)
        seen[key.lower()] = {
            "id": f"f{len(seen) + 1:03d}",
            "title": key[:100],
            "source": src,
            "file_io": prio == 1,
            "priority": prio,
            "why": why,
        }
    feats = sorted(seen.values(), key=lambda f: (f["priority"], f["title"]))
    return feats[:200]


def inventory_help(target: Path) -> dict[str, Any]:
    """Playbook A3 inventory: .chm/.hlp/.pdf beside the EXE."""
    found: list[str] = []
    try:
        for pat in ("*.chm", "*.hlp", "*.pdf", "*manual*", "*help*"):
            for p in target.parent.glob(pat):
                if p.is_file() and p != target:
                    found.append(str(p))
    except OSError:
        pass
    return {
        "beside_exe": sorted(set(found))[:20],
        "note": "CHM is a parseable container (7-Zip extracts; chmlib reads #SYSTEM/#TOPICS) - topic tree becomes features at G1b build time.",
    }


def build_tour_draft(target: str, features: list[dict[str, Any]]) -> str:
    """Playbook A3 tour-YAML draft: priority-1 features become intent steps.

    Intent steps record *what* to reach; the G3 driver resolves live UIA paths
    (docs-seeded ordering, B2). Same schema as scripts/tour/tour.example.yaml.
    """
    lines = [
        f"# Tour draft (elicited {_now()}, status: draft - driver resolves paths live)",
        f"# Target: {target}",
        "target:",
        f"  exe: {json.dumps(target)}",
        "isolation:",
        "  network: off",
        "  credentials: none",
        "  snapshot_before: true",
        "steps:",
        "  - id: launch",
        "    action: launch",
        "    expect: null",
        "    capture: [screenshot, process_list]",
    ]
    for f in features:
        if f["priority"] != 1:
            continue
        title = f["title"].replace('"', "'")
        lines += [
            f"  - id: {f['id']}",
            f"    action: [intent: {json.dumps(title)}]",
            "    expect: null",
            "    capture: [screenshot, uia_tree]",
        ]
        if len([ln for ln in lines if ln.strip().startswith("- id:")]) > 30:
            break
    lines += [
        "  - id: quit",
        '    action: [hotkey: "alt+F4"]',
        "    expect: null",
        "    capture: [process_list]",
        "correlate_after:",
        "  seeds_from: [ocr_text, uia_labels, file_paths_written]",
        '  map_out: "maps/<target>-tour-v1.md"',
    ]
    return "\n".join(lines) + "\n"


def build_elicitation(run_path: Path, triage: dict[str, Any], target: str) -> dict[str, Any]:
    """Run stage 1b over a triaged run. Writes elicitation/ artifacts.

    Re-extracts strings from the target (min_length 5, playbook A1/A3 need the
    raw text, triage only keeps counts). Offline and deterministic.
    """
    from .analyzers import BinaryAnalyzer

    elic_dir = run_path / "elicitation"
    (elic_dir / "formats").mkdir(parents=True, exist_ok=True)

    analyzer = BinaryAnalyzer()
    raw = analyzer.extract_strings(target, min_length=5)
    texts = [s.string for s in raw if hasattr(s, "string")]

    candidates = mine_format_candidates(texts)
    for c in candidates:
        spec = c["known_spec"] or {"name": "none found yet", "url": "prior-art search (operator step)"}
        stub = (
            f"# {c['ext']} - candidate spec (elicited {_now()}, status: lead)\n"
            f"- Claimed by: {c['hits']} string hit(s) near extensions/magic\n"
            f"- Public spec: {spec['name']} <{spec['url']}>\n"
            "- Record boundaries per spec: (fill during prior-art lookup)\n"
            "- App dialect notes: (filled during oracle capture, never before)\n"
            "- Verdict: pending oracle\n"
            f"- Samples: {json.dumps(c['samples'][:2])}\n"
        )
        _atomic_write(elic_dir / "formats" / f"{c['ext']}.md", stub)

    features = mine_features(texts)
    _atomic_write(elic_dir / "features.json", json.dumps(features, indent=2))
    tour = build_tour_draft(target, features)
    _atomic_write(elic_dir / "tour-draft.yaml", tour)
    help_inv = inventory_help(Path(target))
    triage_formats = triage.get("formats_referenced", [])
    prior_art = (
        f"# Prior art ({_now()}, status: leads - operator runs REA web kinds)\n\n"
        f"Triage format refs: {', '.join(triage_formats) or '(none)'}\n"
        f"Mined candidates: {', '.join(c['ext'] for c in candidates[:10]) or '(none)'}\n\n"
        "Search leads (one pass per target, time-boxed to an hour):\n"
        "- Existing specs, SDKs, plugins, converters for the app's formats.\n"
        "- Teardown write-ups, CTF solutions, forum threads about the file format.\n"
        "- Compatible apps (anything that already reads the format is an oracle *and* a reference).\n"
        "Log dead ends here - the next target benefits from knowing what does not exist.\n"
    )
    _atomic_write(elic_dir / "prior-art.md", prior_art)
    summary = {
        "strings_scanned": len(texts),
        "format_candidates": len(candidates),
        "features": len(features),
        "priority1": sum(1 for f in features if f["priority"] == 1),
        "help_inventory": help_inv,
        "triage_formats": triage_formats,
    }
    _atomic_write(elic_dir / "elicitation.json", json.dumps(summary, indent=2))
    summary.update(
        {
            "success": True,
            "message": (
                f"Elicitation: {len(candidates)} format candidate(s), {len(features)} feature(s) "
                f"({summary['priority1']} file-I/O), tour draft + prior-art leads in elicitation/."
            ),
        }
    )
    return summary


# ---------------------------------------------------------------------------
# Stage 3: clicker sessions (execute the target - confirm + isolation gates)


_SESSIONS: dict[str, dict[str, Any]] = {}
_WORKERS: dict[str, threading.Thread] = {}
_CANCELS: dict[str, threading.Event] = {}
_LOCK = threading.RLock()

DEFAULT_STEP_CAP = 200
DEFAULT_TIME_CAP_S = 600


def _session_dir(run_path: Path, session_id: str) -> Path:
    d = run_path / "clicker" / "sessions" / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_session(sdir: Path, state: dict[str, Any]) -> None:
    tmp = sdir / "session.json.tmp"
    tmp.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, sdir / "session.json")


def _slog(sdir: Path, event: str, detail: str = "") -> None:
    with (sdir / "log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now(), "event": event, "detail": detail}) + "\n")


def start_session(
    run_path: Path,
    run_id: str,
    target: str,
    mode: str = "rip",
    tour_rel: str | None = None,
    step_cap: int = DEFAULT_STEP_CAP,
    time_cap_s: int = DEFAULT_TIME_CAP_S,
    confirm: bool = False,
    accept_local: bool = False,
) -> dict[str, Any]:
    """Start a clicker session (background worker). Never raises.

    Gates, in order: known run/target, confirm, isolation opt-out, mode sanity,
    driver presence. The worker records everything under
    ``clicker/sessions/<sid>/``.
    """
    mode = (mode or "rip").lower()
    if not Path(target).is_file():
        return {"success": False, "error": f"Target must be a local file: {target}"}
    if not confirm:
        return {
            "success": False,
            "error": "Clicker sessions execute the target. Re-run with confirm=True (VM preferred - see accept_local).",
        }
    if not accept_local:
        return {
            "success": False,
            "error": (
                "Spec section 1: the clicker runs isolated (Hyper-V VM via virtualization-mcp, snapshot "
                "before, no network, no credentials). Pass accept_local=True for an explicit, logged "
                "opt-out to drive on this desktop."
            ),
        }
    if mode not in ("rip", "tour"):
        return {"success": False, "error": f"Unknown clicker mode '{mode}'. Valid: rip, tour."}
    tour_path: Path | None = None
    if mode == "tour":
        if not tour_rel:
            return {"success": False, "error": "Tour mode needs tour_rel (e.g. elicitation/tour-draft.yaml)."}
        tour_path = (run_path / tour_rel).resolve()
        try:
            tour_path.relative_to(run_path.resolve())
        except ValueError:
            return {"success": False, "error": "Tour path escapes the run directory."}
        if not tour_path.is_file():
            return {"success": False, "error": f"No such tour: {tour_rel}"}
    probe = clicker_engines()
    if not probe["drive_ready"]:
        return {
            "success": False,
            "error": "pywinauto not installed - live driving unavailable.",
            "install_hint": probe["engines"]["pywinauto"].get("install_hint"),
            "note": "Elicitation (formats/features/tour draft) works without it.",
        }

    session_id = uuid.uuid4().hex[:12]
    with _LOCK:
        for sid, st in _SESSIONS.items():
            if st.get("run_id") == run_id and st.get("status") == "running":
                return {"success": False, "busy": True, "session_id": sid, "error": "A session is already running."}
        sdir = _session_dir(run_path, session_id)
        state: dict[str, Any] = {
            "session_id": session_id,
            "run_id": run_id,
            "target": target,
            "mode": mode,
            "tour_rel": tour_rel,
            "step_cap": max(1, min(int(step_cap), 2000)),
            "time_cap_s": max(30, min(int(time_cap_s), 3600)),
            "confirm": True,
            "accept_local": True,
            "status": "running",
            "started": _now(),
            "ended": None,
            "error": None,
            "coverage": {},
            "message": "",
        }
        _save_session(sdir, state)
        _slog(sdir, "session_started", f"mode={mode} target={target} LOCAL-RUN-OPTOUT (no VM)")
        token = uuid.uuid4().hex
        cancel = threading.Event()
        _CANCELS[token] = cancel
        worker = threading.Thread(
            target=_session_worker,
            args=(sdir, state, token, cancel),
            name=f"clicker-{session_id}",
            daemon=True,
        )
        _SESSIONS[session_id] = {**state, "_token": token, "_dir": str(sdir)}
        _WORKERS[token] = worker
        worker.start()
    return {
        "success": True,
        "session_id": session_id,
        "run_id": run_id,
        "mode": mode,
        "status": "running",
        "message": f"Clicker session {session_id} started ({mode}). Poll status; stop kills the target tree.",
    }


def get_session(run_path: Path, session_id: str) -> dict[str, Any]:
    """Session status; a running session with no live worker becomes interrupted."""
    with _LOCK:
        live = _SESSIONS.get(session_id)
    sfile = run_path / "clicker" / "sessions" / session_id / "session.json"
    if not sfile.exists():
        return {"success": False, "error": f"Unknown session: {session_id}"}
    state = json.loads(sfile.read_text(encoding="utf-8"))
    if state.get("status") == "running":
        token = (live or {}).get("_token", "")
        worker = _WORKERS.get(token)
        if worker is None or not worker.is_alive():
            state["status"] = "interrupted"
            state["ended"] = _now()
            state["error"] = "Worker gone (backend restarted?) while the session ran."
            _save_session(run_path / "clicker" / "sessions" / session_id, state)
    state["success"] = True
    return state


def stop_session(run_path: Path, session_id: str) -> dict[str, Any]:
    """Stop a session: cancel event + kill the target process tree."""
    with _LOCK:
        live = _SESSIONS.get(session_id)
        sdir = run_path / "clicker" / "sessions" / session_id
        sfile = sdir / "session.json"
        if not sfile.exists():
            return {"success": False, "error": f"Unknown session: {session_id}"}
        state = json.loads(sfile.read_text(encoding="utf-8"))
        if state.get("status") != "running":
            return {"success": True, "session_id": session_id, "message": f"Session already {state.get('status')}."}
        if live and live.get("_token"):
            cancel = _CANCELS.get(live["_token"])
            if cancel is not None:
                cancel.set()
        pid = state.get("target_pid")
        if pid:
            try:
                engines.kill_tree(int(pid))
            except (ValueError, TypeError):
                pass
        state.update({"status": "stopped", "ended": _now(), "error": "Stopped by user."})
        _save_session(sdir, state)
        _slog(sdir, "stopped", "user stop; target tree killed")
        if live:
            live["status"] = "stopped"
    return {"success": True, "session_id": session_id, "message": f"Session {session_id} stopped; target tree killed."}


def _snapshot_process_list() -> list[dict[str, Any]]:
    import psutil

    rows = []
    for p in psutil.process_iter(["pid", "name"]):
        try:
            rows.append({"pid": p.info["pid"], "name": p.info["name"] or "?"})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rows


def _dump_uia_tree(windows: list[Any]) -> list[dict[str, Any]]:
    """B1 node records: AutomationId, Name, ControlType + pattern names."""
    tree = []
    for w in windows:
        try:
            children = []
            for d in w.descendants():
                try:
                    info = d.element_info
                    patterns = []
                    try:
                        patterns = [i.interface for i in d.iface_registry] if hasattr(d, "iface_registry") else []
                    except Exception as e:
                        logger.debug("pattern probe failed: %s", e)
                        patterns = []
                    children.append(
                        {
                            "automation_id": str(getattr(info, "automation_id", "") or ""),
                            "name": str(getattr(info, "name", "") or "")[:160],
                            "control_type": str(getattr(info, "control_type", "") or ""),
                            "patterns": patterns,
                        }
                    )
                except Exception as e:
                    logger.debug("node dump skipped: %s", e)
                    continue
            tree.append({"window": str(getattr(w.element_info, "name", "") or "")[:160], "nodes": children})
        except Exception as e:
            tree.append({"window": "?", "error": str(e)[:200]})
    return tree


def _session_worker(sdir: Path, state: dict[str, Any], token: str, cancel: threading.Event) -> None:
    """Drive the target (B1 rip or B2 tour). Runs off the event loop."""
    from pywinauto import Application

    sid = state["session_id"]
    deadline = time.monotonic() + state["time_cap_s"]
    target_pid: int | None = None
    coverage: dict[str, Any] = {
        "nodes_seen": 0,
        "nodes_visited": 0,
        "menus_seen": 0,
        "menus_opened": 0,
        "dialogs_reached": 0,
        "steps": 0,
    }
    try:
        _slog(sdir, "launch", state["target"])
        proc = subprocess.Popen([state["target"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        target_pid = proc.pid
        state["target_pid"] = target_pid
        _save_session(sdir, state)
        with _LOCK:
            if sid in _SESSIONS:
                _SESSIONS[sid]["target_pid"] = target_pid

        app = Application(backend="uia")
        try:
            app.connect(process=target_pid, timeout=20)
        except Exception:
            time.sleep(3)
            app.connect(process=target_pid, timeout=20)

        if state["mode"] == "rip":
            _run_rip(sdir, state, app, coverage, cancel, deadline)
        else:
            _run_tour(sdir, state, app, coverage, cancel, deadline)

        ok, msg = (
            True,
            (
                f"{state['mode']} complete: {coverage['nodes_visited']}/{coverage['nodes_seen']} nodes, "
                f"{coverage['menus_opened']}/{coverage['menus_seen']} menus, "
                f"{coverage['dialogs_reached']} dialogs, {coverage['steps']} steps."
            ),
        )
    except engines.Cancelled:
        ok, msg = False, "Cancelled by stop; target tree killed."
    except Exception as e:
        logger.exception("Clicker session %s failed", sid)
        ok, msg = False, str(e)[:500]
    finally:
        if target_pid:
            try:
                engines.kill_tree(target_pid)
            except Exception as e:
                logger.debug("target tree kill failed: %s", e)
        with _LOCK:
            _WORKERS.pop(token, None)
            _CANCELS.pop(token, None)
            live = _SESSIONS.get(sid, {})
            record = live.get("status") != "stopped"  # else stop_session already recorded the outcome
            cur: dict[str, Any] | None = None
            if record:
                try:
                    cur = json.loads((sdir / "session.json").read_text(encoding="utf-8"))
                except (OSError, ValueError) as e:
                    logger.debug("session state unreadable: %s", e)
                    record = False
            if record and cur is not None:
                cur.update(
                    {
                        "status": "done" if ok else "failed",
                        "ended": _now(),
                        "error": None if ok else msg,
                        "message": msg,
                        "coverage": coverage,
                        "target_pid": target_pid,
                    }
                )
                _save_session(sdir, cur)
                _slog(sdir, "session_done" if ok else "session_failed", msg)
                if sid in _SESSIONS:
                    _SESSIONS[sid].update(cur)


def _cancelled(cancel: threading.Event, deadline: float) -> bool:
    if cancel.is_set():
        raise engines.Cancelled("clicker")
    if time.monotonic() > deadline:
        raise TimeoutError("time cap reached")
    return False


def _run_rip(
    sdir: Path,
    state: dict[str, Any],
    app: Any,
    coverage: dict[str, Any],
    cancel: threading.Event,
    deadline: float,
) -> None:
    """B1: BFS over the live UIA tree (GUITAR-style rip-then-walk)."""
    time.sleep(2)  # let the main window appear
    visited: set[str] = set()
    step = 0
    while step < state["step_cap"]:
        _cancelled(cancel, deadline)
        try:
            windows = app.windows()
        except Exception:
            break
        tree = _dump_uia_tree(windows)
        _atomic_write(sdir / "uia_tree.json", json.dumps(tree, indent=2))
        coverage["nodes_seen"] = sum(len(w.get("nodes", [])) for w in tree) + len(tree)
        coverage["dialogs_reached"] = len(tree)

        menus_seen = menus_opened = 0
        progressed = False
        for w in windows:
            try:
                menu = w.menu()
                items = menu.items() if menu else []
                menus_seen += len(items)
                for item in items[:20]:
                    key = f"menu:{item.text()}"
                    if key in visited:
                        continue
                    visited.add(key)
                    try:
                        item.click_input()
                        menus_opened += 1
                        progressed = True
                    except Exception as e:
                        logger.debug("menu click failed: %s", e)
                        continue
                    step += 1
                    if step >= state["step_cap"]:
                        break
            except Exception as e:
                logger.debug("menu walk failed: %s", e)
                continue
            if step >= state["step_cap"]:
                break
        coverage["menus_seen"] += menus_seen
        coverage["menus_opened"] += menus_opened

        # Walk invokable / expandable / selectable controls, cheapest first.
        try:
            for w in windows:
                for d in w.descendants():
                    _cancelled(cancel, deadline)
                    if step >= state["step_cap"]:
                        break
                    try:
                        info = d.element_info
                        key = f"{info.control_type}:{info.automation_id}:{info.name}"
                    except Exception as e:
                        logger.debug("element info failed: %s", e)
                        continue
                    if key in visited:
                        continue
                    acted = False
                    for pattern in ("invoke", "expand", "select"):
                        if not hasattr(d, pattern):
                            continue
                        try:
                            getattr(d, pattern)()
                        except Exception as e:
                            logger.debug("%s failed on %s: %s", pattern, key[:60], e)
                            continue
                        acted = True
                        break
                    if acted:
                        visited.add(key)
                        step += 1
                        progressed = True
                        time.sleep(0.3)
                if step >= state["step_cap"]:
                    break
        except engines.Cancelled:
            raise
        except Exception as e:
            logger.debug("control walk pass failed: %s", e)

        coverage["steps"] = step
        coverage["nodes_visited"] = len(visited)
        state["coverage"] = dict(coverage)
        _save_session(sdir, state)
        _slog(sdir, "rip_pass", f"step={step} visited={len(visited)} menus={menus_opened}")
        if not progressed:
            break
    _atomic_write(
        sdir / "rip.json",
        json.dumps(
            {
                "coverage": coverage,
                "deterministic_note": "re-running the same build must produce the same walk (flakes are bugs, file them).",
            },
            indent=2,
        ),
    )
    _atomic_write(sdir / "process_list.json", json.dumps(_snapshot_process_list(), indent=2))


def _run_tour(
    sdir: Path,
    state: dict[str, Any],
    app: Any,
    coverage: dict[str, Any],
    cancel: threading.Event,
    deadline: float,
) -> None:
    """B2: execute a tour-YAML draft; intent steps resolve against the live tree."""
    import yaml

    run_root = sdir.parents[2]  # sessions/<sid> -> sessions -> clicker -> run
    tour_file = (run_root / (state["tour_rel"] or "")).resolve()
    tour = yaml.safe_load(tour_file.read_text(encoding="utf-8")) or {}
    steps = tour.get("steps", [])
    results = []
    step = 0
    for tstep in steps:
        _cancelled(cancel, deadline)
        if step >= state["step_cap"]:
            break
        sid_step = str(tstep.get("id", f"s{step}"))
        action = tstep.get("action")
        expect = tstep.get("expect")
        capture = tstep.get("capture", [])
        outcome = _exec_action(app, action, sdir, sid_step, capture)
        ok_expect = True
        if expect:
            try:
                titles = " ".join(w.window_text() for w in app.windows())
                ok_expect = str(expect).lower() in titles.lower()
            except Exception:
                ok_expect = False
        results.append({"id": sid_step, "action": action, "outcome": outcome, "expect": expect, "expect_ok": ok_expect})
        _slog(sdir, "tour_step", f"{sid_step}: {outcome} expect_ok={ok_expect}")
        step += 1
        coverage["steps"] = step
        coverage["nodes_visited"] = step
        state["coverage"] = dict(coverage)
        _save_session(sdir, state)
    _atomic_write(sdir / "tour-results.json", json.dumps(results, indent=2, default=str))
    _atomic_write(sdir / "uia_tree.json", json.dumps(_dump_uia_tree(app.windows()), indent=2, default=str))
    _atomic_write(sdir / "process_list.json", json.dumps(_snapshot_process_list(), indent=2))


def _exec_action(app: Any, action: Any, sdir: Path, sid_step: str, capture: list[str]) -> str:
    """Execute one tour action. Returns a short outcome string; never raises."""
    try:
        acts = action if isinstance(action, list) else [action]
        notes = []
        for a in acts:
            if a == "launch":
                notes.append("launched (session start)")
            elif isinstance(a, dict) and "intent" in a:
                notes.append(_resolve_intent(app, str(a["intent"])))
            elif isinstance(a, dict) and "click_menu" in a:
                notes.append(_resolve_intent(app, f"{a.get('click_menu', '')} {a.get('click_item', '')}"))
            elif isinstance(a, dict) and "hotkey" in a:
                app.top_window().type_keys(str(a["hotkey"]))
                notes.append(f"hotkey {a['hotkey']}")
            elif isinstance(a, dict) and "key" in a:
                app.top_window().type_keys(f"{{{a['key']}}}")
                notes.append(f"key {a['key']}")
            elif isinstance(a, dict) and "type" in a:
                app.top_window().type_keys(str(a["type"]), with_spaces=True)
                notes.append(f"typed {len(str(a['type']))} chars")
            else:
                notes.append(f"skipped unhandled action {json.dumps(a)[:80]}")
        if "screenshot" in capture:
            _capture_shot(app, sdir / f"{sid_step}.png")
        return "; ".join(notes)[:300]
    except Exception as e:
        return f"action failed: {e!s}"[:200]


def _resolve_intent(app: Any, intent: str) -> str:
    """B2 resolution: first live control whose name contains an intent keyword wins."""
    words = [w.lower() for w in re.findall(r"[A-Za-zÄÖÜäöüß]{3,}", intent)]
    try:
        for w in app.windows():
            for d in w.descendants():
                try:
                    name = str(d.element_info.name or "").lower()
                except Exception as e:
                    logger.debug("intent name probe failed: %s", e)
                    continue
                if name and any(kw in name for kw in words):
                    for meth in ("invoke", "click_input", "select"):
                        if hasattr(d, meth):
                            try:
                                getattr(d, meth)()
                                time.sleep(0.5)
                                return f"intent '{intent[:40]}' -> '{name[:40]}' via {meth}"
                            except Exception as e:
                                logger.debug("intent %s via %s failed: %s", intent[:40], meth, e)
                                continue
    except Exception as e:
        return f"intent resolve failed: {e!s}"[:120]
    return f"intent '{intent[:40]}' unresolved (no live match)"


def elicit_run(run_id: str) -> dict[str, Any]:
    """Stage 1b for a run: needs triage first. Blocking - call via to_thread."""
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    triage_file = run_path / "triage" / "triage.json"
    if not triage_file.exists():
        return {"success": False, "error": "Elicitation needs triage first (advance the run to triage)."}
    triage = json.loads(triage_file.read_text(encoding="utf-8"))
    return build_elicitation(run_path, triage, state["target"])


def clicker_start(
    run_id: str,
    mode: str = "rip",
    tour_rel: str | None = None,
    step_cap: int = DEFAULT_STEP_CAP,
    time_cap_s: int = DEFAULT_TIME_CAP_S,
    confirm: bool = False,
    accept_local: bool = False,
) -> dict[str, Any]:
    """Validate the run, then hand to start_session."""
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    return start_session(run_path, run_id, state["target"], mode, tour_rel, step_cap, time_cap_s, confirm, accept_local)


def clicker_status(run_id: str, session_id: str) -> dict[str, Any]:
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    return get_session(run_path, session_id)


def clicker_stop(run_id: str, session_id: str) -> dict[str, Any]:
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    return stop_session(run_path, session_id)


def _capture_shot(app: Any, path: Path) -> None:
    try:
        from PIL import ImageGrab

        _ = ImageGrab  # re-export guard: Pillow present means capture_as_image can save
    except ImportError:
        return
    try:
        shot = app.top_window().capture_as_image()
        if shot is not None:
            shot.save(str(path))
    except Exception as e:
        logger.debug("screenshot capture failed: %s", e)
