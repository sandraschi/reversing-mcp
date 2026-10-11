# Tour runner (Tier 3) — `scripts/tour/`

Behavioral half of the feature-to-code-map pipeline. Status: **static
correlation (correlate.py) works now**; live CUA driving is Phase 2.

## Layout

- `tour.example.yaml` — scripted Digibib5 feature tour (launch, open volume,
  page text). Documents the future live run; NOT executed yet (needs an
  isolated host + pywinauto driver per `docs/CUA_DISASSEMBLY_COMBO.md` §3).
- `correlate.py` — static correlation v1: observed-string seeds → string
  offsets in the target (via `reversing_mcp.analyzers`) → function refs when an
  engine is present → feature-to-code map markdown. Runs today.
- `captures/` (gitignored) — tour-run bundles land here when Phase 2 exists.
- `maps/` — committed map artifacts (ground truth for Tier 3 progress).

## Capture bundle v1 (format, for Phase 2 implementers)

`captures/<target>-<yyyymmdd-hhmmss>/` with `tour.jsonl` (one record per step:
`step`, `action`, `ts`, `ocr_text`, `uia_snapshot`, `artifacts[]`) plus raw
artifacts (screenshots, UI trees, file/registry diffs, HAR/pcap). REA-compatible
shapes only (process-capture / HAR), so bundles feed
`rea_investigate(..., snapshot_path=...)` without conversion.

## correlate.py usage

```powershell
uv run python scripts/tour/correlate.py --target "tests/fixtures/exe files/Digibib5.exe" --seeds DKI,decompress,ReadFile --out maps/digibib5-search-v1.md
uv run python scripts/tour/correlate.py --target prog.exe --seeds-file seeds.txt --out maps/prog.md
```

Exit 0 with a map file always (even when engines are absent — their sections say
so honestly). Never claims coverage it did not compute.
