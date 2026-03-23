#!/usr/bin/env python3
"""
CLI: static Digibib5 / Directmedia research snapshot (JSON).

Usage (from repo root):
  uv run python scripts/analyze_digibib.py
  uv run python scripts/analyze_digibib.py --exe "D:\\path\\to\\Digibib5.exe"
  uv run python scripts/analyze_digibib.py --output artifacts/digibib_snapshot.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Repo root = parent of scripts/
_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from reversing_mcp.analyzers import BinaryAnalyzer  # noqa: E402
from reversing_mcp.digibib_research import (  # noqa: E402
    build_research_snapshot,
    resolve_digibib_exe,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Digibib5 static research snapshot")
    parser.add_argument("--exe", default=None, help="Path to Digibib5.exe (optional)")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write JSON to this file (default: print to stdout)",
    )
    args = parser.parse_args()

    resolved, tried = resolve_digibib_exe(args.exe)
    if resolved is None:
        print("Digibib5.exe not found. Searched:", file=sys.stderr)
        for p in tried:
            print(f"  {p}", file=sys.stderr)
        return 1

    analyzer = BinaryAnalyzer()
    snap = build_research_snapshot(analyzer, resolved)
    text = json.dumps(snap, indent=2, ensure_ascii=False)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}", file=sys.stderr)
    else:
        print(text)
    return 0 if snap.get("success") else 2


if __name__ == "__main__":
    raise SystemExit(main())
