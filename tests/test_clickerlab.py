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


CALIB_WIN32 = Path(__file__).parent / "fixtures" / "calib" / "calib_win32.exe"


def _run_with_triage(runs_root: Path, target: Path | None = None) -> str:
    out = gym.create_run(str(target or FIXTURE), test_files=[], notes="t")
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


def test_clicker_gates_are_honest(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id = _run_with_triage(runs_root)
    no_confirm = clickerlab.clicker_start(run_id, confirm=False, accept_local=True)
    assert no_confirm["success"] is False and "confirm" in no_confirm["error"]
    no_local = clickerlab.clicker_start(run_id, confirm=True, accept_local=False)
    assert (no_local["success"] is False and "virtualization-mcp" in no_local["error"]) or "VM" in no_local["error"]
    # Env-independent: force the no-driver path even where pywinauto is installed.
    # Without this, the test would spawn the fixture binary for real.
    monkeypatch.setattr(
        clickerlab,
        "clicker_engines",
        lambda: {"drive_ready": False, "engines": {"pywinauto": {"available": False, "install_hint": "x"}}},
    )
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
    assert set(probe["engines"]) >= {"pywinauto", "pillow", "yaml", "ocr"}


def test_allowlist_blocks_credentials_and_payment() -> None:
    for intent in ("Enter password", "Sign in to continue", "Buy now with credit card", "Paste license key"):
        gate = clickerlab.classify_step({"id": "x", "action": [{"intent": intent}]})
        assert gate["allowed"] is False and gate["skip_name"].startswith("forbidden:")
    ok = clickerlab.classify_step({"id": "y", "action": [{"intent": "Open file"}]})
    assert ok["allowed"] is True


def test_file_diff_and_jsonl(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    a.write_text("v1")
    before, trunc_before = clickerlab.snapshot_files([tmp_path])
    assert trunc_before is False
    a.write_text("v2 longer")
    (tmp_path / "b.txt").write_text("new")
    after, _ = clickerlab.snapshot_files([tmp_path])
    diff = clickerlab.diff_files(before, after)
    assert any("b.txt" in p for p in diff["added"])
    assert any("a.txt" in p for p in diff["modified"])
    clickerlab.jlog(tmp_path, {"kind": "probe", "ok": True})
    lines = (tmp_path / "tour.jsonl").read_text().splitlines()
    assert len(lines) == 1 and '"probe"' in lines[0]


def test_screenshot_diff_and_ocr_graceful(tmp_path: Path) -> None:
    from PIL import Image

    white = tmp_path / "w.png"
    Image.new("L", (128, 128), 255).save(str(white))
    assert clickerlab.screenshot_diff_regions(white, white) == []
    other = tmp_path / "b.png"
    img = Image.new("L", (128, 128), 255)
    img.paste(0, (32, 32, 96, 96))
    img.save(str(other))
    boxes = clickerlab.screenshot_diff_regions(white, other)
    assert boxes and all(b["w"] > 0 and b["h"] > 0 for b in boxes)
    assert clickerlab.ocr_regions(white) == []
    assert clickerlab.ocr_image(tmp_path / "missing.png") == ""
    assert clickerlab.read_clipboard_text() is not None


def test_time_cap_propagates_instead_of_spinning(tmp_path: Path) -> None:
    """Live-fire regression: an expired deadline must raise out of _run_rip,
    never be swallowed by a pass-level except (infinite spin past time_cap)."""

    class _DeadApp:
        def windows(self) -> list:
            return []

        def top_window(self):  # pragma: no cover - never reached
            raise AssertionError("unreachable")

    import threading
    import time

    state = {"step_cap": 40, "time_cap_s": 300, "coverage": {}, "watch_dirs": []}
    coverage: dict = {}
    with pytest.raises(TimeoutError):
        clickerlab._run_rip(tmp_path, state, _DeadApp(), coverage, threading.Event(), time.monotonic() - 1)


def test_target_alive() -> None:
    import os

    assert clickerlab._target_alive({"target_pid": os.getpid()}) is True
    assert clickerlab._target_alive({"target_pid": 999999999}) is False
    assert clickerlab._target_alive({}) is False


def test_snapshot_budget_and_truncated_flag(tmp_path: Path) -> None:
    for i in range(10):
        (tmp_path / f"f{i}.txt").write_text("x")
    snap, truncated = clickerlab.snapshot_files([tmp_path], max_files=5)
    assert len(snap) <= 5 and truncated is True
    full, truncated_full = clickerlab.snapshot_files([tmp_path], max_files=100)
    assert len(full) == 10 and truncated_full is False


def test_file_offset_to_va() -> None:
    target = str(CALIB_WIN32)
    if not Path(target).is_file():
        pytest.skip("calibration binaries missing")
    import struct

    with open(target, "rb") as f:
        data = f.read(0x1000)
    (e_lfanew,) = struct.unpack_from("<I", data, 0x3C)
    (n_sec,) = struct.unpack_from("<H", data, e_lfanew + 6)
    assert n_sec and n_sec < 96
    # A mid-.rdata offset must map above the image base; headers must not.
    assert (clickerlab.file_offset_to_va(target, 0x2000) or 0) > 0x10000
    assert clickerlab.file_offset_to_va(target, 0) is None
    assert clickerlab.file_offset_to_va(target, 0xFFFFFF) is None
    assert clickerlab.file_offset_to_va("D:/nope.exe", 99) is None


def test_compare_sessions_scores_and_divergence(runs_root: Path) -> None:
    run_id = _run_with_triage(runs_root)
    base = runs_root / run_id / "clicker" / "sessions"
    for sid in ("a1", "b1"):
        sdir = base / sid
        sdir.mkdir(parents=True)
        (sdir / "session.json").write_text("{}")
    steps = [
        {"id": "s1", "action": "launch", "outcome": "launched", "expect": None, "expect_ok": True},
        {"id": "s2", "action": [{"intent": "open"}], "outcome": "ok", "expect": "win", "expect_ok": True},
    ]
    (base / "a1" / "tour-results.json").write_text(json.dumps(steps))
    (base / "b1" / "tour-results.json").write_text(json.dumps(steps))
    same = clickerlab.compare_sessions(run_id, "a1", "b1")
    assert same["success"] and same["deterministic"] is True and same["score"] == 1.0
    altered = [dict(steps[0]), dict(steps[1], expect_ok=False)]
    (base / "b1" / "tour-results.json").write_text(json.dumps(altered))
    diff = clickerlab.compare_sessions(run_id, "a1", "b1")
    assert diff["success"] and diff["deterministic"] is False and diff["score"] == 0.5
    assert len(diff["diverged"]) == 1 and diff["diverged"][0]["index"] == 1
    assert clickerlab.compare_sessions(run_id, "a1", "nope")["success"] is False


def test_export_map_writes_ida_script_without_jvm(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if not CALIB_WIN32.is_file():
        pytest.skip("calibration binaries missing")
    run_id = _run_with_triage(runs_root, CALIB_WIN32)
    sdir = runs_root / run_id / "clicker" / "sessions" / "s1"
    sdir.mkdir(parents=True)
    (sdir / "session.json").write_text("{}")
    va = clickerlab.file_offset_to_va(str(CALIB_WIN32), 0x400)
    assert va, "calib .text offset must map (else the fixture changed)"
    (sdir / "map.json").write_text(
        json.dumps(
            {
                "seeds": [{"seed": "Open", "offsets": [0x400], "xref_functions": ["FUN_1"], "verdict": "mapped"}],
                "mapped": 1,
                "total": 1,
            }
        )
    )
    import pyghidra

    from reversing_mcp import analyzers

    monkeypatch.setattr(analyzers, "_JVM_STARTED", True)
    monkeypatch.setattr(pyghidra, "open_program", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no jvm")))
    out = clickerlab.export_map(run_id, "s1")
    assert out["success"] is True
    assert out["ghidra_error"] is not None
    script = (sdir / "map_import_ida.py").read_text()
    assert "Open" in script and str(va) in script
    assert clickerlab.export_map(run_id, "nosess")["success"] is False


def test_correlate_writes_map_without_rea(runs_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Function inventory can shell out to slow engines; verdict logic is what's under test.
    monkeypatch.setattr(
        "reversing_mcp.analyzers.BinaryAnalyzer.find_functions",
        lambda self, target, tool="auto": [{"error": "stubbed for speed"}],
    )
    run_id = _run_with_triage(runs_root)
    sdir = runs_root / run_id / "clicker" / "sessions" / "s1"
    sdir.mkdir(parents=True)
    (sdir / "session.json").write_text("{}")
    (sdir / "tour.jsonl").write_text(
        '{"ts": "t", "kind": "tour_step", "outcome": "opened", "ocr_text": "File Open", "clipboard": "", "text": ""}\n'
    )
    out = clickerlab.correlate_session(run_id, "s1", with_rea=False)
    assert out["success"], out
    assert (sdir / "map.md").exists()
    assert out["seeds"] >= 0
    bad = clickerlab.correlate_session(run_id, "nope", with_rea=False)
    assert bad["success"] is False
