"""Tests for ClickerLab: stage-1b elicitation + stage-3 session gates.

Hermetic: tmp_path run roots (monkeypatched), fixture binary only. Live driving
is never attempted - the gate refusals (confirm, VM opt-out, missing pywinauto)
are asserted as honest outcomes, not skips.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from reversing_mcp import clickerlab, gym

FIXTURE = Path(__file__).parent / "fixtures" / "binaries" / "test_pe.exe"


@pytest.fixture()
def runs_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "runs"
    root.mkdir()
    monkeypatch.setattr(gym, "_runs_dir", root)
    return root


def _run_with_triage(runs_root: Path) -> str:
    out = gym.create_run(str(FIXTURE), test_files=[], notes="t")
    assert out["success"], out
    run_id = out["run_id"]
    triage = {"formats_referenced": [".txt"], "die": {}, "capa": {}}
    (runs_root / run_id / "triage" / "triage.json").write_text(json.dumps(triage))
    return run_id


def test_mining_is_pure_and_bounded() -> None:
    strings = [
        "Open File... menu handler",
        "Export to PDF document writer",
        "Save skin theme toolbar config",
        "MZ header PK zip ITSF chm",
        "x",
        "A" * 500,
    ]
    cands = clickerlab.mine_format_candidates(strings)
    assert isinstance(cands, list) and len(cands) <= 25
    feats = clickerlab.mine_features(strings)
    prio1 = [f for f in feats if f["priority"] == 1]
    assert prio1, "file-I/O strings must surface as priority 1"
    assert all(set(f) >= {"id", "title", "source", "file_io", "priority"} for f in feats)
    tour = clickerlab.build_tour_draft(str(FIXTURE), feats)
    parsed = yaml.safe_load(tour)
    assert parsed["steps"][0]["action"] == "launch"
    assert parsed["steps"][-1]["id"] == "quit"


def test_elicit_run_builds_artifacts(runs_root: Path) -> None:
    run_id = _run_with_triage(runs_root)
    out = clickerlab.elicit_run(run_id)
    assert out["success"], out
    elic = runs_root / run_id / "elicitation"
    assert (elic / "elicitation.json").exists()
    assert (elic / "features.json").exists()
    assert (elic / "tour-draft.yaml").exists()
    assert (elic / "prior-art.md").exists()
    assert list((elic / "formats").glob("*.md")), "expected at least one format stub"
    feats = json.loads((elic / "features.json").read_text())
    assert isinstance(feats, list)
    assert yaml.safe_load((elic / "tour-draft.yaml").read_text())["steps"]


def test_elicit_needs_known_run_and_triage(runs_root: Path) -> None:
    assert clickerlab.elicit_run("nope")["success"] is False
    out = gym.create_run(str(FIXTURE), test_files=[], notes="t")
    run_id = out["run_id"]
    missing = clickerlab.elicit_run(run_id)
    assert missing["success"] is False and "triage" in missing["error"]


def test_clicker_gates_are_honest(runs_root: Path) -> None:
    run_id = _run_with_triage(runs_root)
    no_confirm = clickerlab.clicker_start(run_id, confirm=False, accept_local=True)
    assert no_confirm["success"] is False and "confirm" in no_confirm["error"]
    no_local = clickerlab.clicker_start(run_id, confirm=True, accept_local=False)
    assert (no_local["success"] is False and "virtualization-mcp" in no_local["error"]) or "VM" in no_local["error"]
    no_driver = clickerlab.clicker_start(run_id, confirm=True, accept_local=True)
    assert no_driver["success"] is False and "pywinauto" in no_driver["error"]
    tour_missing = clickerlab.clicker_start(run_id, mode="tour", confirm=True, accept_local=True)
    assert tour_missing["success"] is False and "tour" in tour_missing["error"].lower()
    assert clickerlab.clicker_status(run_id, "nope")["success"] is False
    assert clickerlab.clicker_stop(run_id, "nope")["success"] is False
    assert clickerlab.clicker_start("nope", confirm=True, accept_local=True)["success"] is False


def test_engines_probe_never_raises() -> None:
    probe = clickerlab.clicker_engines()
    assert probe["elicitation_ready"] is True
    assert set(probe["engines"]) >= {"pywinauto", "pillow", "yaml"}
