"""Tests for the Reversing Gym G1 job runner (src/reversing_mcp/gym.py).

Hermetic: tmp_path run roots (monkeypatched), fixture binary only, no live
engines required (absent DiE/capa is an asserted honest outcome, not a skip).
"""

from __future__ import annotations

import json
from pathlib import Path

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


def test_full_g1_flow_to_gate(runs_root: Path) -> None:
    run_id = _start()["run_id"]

    triage = gym.advance_run(run_id)
    assert triage["success"], triage
    assert triage["stage"] == "triage"
    assert (runs_root / run_id / "triage" / "triage.json").exists()

    assess = gym.advance_run(run_id)
    assert assess["success"], assess
    assert assess["stage"] == "assessment"
    dims = assess["assessment"]["dimensions"]
    assert {d["dimension"] for d in dims} == {"Binary", "UI coverage", "Format", "Logic", "Oracle"}
    assert assess["assessment"]["verdict"] in ("green", "amber", "red")
    assert (runs_root / run_id / "assessment" / "assessment.json").exists()

    gated = gym.advance_run(run_id)
    assert gated["success"] is False and "decision" in gated["error"]

    go = gym.advance_run(run_id, decision="go")
    assert go["success"] and "go" in go["message"]

    beyond = gym.advance_run(run_id)
    assert beyond["success"] is False and "pending-spec" in beyond["error"]


def test_engines_absent_is_honest(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("reversing_mcp.engines.run_die", lambda *a, **k: {"available": False, "error": "no DiE"})
    monkeypatch.setattr("reversing_mcp.engines.run_capa", lambda *a, **k: {"available": False, "error": "no capa"})
    run_id = _start()["run_id"]
    triage = gym.advance_run(run_id)
    assert triage["success"]
    assert triage["triage"]["die"]["available"] is False
    assess = gym.advance_run(run_id)
    by_dim = {d["dimension"]: d for d in assess["assessment"]["dimensions"]}
    assert by_dim["Binary"]["status"] == "unknown"
    assert by_dim["Logic"]["status"] == "unknown"


def test_artifact_traversal_guard(runs_root: Path) -> None:
    run_id = _start()["run_id"]
    bad = gym.read_artifact(run_id, "../../server.py")
    assert bad["success"] is False and "escapes" in bad["error"]
    missing = gym.read_artifact(run_id, "triage/nope.json")
    assert missing["success"] is False
    gym.advance_run(run_id)
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
