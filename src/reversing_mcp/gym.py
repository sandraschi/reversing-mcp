"""Reversing Gym G1: job runner + stages 0 (intake), 1 (triage), 4 (assessment).

Spec: docs/GYM_SPEC.md. Stages 2,3,5,6,7,8 are scaffolded as
"pending-spec" — advance() refuses them honestly instead of pretending.

Runs live in gym/runs/<run-id>/ (gitignored): run.json (state machine),
one subdirectory per completed stage, log.jsonl. Stages are idempotent:
re-running a completed stage reuses its artifacts unless forced.

Stages run in a background worker thread: advance_run() marks the stage
"running", starts the worker and returns at once; callers poll get_run(). Each
attempt carries a token so a stopped attempt that finishes late cannot
overwrite a newer one. stop_run() also fires the attempt's cancel event, which
kills the running engine's process tree (engines.run_cancellable) and aborts the
stage. A stage left "running" with no live worker (backend
restarted) is reported as "interrupted" and is retried by the next advance.
The REST/MCP layers still call these functions via asyncio.to_thread because
the bookkeeping does file I/O (2026-10-12 /ghidra/status incident).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Any

from . import engines
from .analyzers import BinaryAnalyzer
from .logging_config import get_logger

logger = get_logger("reversing_mcp.gym")

STAGES = [
    "intake",
    "triage",
    "oracle_capture",
    "clicker_tour",
    "assessment",
    "recovery",
    "ui_build",
    "round_trip",
    "compare",
]
G1_STAGES = ["intake", "triage", "oracle_capture", "assessment"]
PENDING_SPEC = [s for s in STAGES if s not in G1_STAGES]

#: Stage-2 defaults (overridable per advance call, stored in stage_params).
ORACLE_DEFAULT_DURATION_S = int(os.environ.get("GYM_ORACLE_DURATION_S", "60"))

# capa is slow on real apps (Digibib5, 4.7 MB Delphi: 2511 s on 2026-10-12). Default keeps
# triage interactive; raise via env for a full capa pass.
CAPA_TIMEOUT_S = int(os.environ.get("GYM_CAPA_TIMEOUT_S", "300"))

_runs_dir: Path | None = None

# Guards every run.json read-modify-write and the worker registry (one backend process).
_lock = threading.RLock()
# attempt token -> thread executing that stage attempt
_workers: dict[str, threading.Thread] = {}
# attempt token -> cancel event; stop_run sets it and the engine process tree is killed
_cancels: dict[str, threading.Event] = {}


def runs_dir() -> Path:
    global _runs_dir
    if _runs_dir is None:
        root = Path(__file__).resolve().parents[2]
        _runs_dir = root / "gym" / "runs"
        _runs_dir.mkdir(parents=True, exist_ok=True)
    return _runs_dir


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _log(run_path: Path, event: str, detail: str = "") -> None:
    with (run_path / "log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now(), "event": event, "detail": detail}) + "\n")


def _worker_alive(token: str | None) -> bool:
    t = _workers.get(token or "")
    return t is not None and t.is_alive()


def _load(run_id: str) -> tuple[Path, dict] | tuple[None, dict]:
    """Load run state; a 'running' stage whose worker is gone becomes 'interrupted'."""
    run_path = runs_dir() / run_id
    state_file = run_path / "run.json"
    with _lock:
        if not state_file.exists():
            return None, {"error": f"Unknown run: {run_id}"}
        state = json.loads(state_file.read_text(encoding="utf-8"))
        changed = False
        for stage, info in state["stages"].items():
            if info["status"] == "running" and not _worker_alive(info.get("attempt")):
                info.update(
                    {
                        "status": "interrupted",
                        "ended": _now(),
                        "error": "Worker gone (backend restarted?) while the stage ran. Advance to retry.",
                    }
                )
                _log(run_path, "stage_interrupted", stage)
                changed = True
        if changed:
            _save(run_path, state)
        return run_path, state


def _save(run_path: Path, state: dict) -> None:
    # Atomic: pollers must never read a half-written run.json.
    tmp = run_path / "run.json.tmp"
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(tmp, run_path / "run.json")


def _running_stage(state: dict) -> str | None:
    return next((s for s, i in state["stages"].items() if i["status"] == "running"), None)


def create_run(target: str, test_files: list[str] | None = None, notes: str = "") -> dict[str, Any]:
    """Stage 0 (intake): validate target, hash it, lay out the run directory."""
    target_path = Path(target)
    if not target_path.exists() or not target_path.is_file():
        return {"success": False, "error": f"Target must be a local file: {target}"}
    if target_path.suffix.lower() not in (".exe", ".lnk", ".dll", ".msi"):
        return {
            "success": False,
            "error": f"Gym takes Windows executables (.exe/.lnk/.dll/.msi), got {target_path.suffix or 'no extension'}",
        }
    run_id = uuid.uuid4().hex[:12]
    run_path = runs_dir() / run_id
    run_path.mkdir(parents=True)
    for stage in STAGES:
        (run_path / stage).mkdir()
    test_list = [t for t in (test_files or []) if Path(t).exists()]
    state = {
        "id": run_id,
        "target": str(target_path),
        "sha256": _sha256(target_path),
        "size": target_path.stat().st_size,
        "test_files": test_list,
        "test_files_missing": [t for t in (test_files or []) if not Path(t).exists()],
        "notes": notes,
        "created": _now(),
        "stages": {s: {"status": "pending", "started": None, "ended": None, "error": None} for s in STAGES},
        "gate": None,
        "message": "",
    }
    _save(run_path, state)
    _log(run_path, "created", f"target={target_path} sha256={state['sha256'][:16]}…")
    return _run_stage(run_path, state, "intake")


def _build_oracle(events: list[Any], target: str) -> dict[str, Any]:
    """Fold file_io events into a per-path read/write offset map.

    The map (path -> [{offset, requested, head}]) is the evidence: which file
    regions the target touched, in what order. Content is head-bytes only
    (64 B hex), never full buffers.
    """
    files: dict[str, dict[str, Any]] = {}
    opens = closes = 0
    for ev in events:
        if not isinstance(ev, dict):
            continue
        kind = ev.get("type")
        if kind == "file_open":
            opens += 1
            continue
        if kind == "file_close":
            if ev.get("known", True):
                closes += 1
            continue
        if kind != "file_io":
            continue
        path = str(ev.get("path") or "(unknown)")
        slot = files.setdefault(path, {"reads": [], "writes": [], "total_read": 0, "total_written": 0})
        rec = {"offset": ev.get("offset"), "requested": ev.get("requested"), "head": ev.get("head")}
        if ev.get("op") == "write":
            slot["writes"].append(rec)
            slot["total_written"] += int(ev.get("requested") or 0)
        else:
            slot["reads"].append(rec)
            slot["total_read"] += int(ev.get("requested") or 0)
    flags = []
    for path, slot in files.items():
        low = path.lower()
        if slot["writes"] and low.endswith((".exe", ".dll", ".sys", ".scr")):
            flags.append(f"writes executable: {path}")
        if slot["writes"] and ("\\windows\\" in low or low.startswith("c:\\windows")):
            flags.append(f"writes into Windows dir: {path}")
        if "sam" in low or "security" in low.split("\\")[-1:]:
            flags.append(f"touches credential hive path: {path}")
    return {
        "target": target,
        "files": files,
        "file_count": len(files),
        "opens": opens,
        "closes": closes,
        "flags": flags,
        "message": f"Oracle: {len(files)} file(s), "
        f"{sum(len(s['reads']) for s in files.values())} reads, "
        f"{sum(len(s['writes']) for s in files.values())} writes." + (f" FLAGS: {'; '.join(flags)}" if flags else ""),
    }


def _stage_oracle(run_path: Path, state: dict, cancel: threading.Event | None = None) -> dict[str, Any]:
    """Stage 2: execute the target under the Frida file-API oracle.

    Confirm-gated like the clicker (this RUNS the binary): advance must pass
    confirm=True + accept_local=True (logged VM opt-out), stored in
    state["stage_params"]["oracle_capture"]. Duration-capped, stop-responsive.
    """
    params = (state.get("stage_params") or {}).get("oracle_capture", {})
    if not params.get("confirm"):
        return {
            "refused": True,
            "error": "Oracle executes the target. Advance with confirm=True (and accept_local=True).",
        }
    if not params.get("accept_local"):
        return {
            "refused": True,
            "error": "Spec section 1: detonation belongs in an isolated VM (virtualization-mcp). "
            "Pass accept_local=True for a logged opt-out to run on this desktop.",
        }
    target = state["target"]
    duration_s = max(5, min(int(params.get("duration_s", ORACLE_DEFAULT_DURATION_S)), 120))
    _log(run_path, "oracle_start", f"{target} {duration_s}s LOCAL-RUN-OPTOUT (no VM)")
    res = engines.frida_oracle(target, duration_s=duration_s, cancel=cancel)
    if res.get("cancelled"):
        return {"error": "Cancelled by stop."}
    if not res.get("success"):
        return {"error": res.get("error", "Oracle failed")}
    oracle = _build_oracle(res.get("events", []), target)
    oracle.update(
        {
            "pid": res.get("pid"),
            "elapsed_s": res.get("elapsed_s"),
            "process_exited": res.get("process_exited"),
            "hooked": res.get("hooked"),
            "hook_errors": res.get("hook_errors"),
            "dropped": res.get("dropped"),
        }
    )
    (run_path / "oracle" / "oracle.json").parent.mkdir(parents=True, exist_ok=True)
    (run_path / "oracle" / "oracle.json").write_text(json.dumps(oracle, indent=2), encoding="utf-8")
    _log(run_path, "oracle_done", oracle["message"])
    oracle["message"] = oracle["message"] + f" Full map in oracle/oracle.json ({res.get('event_count')} events)."
    return oracle


_STAGE_FNS = {
    "intake": lambda run_path, state, _cancel: _stage_intake(run_path, state),
    "triage": lambda run_path, state, cancel: _stage_triage(run_path, state, cancel),
    "oracle_capture": lambda run_path, state, cancel: _stage_oracle(run_path, state, cancel),
    "assessment": lambda run_path, state, _cancel: _stage_assessment(run_path, state),
}


def _begin_stage(run_path: Path, state: dict, stage: str) -> str:
    """Mark `stage` running under a fresh attempt token. Caller holds _lock and must
    register the executing thread in _workers[token] before releasing it."""
    token = uuid.uuid4().hex
    state["stages"][stage].update(
        {"status": "running", "started": _now(), "ended": None, "error": None, "message": None, "attempt": token}
    )
    _cancels[token] = threading.Event()
    _save(run_path, state)
    _log(run_path, "stage_started", stage)
    return token


def _execute_stage(run_path: Path, stage: str, token: str) -> tuple[bool, dict[str, Any]]:
    """Run the stage body (slow, no lock held). State is re-read: bodies only read it."""
    with _lock:
        state = json.loads((run_path / "run.json").read_text(encoding="utf-8"))
        cancel = _cancels.get(token)
    try:
        result = _STAGE_FNS[stage](run_path, state, cancel)
        # Gate refusals are routine, not crashes: no traceback, failed status.
        if isinstance(result, dict) and result.get("refused"):
            return False, {"error": result.get("error", "Refused.")}
        return True, result
    except engines.Cancelled:
        return False, {"error": "Cancelled by stop; engine process killed."}
    except Exception as e:
        logger.exception("Gym stage %s failed for run %s", stage, state["id"])
        return False, {"error": str(e)}


def _finish_stage(run_path: Path, stage: str, token: str, ok: bool, result: dict[str, Any]) -> dict[str, Any]:
    """Record the outcome, unless this attempt was stopped or superseded meanwhile."""
    with _lock:
        _workers.pop(token, None)
        _cancels.pop(token, None)
        state = json.loads((run_path / "run.json").read_text(encoding="utf-8"))
        info = state["stages"][stage]
        if info.get("attempt") != token or info["status"] != "running":
            _log(run_path, "stage_result_discarded", f"{stage}: attempt no longer current ({info['status']})")
            return {
                "success": False,
                "run_id": state["id"],
                "stage": stage,
                "error": f"Stage '{stage}' was {info['status']} before this attempt finished; result discarded.",
            }
        if ok:
            info.update({"status": "done", "ended": _now(), "message": result.get("message")})
            if stage == "assessment":
                state["gate"] = {"stage": "assessment", "decision": None, "at": None}
            _log(run_path, "stage_done", stage)
            result.update({"success": True, "run_id": state["id"], "stage": stage})
        else:
            info.update({"status": "failed", "ended": _now(), "error": result["error"]})
            _log(run_path, "stage_failed", f"{stage}: {result['error']}")
            result = {"success": False, "run_id": state["id"], "stage": stage, "error": result["error"]}
        state["message"] = result.get("message") or result.get("error") or ""
        _save(run_path, state)
        return result


def _run_stage(run_path: Path, state: dict, stage: str) -> dict[str, Any]:
    """Run a stage in the calling thread and return its result (intake; background=False)."""
    with _lock:
        token = _begin_stage(run_path, state, stage)
        _workers[token] = threading.current_thread()
    ok, result = _execute_stage(run_path, stage, token)
    return _finish_stage(run_path, stage, token, ok, result)


def _stage_worker(run_path: Path, stage: str, token: str) -> None:
    try:
        ok, result = _execute_stage(run_path, stage, token)
        _finish_stage(run_path, stage, token, ok, result)
    except Exception:
        # Run dir vanished or similar: the stage stays 'running' until _load marks it interrupted.
        logger.exception("Gym worker for %s/%s crashed", run_path.name, stage)
        with _lock:
            _workers.pop(token, None)
            _cancels.pop(token, None)


def _stage_intake(run_path: Path, state: dict) -> dict[str, Any]:
    (run_path / "intake" / "target.json").write_text(
        json.dumps(
            {
                "target": state["target"],
                "sha256": state["sha256"],
                "size": state["size"],
                "test_files": state["test_files"],
                "test_files_missing": state["test_files_missing"],
                "notes": state["notes"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "message": f"Intake complete: {Path(state['target']).name} "
        f"({state['size']:,} bytes, {len(state['test_files'])} test file(s))."
    }


def _stage_triage(run_path: Path, state: dict, cancel: threading.Event | None = None) -> dict[str, Any]:
    target = state["target"]
    analyzer = BinaryAnalyzer()
    triage: dict[str, Any] = {"target": target}

    def check_cancel() -> None:
        if cancel is not None and cancel.is_set():
            raise engines.Cancelled("triage")

    # engines.run_* contract: success / error; DiE adds detections + packed, capa adds capabilities.
    # A stop kills the running engine (cancelled=True) and aborts the rest of the stage.
    die = engines.run_die(target, timeout_s=120, cancel=cancel)
    check_cancel()
    die["available"] = bool(die.get("success"))
    triage["die"] = die
    capa = engines.run_capa(target, timeout_s=CAPA_TIMEOUT_S, cancel=cancel)
    check_cancel()
    capa["available"] = bool(capa.get("success"))
    triage["capa"] = {
        "summary": capa.get("capabilities", []),
        "available": capa["available"],
        "error": capa.get("error"),
    }
    try:
        triage["pe"] = analyzer.analyze_pe_file(target)
    except Exception as e:
        triage["pe"] = {"error": str(e)}
    try:
        ent = analyzer.analyze_entropy(target)
        triage["entropy"] = {"overall": ent.get("overall"), "compressed": len(ent.get("compressed", []))}
    except Exception as e:
        triage["entropy"] = {"error": str(e)}
    try:
        strings = analyzer.extract_strings(target, min_length=6)
        texts = [s.string for s in strings if hasattr(s, "string")]
        triage["strings_count"] = len(texts)
        exts = sorted({w.lower() for t in texts for w in re.findall(r"\.[a-zA-Z0-9]{2,4}\b", t)} - {".exe", ".dll"})[
            :20
        ]
        triage["formats_referenced"] = exts
    except Exception as e:
        triage["strings_count"] = -1
        triage["formats_referenced"] = []
        triage["strings_error"] = str(e)

    (run_path / "triage" / "triage.json").write_text(json.dumps(triage, indent=2, default=str), encoding="utf-8")
    parts = [
        f"DiE: {'answered' if die.get('available') else 'absent'}",
        "capa: "
        + ("answered" if capa.get("available") else "timed out" if "timed out" in str(capa.get("error")) else "absent"),
        f"strings: {triage.get('strings_count', '?')}",
    ]
    return {"triage": triage, "message": f"Triage complete ({', '.join(parts)}). See triage/triage.json."}


def _assess_dimension(name: str, status: str, reason: str) -> dict[str, str]:
    assert status in ("green", "amber", "red", "unknown")
    return {"dimension": name, "status": status, "reason": reason}


def _stage_assessment(run_path: Path, state: dict) -> dict[str, Any]:
    triage_file = run_path / "triage" / "triage.json"
    if not triage_file.exists():
        return {
            "success": False,
            "run_id": state["id"],
            "error": "Assessment needs triage first (run advance from triage).",
        }
    triage = json.loads(triage_file.read_text(encoding="utf-8"))

    die = triage.get("die", {})
    die_text = json.dumps(die).lower()
    if die.get("packed") or any(w in die_text for w in ["upx", "aspack", "themida", "vmprotect", "obsidium", "enigma"]):
        binary = _assess_dimension("Binary", "amber", "Packer/protector indicated by DiE — confirm before cloning.")
    elif die.get("available"):
        binary = _assess_dimension("Binary", "green", "Unpacked, compiler identified by DiE.")
    else:
        binary = _assess_dimension("Binary", "unknown", "DiE absent — compiler/packer unknown.")

    capa = triage.get("capa", {})
    if capa.get("available") and capa.get("summary"):
        logic = _assess_dimension("Logic", "amber", "capa capabilities present — review summary for effort.")
    elif capa.get("available"):
        logic = _assess_dimension("Logic", "green", "capa answered with no red-flag capabilities.")
    else:
        why = capa.get("error") or "capa absent"
        logic = _assess_dimension("Logic", "unknown", f"{why} — effort unknown, needs stage 5.")

    anti_vm = sorted(
        {
            r.get("name", "")
            for r in capa.get("summary", [])
            if str(r.get("namespace") or "").startswith("anti-analysis/anti-vm")
        }
    )
    if anti_vm:
        oracle = _assess_dimension(
            "Oracle",
            "amber",
            f"capa found anti-VM checks ({'; '.join(anti_vm[:3])}) — the VM clicker may be detected.",
        )
    else:
        oracle = _assess_dimension("Oracle", "unknown", "VM plumbing unverified (stage 2).")

    fmt = triage.get("formats_referenced", [])
    if fmt:
        apas = ", ".join(fmt[:8])
        format_d = _assess_dimension("Format", "amber", f"Test-file I/O not yet traced; strings reference: {apas}.")
    else:
        format_d = _assess_dimension("Format", "unknown", "No format hints in strings — needs oracle capture.")

    dims = [
        binary,
        _assess_dimension("UI coverage", "unknown", "Needs clicker tour (stage 3)."),
        format_d,
        logic,
        oracle,
    ]
    reds = sum(1 for d in dims if d["status"] == "red")
    ambers = sum(1 for d in dims if d["status"] in ("amber", "unknown"))
    verdict = "red" if reds else ("amber" if ambers else "green")
    assessment = {
        "dimensions": dims,
        "verdict": verdict,
        "message": f"Assessment: {verdict.upper()} — approve the gate to continue past triage.",
    }
    (run_path / "assessment" / "assessment.json").write_text(json.dumps(assessment, indent=2), encoding="utf-8")
    return {"assessment": assessment, "message": assessment["message"]}


def advance_run(
    run_id: str,
    decision: str | None = None,
    background: bool = True,
    confirm: bool = False,
    accept_local: bool = False,
    duration_s: int = ORACLE_DEFAULT_DURATION_S,
) -> dict[str, Any]:
    """Start the next G1 stage (in a background worker by default) or record the gate decision.

    Returns at once with status 'running'; poll get_run() for the outcome. A run with a
    stage still running is busy. Failed / stopped / interrupted stages are retried.
    background=False runs the stage in the calling thread and returns its result.
    oracle_capture executes the target: pass confirm=True + accept_local=True
    (logged VM opt-out) or it refuses honestly.
    """
    with _lock:
        run_path, state = _load(run_id)
        if run_path is None:
            return {"success": False, "error": state.get("error")}
        running = _running_stage(state)
        if running:
            return {
                "success": False,
                "run_id": run_id,
                "stage": running,
                "busy": True,
                "error": f"Stage '{running}' is still running in the background. Poll status, or stop the run.",
            }
        next_stage = next((s for s in G1_STAGES if state["stages"][s]["status"] != "done"), None)
        if next_stage == "oracle_capture":
            params = state.setdefault("stage_params", {}).setdefault("oracle_capture", {})
            params.update({"confirm": confirm, "accept_local": accept_local, "duration_s": duration_s})
            _save(run_path, state)
        if next_stage is None:
            if state.get("gate") and state["gate"].get("decision") is None:
                if decision in ("go", "no-go"):
                    state["gate"].update({"decision": decision, "at": _now()})
                    _save(run_path, state)
                    _log(run_path, "gate_decision", decision)
                    return {
                        "success": True,
                        "run_id": run_id,
                        "stage": "assessment",
                        "message": f"Gate recorded: {decision}.",
                    }
                return {
                    "success": False,
                    "run_id": run_id,
                    "error": "G1 complete. Assessment gate awaits decision: advance with decision='go'|'no-go'.",
                }
            return {"success": False, "run_id": run_id, "error": "G1 complete (stages 3,5,6,7,8 are pending-spec)."}
        if background:
            token = _begin_stage(run_path, state, next_stage)
            worker = threading.Thread(
                target=_stage_worker,
                args=(run_path, next_stage, token),
                name=f"gym-{run_id}-{next_stage}",
                daemon=True,
            )
            _workers[token] = worker
            worker.start()
            return {
                "success": True,
                "run_id": run_id,
                "stage": next_stage,
                "status": "running",
                "message": f"Stage '{next_stage}' started in the background. Poll status for the result.",
            }
    return _run_stage(run_path, state, next_stage)  # background=False: outside the lock


def stop_run(run_id: str) -> dict[str, Any]:
    """Stop the running stage: mark it stopped and fire its cancel event, which kills the
    engine process tree (DiE / capa) within about a second. The worker's result is discarded."""
    with _lock:
        run_path, state = _load(run_id)
        if run_path is None:
            return {"success": False, "error": state.get("error")}
        stopped = []
        for stage, info in state["stages"].items():
            if info["status"] == "running":
                info.update({"status": "stopped", "ended": _now(), "error": "Stopped by user."})
                cancel = _cancels.get(info.get("attempt") or "")
                if cancel is not None:
                    cancel.set()
                stopped.append(stage)
        _save(run_path, state)
        _log(run_path, "stopped", ",".join(stopped))
    detail = f" Stopped stage: {', '.join(stopped)}; advance to retry it." if stopped else ""
    return {"success": True, "run_id": run_id, "message": f"Run {run_id} stopped.{detail}"}


def get_run(run_id: str) -> dict[str, Any]:
    run_path, state = _load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error")}
    state["running_stage"] = _running_stage(state)
    state["success"] = True
    return state


def list_runs() -> dict[str, Any]:
    runs = []
    for child in sorted(runs_dir().iterdir(), reverse=True):
        state_file = child / "run.json"
        if not state_file.exists():
            continue
        try:
            s = json.loads(state_file.read_text(encoding="utf-8"))
            done = [k for k, v in s.get("stages", {}).items() if v.get("status") == "done"]
            runs.append(
                {
                    "id": s["id"],
                    "target": Path(s["target"]).name,
                    "created": s.get("created"),
                    "done": done,
                    "running": _running_stage(s),
                    "gate": (s.get("gate") or {}).get("decision"),
                }
            )
        except (OSError, ValueError, KeyError):
            continue
    return {"success": True, "runs": runs, "message": f"{len(runs)} run(s)."}


def read_artifact(run_id: str, rel_path: str, max_chars: int = 20000) -> dict[str, Any]:
    run_path, state = _load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error")}
    full = (run_path / rel_path).resolve()
    try:
        full.relative_to(run_path.resolve())
    except ValueError:
        return {"success": False, "error": "Artifact path escapes the run directory."}
    if not full.is_file():
        return {"success": False, "error": f"No such artifact: {rel_path}"}
    text = full.read_text(encoding="utf-8", errors="replace")
    truncated = len(text) > max_chars
    return {"success": True, "run_id": run_id, "path": rel_path, "truncated": truncated, "content": text[:max_chars]}
