"""Tier 3 one-shot: run -> triage -> elicit -> drive -> correlate.

Usage:
    uv run python scripts/cua_tour.py --target D:/apps/prog.exe --mode rip --confirm --accept-local
    uv run python scripts/cua_tour.py --target D:/apps/prog.exe --mode tour --tour-rel elicitation/tour-draft.yaml --confirm --accept-local

--confirm executes the target; --accept-local is the logged opt-out from VM
isolation (spec section 1). Both are required, every invocation - the recipe
does not bake them in. Exit 0 prints the map path; exit 2 on any stage failure.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from reversing_mcp import clickerlab, gym


def fail(msg: str) -> int:
    print(f"cua-tour FAILED: {msg}")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description="Tier 3 one-shot CUA tour + correlate.")
    ap.add_argument("--target", required=True)
    ap.add_argument("--mode", default="rip", choices=("rip", "tour"))
    ap.add_argument("--tour-rel", default=None)
    ap.add_argument("--step-cap", type=int, default=200)
    ap.add_argument("--time-cap", type=int, default=600)
    ap.add_argument("--no-rea", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--accept-local", action="store_true")
    args = ap.parse_args()

    if not args.confirm or not args.accept_local:
        return fail("refusing without --confirm --accept-local (target executes on this desktop)")

    started = gym.create_run(args.target, test_files=[], notes="cua-tour one-shot")
    if not started.get("success"):
        return fail(f"intake: {started.get('error')}")
    run_id = started["run_id"]
    print(f"run {run_id}")

    triage = gym.advance_run(run_id, background=False)
    if not triage.get("success"):
        return fail(f"triage: {triage.get('error')}")
    print(f"triage: {triage.get('message')}")

    elic = clickerlab.elicit_run(run_id)
    if not elic.get("success"):
        return fail(f"elicitation: {elic.get('error')}")
    print(f"elicitation: {elic.get('message')}")

    tour_rel = args.tour_rel or ("elicitation/tour-draft.yaml" if args.mode == "tour" else None)
    sess = clickerlab.clicker_start(
        run_id,
        mode=args.mode,
        tour_rel=tour_rel,
        step_cap=args.step_cap,
        time_cap_s=args.time_cap,
        confirm=True,
        accept_local=True,
    )
    if not sess.get("success"):
        return fail(f"session start: {sess.get('error')}")
    sid = sess["session_id"]
    print(f"session {sid} ({args.mode}) - driving...")

    while True:
        time.sleep(5)
        st = clickerlab.clicker_status(run_id, sid)
        status = st.get("status")
        if status != "running":
            print(f"session {status}: {st.get('message') or st.get('error')}")
            if status != "done":
                return fail(f"session {status}: {st.get('error')}")
            break

    corr = clickerlab.correlate_session(run_id, sid, with_rea=not args.no_rea)
    if not corr.get("success"):
        return fail(f"correlate: {corr.get('error')}")
    print(f"map: gym/runs/{run_id}/clicker/sessions/{sid}/map.md")
    print(corr.get("message"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
