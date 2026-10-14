"""Tests for the Reversing Gym G1 job runner (src/reversing_mcp/gym.py).

Hermetic: tmp_path run roots (monkeypatched), fixture binary only, no live
engines required (absent DiE/capa is an asserted honest outcome, not a skip).
Stage-2 oracle never executes here: gate refusals, agent shape, and the
event-folding are asserted without spawning anything.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from reversing_mcp import gym

FIXTURE = Path(__file__).parent / "fixtures" / "binaries" / "test_pe.exe"


@pytest.fixture()
def runs_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "runs"
    root.mkdir()
    monkeypatch.setattr(gym, "_runs_dir", root)
    return root


def _start(target: str = str(FIXTURE)) -> dict:
    out = gym.create_run(target, test_files=[], notes="t")
    assert out["success"], out
    assert out["stage"] == "intake"
    return out


def test_start_rejects_missing_and_non_exe(tmp_path: Path) -> None:
    assert gym.create_run(str(tmp_path / "nope.exe"))["success"] is False
    txt = tmp_path / "notes.txt"
    txt.write_text("hi")
    out = gym.create_run(str(txt))
    assert out["success"] is False and ".exe" in out["error"]


CANNED_ORACLE = {
    "success": True,
    "events": [
        {"type": "file_open", "path": "C:/t/a.txt", "handle": "100"},
        {"type": "file_io", "op": "read", "path": "C:/t/a.txt", "offset": 0, "requested": 16, "head": "aa"},
        {"type": "file_close", "handle": "100", "path": "C:/t/a.txt"},
    ],
    "pid": 1,
    "elapsed_s": 1.0,
    "process_exited": True,
    "hooked": ["kernel32.dll!ReadFile"],
    "hook_errors": [],
    "dropped": 0,
}


def test_full_g1_flow_to_gate(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("reversing_mcp.engines.frida_oracle", lambda *a, **k: dict(CANNED_ORACLE))
    run_id = _start()["run_id"]

    triage = gym.advance_run(run_id, background=False)
    assert triage["success"], triage
    assert triage["stage"] == "triage"
    assert (runs_root / run_id / "triage" / "triage.json").exists()

    refused = gym.advance_run(run_id, background=False)
    assert refused["success"] is False and "confirm" in refused["error"]

    oracle = gym.advance_run(run_id, background=False, confirm=True, accept_local=True)
    assert oracle["success"], oracle
    assert oracle["stage"] == "oracle_capture"
    assert (runs_root / run_id / "oracle" / "oracle.json").exists()

    assess = gym.advance_run(run_id, background=False)
    assert assess["success"], assess
    assert assess["stage"] == "assessment"
    dims = assess["assessment"]["dimensions"]
    assert {d["dimension"] for d in dims} == {"Binary", "UI coverage", "Format", "Logic", "Oracle"}
    assert assess["assessment"]["verdict"] in ("green", "amber", "red")
    assert (runs_root / run_id / "assessment" / "assessment.json").exists()

    gated = gym.advance_run(run_id, background=False)
    assert gated["success"] is False and "decision" in gated["error"]

    go = gym.advance_run(run_id, decision="go")
    assert go["success"] and "go" in go["message"]

    beyond = gym.advance_run(run_id, background=False)
    assert beyond["success"] is False and "pending-spec" in beyond["error"]


def test_engines_absent_is_honest(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("reversing_mcp.engines.run_die", lambda *a, **k: {"success": False, "error": "no DiE"})
    monkeypatch.setattr("reversing_mcp.engines.run_capa", lambda *a, **k: {"success": False, "error": "no capa"})
    run_id = _start()["run_id"]
    triage = gym.advance_run(run_id, background=False)
    assert triage["success"]
    assert triage["triage"]["die"]["available"] is False
    monkeypatch.setattr("reversing_mcp.engines.frida_oracle", lambda *a, **k: dict(CANNED_ORACLE))
    oracle = gym.advance_run(run_id, background=False, confirm=True, accept_local=True)
    assert oracle["success"], oracle
    assess = gym.advance_run(run_id, background=False)
    by_dim = {d["dimension"]: d for d in assess["assessment"]["dimensions"]}
    assert by_dim["Binary"]["status"] == "unknown"
    assert by_dim["Logic"]["status"] == "unknown"


def test_engines_present_real_contract(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Shapes as engines.run_die / run_capa actually return them (Digibib5, 2026-10-12)."""
    die = {
        "success": True,
        "packed": False,
        "detections": [{"type": "compiler", "name": "Borland Delphi", "string": "Compiler: Borland Delphi(7)"}],
    }
    capa = {
        "success": True,
        "capabilities": [
            {"name": "check for unmoving mouse cursor", "namespace": "anti-analysis/anti-vm/vm-detection"},
            {"name": "read file on Windows", "namespace": "host-interaction/file-system/read"},
        ],
    }
    monkeypatch.setattr("reversing_mcp.engines.run_die", lambda *a, **k: dict(die))
    monkeypatch.setattr("reversing_mcp.engines.run_capa", lambda *a, **k: dict(capa))
    run_id = _start()["run_id"]
    triage = gym.advance_run(run_id, background=False)
    assert "DiE: answered" in triage["message"] and "capa: answered" in triage["message"]
    assert len(triage["triage"]["capa"]["summary"]) == 2
    monkeypatch.setattr("reversing_mcp.engines.frida_oracle", lambda *a, **k: dict(CANNED_ORACLE))
    assert gym.advance_run(run_id, background=False, confirm=True, accept_local=True)["success"]
    by_dim = {d["dimension"]: d for d in gym.advance_run(run_id, background=False)["assessment"]["dimensions"]}
    assert by_dim["Binary"]["status"] == "green"
    assert by_dim["Logic"]["status"] == "amber"
    assert by_dim["Oracle"]["status"] == "amber" and "anti-VM" in by_dim["Oracle"]["reason"]


def test_artifact_traversal_guard(runs_root: Path) -> None:
    run_id = _start()["run_id"]
    bad = gym.read_artifact(run_id, "../../server.py")
    assert bad["success"] is False and "escapes" in bad["error"]
    missing = gym.read_artifact(run_id, "triage/nope.json")
    assert missing["success"] is False
    gym.advance_run(run_id, background=False)
    ok = gym.read_artifact(run_id, "triage/triage.json")
    assert ok["success"] and ok["content"].startswith("{")


def test_stop_list_unknown(runs_root: Path) -> None:
    run_id = _start()["run_id"]
    assert gym.stop_run(run_id)["success"] is True
    assert gym.stop_run("deadbeefcafe")["success"] is False
    assert gym.get_run("deadbeefcafe")["success"] is False
    listed = gym.list_runs()
    assert listed["success"] and any(r["id"] == run_id for r in listed["runs"])
    log = (runs_root / run_id / "log.jsonl").read_text(encoding="utf-8")
    assert "stage_done" in log or "created" in log
    _ = json.loads((runs_root / run_id / "run.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- background execution


def _wait_idle(run_id: str, timeout: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = gym.get_run(run_id)
        if not state["running_stage"]:
            return state
        time.sleep(0.05)
    raise AssertionError(f"run {run_id} still running after {timeout}s")


@pytest.fixture()
def gated_capa(monkeypatch: pytest.MonkeyPatch) -> threading.Event:
    """run_capa blocks until the returned event is set (stands in for a 40-minute capa)."""
    release = threading.Event()

    def slow_capa(*_a: Any, **_k: Any) -> dict:
        release.wait(10)
        return {"success": True, "capabilities": []}

    monkeypatch.setattr("reversing_mcp.engines.run_die", lambda *a, **k: {"success": True, "detections": []})
    monkeypatch.setattr("reversing_mcp.engines.run_capa", slow_capa)
    return release


def test_advance_returns_immediately_and_completes_in_background(runs_root: Path, gated_capa: threading.Event) -> None:
    run_id = _start()["run_id"]
    t0 = time.monotonic()
    started = gym.advance_run(run_id)
    assert time.monotonic() - t0 < 2, "advance must not wait for the stage"
    assert started["success"] and started["status"] == "running" and started["stage"] == "triage"
    assert gym.get_run(run_id)["running_stage"] == "triage"

    busy = gym.advance_run(run_id)
    assert busy["success"] is False and busy["busy"] is True and busy["stage"] == "triage"
    assert any(r["id"] == run_id and r["running"] == "triage" for r in gym.list_runs()["runs"])

    gated_capa.set()
    state = _wait_idle(run_id)
    assert state["stages"]["triage"]["status"] == "done"
    assert "Triage complete" in state["stages"]["triage"]["message"]

    assert gym.advance_run(run_id)["stage"] == "oracle_capture"
    state = _wait_idle(run_id)
    assert state["stages"]["oracle_capture"]["status"] == "failed"
    assert "confirm" in (state["stages"]["oracle_capture"]["error"] or "")
    assert state["gate"] is None  # gate only exists after assessment completes


def test_stop_discards_late_result_and_retry_works(runs_root: Path, gated_capa: threading.Event) -> None:
    run_id = _start()["run_id"]
    gym.advance_run(run_id)
    stopped = gym.stop_run(run_id)
    assert stopped["success"] and "triage" in stopped["message"]
    assert gym.get_run(run_id)["stages"]["triage"]["status"] == "stopped"

    # Retry while the stopped attempt is still blocked inside capa.
    retry = gym.advance_run(run_id)
    assert retry["success"] and retry["stage"] == "triage"
    gated_capa.set()  # releases both attempts
    state = _wait_idle(run_id)
    assert state["stages"]["triage"]["status"] == "done"
    log = (runs_root / run_id / "log.jsonl").read_text(encoding="utf-8")
    assert "stage_result_discarded" in log  # the stopped attempt's late result


def test_running_without_worker_becomes_interrupted(runs_root: Path) -> None:
    run_id = _start()["run_id"]
    state_file = runs_root / run_id / "run.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["stages"]["triage"].update({"status": "running", "attempt": "from-a-dead-backend"})
    state_file.write_text(json.dumps(state), encoding="utf-8")

    seen = gym.get_run(run_id)
    assert seen["stages"]["triage"]["status"] == "interrupted"
    assert seen["running_stage"] is None
    assert gym.advance_run(run_id)["stage"] == "triage"  # resumable
    _wait_idle(run_id, timeout=120)  # don't leak the worker into later tests


def test_stage_exception_marks_failed(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a: Any, **_k: Any) -> dict:
        raise RuntimeError("diec exploded")

    monkeypatch.setattr("reversing_mcp.engines.run_die", boom)
    run_id = _start()["run_id"]
    gym.advance_run(run_id)
    state = _wait_idle(run_id)
    assert state["stages"]["triage"]["status"] == "failed"
    assert "diec exploded" in state["stages"]["triage"]["error"]


def test_stop_cancels_engine_and_worker_ends_promptly(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """stop fires the attempt's cancel event; a cancel-aware engine returns at once."""
    seen: dict[str, Any] = {}

    def cancellable_capa(*_a: Any, cancel: threading.Event | None = None, **_k: Any) -> dict:
        seen["cancel"] = cancel
        assert cancel is not None
        if cancel.wait(30):
            return {"success": False, "cancelled": True, "error": "capa cancelled (process tree killed)"}
        return {"success": True, "capabilities": []}

    monkeypatch.setattr("reversing_mcp.engines.run_die", lambda *a, **k: {"success": True, "detections": []})
    monkeypatch.setattr("reversing_mcp.engines.run_capa", cancellable_capa)
    run_id = _start()["run_id"]
    gym.advance_run(run_id)
    deadline = time.monotonic() + 5
    while "cancel" not in seen and time.monotonic() < deadline:
        time.sleep(0.05)

    t0 = time.monotonic()
    gym.stop_run(run_id)
    assert seen["cancel"].is_set()
    while gym._workers and time.monotonic() - t0 < 5:
        time.sleep(0.05)
    assert not gym._workers, "worker still alive after stop"
    assert time.monotonic() - t0 < 3
    state = gym.get_run(run_id)
    assert state["stages"]["triage"]["status"] == "stopped"
    log = (runs_root / run_id / "log.jsonl").read_text(encoding="utf-8")
    assert "stage_result_discarded" in log


def test_oracle_agent_shape() -> None:
    from reversing_mcp import engines

    src = engines.build_oracle_agent()
    for token in ("CreateFileW", "ReadFile", "WriteFile", "CloseHandle", "OVERLAPPED", "file_io"):
        assert token in src, f"oracle agent missing {token}"


def test_build_oracle_folds_and_flags() -> None:
    events = [
        {"type": "file_open", "path": "C:/t/a.txt", "handle": "100"},
        {"type": "file_io", "op": "read", "path": "C:/t/a.txt", "offset": 0, "requested": 64, "head": "ab"},
        {"type": "file_io", "op": "write", "path": "C:/t/evil.exe", "offset": 1024, "requested": 512, "head": "cd"},
        {"type": "file_close", "handle": "100", "path": "C:/t/a.txt", "known": True},
        {"type": "file_close", "handle": "999", "path": None, "known": False},
    ]
    oracle = gym._build_oracle(events, "t.exe")
    assert oracle["file_count"] == 2
    assert oracle["files"]["C:/t/a.txt"]["total_read"] == 64
    assert oracle["files"]["C:/t/evil.exe"]["total_written"] == 512
    assert any("evil.exe" in f for f in oracle["flags"])


def test_oracle_refuses_without_gates(runs_root: Path) -> None:
    run_id = _start()["run_id"]
    run_path = runs_root / run_id
    state = json.loads((run_path / "run.json").read_text(encoding="utf-8"))
    no_confirm = gym._stage_oracle(run_path, {**state, "stage_params": {}})
    assert "confirm" in no_confirm["error"]
    no_local = gym._stage_oracle(run_path, {**state, "stage_params": {"oracle_capture": {"confirm": True}}})
    assert "virtualization-mcp" in no_local["error"] or "VM" in no_local["error"]


def test_advance_reaches_oracle_with_gates(runs_root: Path) -> None:
    run_id = _start()["run_id"]
    run_path = runs_root / run_id
    # Fake intake+triage done (triage engines stay untouched).
    state = json.loads((run_path / "run.json").read_text(encoding="utf-8"))
    for s in ("intake", "triage"):
        state["stages"][s].update({"status": "done", "ended": "t", "message": "fake"})
    (run_path / "run.json").write_text(json.dumps(state), encoding="utf-8")
    refused = gym.advance_run(run_id, background=False)
    assert refused["success"] is False and "confirm" in refused["error"]
