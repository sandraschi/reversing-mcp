"""Hermetic calibration: known-answer tests for the C-built targets.

tests/fixtures/calib holds two tiny C apps (source + committed binaries,
built by scripts/build_calib.py): calib_win32 (real menus/button/file I/O)
and calib_canvas (painted UI, forces the B3 path). expected.json is the
ground truth. Live rip/tour stay local (need a desktop); everything here
runs headless in CI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reversing_mcp import clickerlab, gym

CALIB = Path(__file__).parent / "fixtures" / "calib"


def _expected() -> dict:
    return json.loads((CALIB / "expected.json").read_text(encoding="utf-8"))


requires_exes = pytest.mark.skipif(
    not ((CALIB / "calib_win32.exe").is_file() and (CALIB / "calib_canvas.exe").is_file()),
    reason="calibration binaries missing - run scripts/build_calib.py on Windows",
)


@pytest.fixture()
def runs_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "runs"
    root.mkdir()
    monkeypatch.setattr(gym, "_runs_dir", root)
    return root


def _triaged_run(runs_root: Path, binary: str) -> str:
    out = gym.create_run(str(CALIB / binary), test_files=[], notes="calib")
    assert out["success"], out
    run_id = out["run_id"]
    (runs_root / run_id / "triage" / "triage.json").write_text(json.dumps({"formats_referenced": []}))
    return run_id


@requires_exes
def test_elicit_finds_known_features(runs_root: Path) -> None:
    exp = _expected()["CALIB_WIN32"]
    run_id = _triaged_run(runs_root, exp["binary"])
    out = clickerlab.elicit_run(run_id)
    assert out["success"], out
    feats = json.loads((runs_root / run_id / "elicitation" / "features.json").read_text())
    titles = " ".join(f["title"] for f in feats)
    for want in exp["must_elicit_features"]:
        assert want in titles, f"elicitation missed known feature {want!r}"


@requires_exes
def test_correlate_known_seeds(runs_root: Path) -> None:
    exp = _expected()["CALIB_CANVAS"]
    run_id = _triaged_run(runs_root, exp["binary"])
    sdir = runs_root / run_id / "clicker" / "sessions" / "s1"
    sdir.mkdir(parents=True)
    (sdir / "session.json").write_text("{}")
    painted = " ".join(exp["painted_text"])
    (sdir / "tour.jsonl").write_text(
        '{"ts": "t", "kind": "tour_step", "outcome": "canvas", "ocr_text": '
        + json.dumps(painted)
        + ', "clipboard": "", "text": ""}\n'
    )
    out = clickerlab.correlate_session(run_id, "s1", with_rea=False)
    assert out["success"], out
    rows = {r["seed"]: r["verdict"] for r in _map_rows(sdir)}
    for want in exp["must_correlate_seeds"]:
        assert want in rows, f"seed {want!r} missing from map"
        assert rows[want] != "no static trace", f"seed {want!r} has no static trace but is in the binary"


def _map_rows(sdir: Path) -> list[dict]:
    import re

    rows = []
    for m in re.finditer(r"^## (.+?) - (\w[\w ]*)$", (sdir / "map.md").read_text(), re.M):
        rows.append({"seed": m.group(1), "verdict": m.group(2)})
    return rows


@requires_exes
def test_ghidra_inventory_calib() -> None:
    from reversing_mcp import toolbox

    if toolbox.detect_ghidra()["status"] != "ready":
        pytest.skip("no Ghidra on this host")
    from reversing_mcp.analyzers import ghidra_inventory

    inv = ghidra_inventory(str(CALIB / "calib_win32.exe"))
    assert inv.get("success"), inv.get("error")
    # Release build, no PDB: user functions are FUN_* (honest known answer).
    # Structural facts that must hold regardless of symbols:
    assert inv.get("function_count", 0) >= 5
    names = " ".join(f["name"] for f in inv.get("functions", []))
    assert "entry" in names  # CRT entry thunk is always recovered
    assert "__scrt_common_main_seh" in names  # CRT startup anchor
    assert all(f["address"].startswith("0x") and f["size"] > 0 for f in inv.get("functions", []))
