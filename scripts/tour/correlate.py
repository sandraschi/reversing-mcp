"""Static correlation v1 (Tier 3 MVP, static half).

Observed-string seeds -> string offsets in the target (via
reversing_mcp.analyzers) -> function refs when an engine answers ->
feature-to-code map markdown.

Reads no captures yet (tour driver is Phase 2); seeds come from --seeds,
--seeds-file, or mission knowledge. Exit 0 with a map file always; engine
sections report absence honestly instead of pretending.

Usage:
    uv run python scripts/tour/correlate.py --target <exe> --seeds DKI,decompress --out maps/x.md
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from reversing_mcp.analyzers import BinaryAnalyzer


def harvest(target: Path, seeds: list[str], min_length: int = 4) -> dict[str, list[dict]]:
    analyzer = BinaryAnalyzer()
    strings = analyzer.extract_strings(str(target), min_length=min_length)
    out: dict[str, list[dict]] = {s: [] for s in seeds}
    for s in strings:
        text = getattr(s, "string", None) or getattr(s, "text", None) or ""
        if not isinstance(text, str):
            text = str(text)
        low = text.lower()
        for seed in seeds:
            if seed.lower() in low:
                offset = getattr(s, "offset", -1)
                enc = getattr(s, "encoding", "?")
                out[seed].append(
                    {"offset": offset if isinstance(offset, int) else -1, "encoding": enc, "text": text[:160]}
                )
    for hits in out.values():
        hits.sort(key=lambda h: h["offset"])
    return out


def functions(target: Path) -> dict:
    analyzer = BinaryAnalyzer()
    try:
        found = analyzer.find_functions(str(target), tool="auto")
    except Exception as e:  # engines absent is a normal outcome, not a crash
        return {"available": False, "error": str(e)}
    if isinstance(found, list) and len(found) == 1 and isinstance(found[0], dict) and "error" in found[0]:
        return {"available": False, "error": found[0]["error"]}
    return {"available": True, "functions": found}


def render_map(target: Path, seeds: list[str], hits: dict, funcs: dict) -> str:
    lines = [
        f"# Feature-to-code map (static v1): {target.name}",
        "",
        f"Target: `{target}` ({target.stat().st_size:,} bytes)",
        f"Generated: {datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')}",
        "Method: seed-string correlation (static only; no live tour yet)",
        "",
        "## Seeds",
        "",
    ]
    for seed in seeds:
        seed_hits = hits.get(seed, [])
        lines.append(f"### `{seed}` — {len(seed_hits)} hit(s)")
        lines.append("")
        if not seed_hits:
            lines.append("- No static trace. (Verdict: unmapped statically.)")
        else:
            for h in seed_hits[:25]:
                lines.append(f"- `0x{h['offset']:X}` [{h['encoding']}] {h['text']}")
            if len(seed_hits) > 25:
                lines.append(f"- …and {len(seed_hits) - 25} more (see tool output for full list).")
        lines.append("")
    lines += ["## Functions", ""]
    if funcs.get("available"):
        names = funcs["functions"] if isinstance(funcs["functions"], list) else []
        lines.append(f"- Engine answered: {len(names)} function(s) (see tool output).")
    else:
        lines.append(f"- No engine answered ({funcs.get('error', 'unavailable')}).")
        lines.append("  Verdict: code refs pending — rerun with Ghidra/REA or after a live tour.")
    lines += [
        "",
        "## Verdict key",
        "",
        "- mapped: seed has offsets above; next step is xrefs/decompile per hit.",
        "- unmapped statically: needs a live tour (behavioral evidence) or an engine.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Static correlation v1: seeds -> map markdown.")
    ap.add_argument("--target", required=True)
    ap.add_argument("--seeds", default="")
    ap.add_argument("--seeds-file", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-length", type=int, default=4)
    args = ap.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"Target not found: {target}")
        return 2
    seeds = [s.strip() for s in args.seeds.split(",") if s.strip()]
    if args.seeds_file:
        seeds += [
            line.strip()
            for line in Path(args.seeds_file).read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
    if not seeds:
        print("No seeds given.")
        return 2

    hits = harvest(target, seeds, min_length=args.min_length)
    funcs = functions(target)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_map(target, seeds, hits, funcs), encoding="utf-8")
    total = sum(len(v) for v in hits.values())
    print(f"map: {out} ({total} hits across {len(seeds)} seeds)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
