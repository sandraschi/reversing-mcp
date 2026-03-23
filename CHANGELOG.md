# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `docs/DIGIBIB_DECOMPILE_PLAN.md` — phased Ghidra/ReVa plan for full `Digibib5.exe` reverse; empirical notes on `tree.dki` vs `text.dki`, index extensions, and public-repo gap.

### Changed

- **ReVa vs reversing-mcp:** Docs and README now state explicitly that **ReVa MCP tools are not implemented in this repo**; ReVa is a **separate** server. **Digibib5.exe / DKI** framed as a **small/medium-app example and test case**, not a goal to decompile huge programs (e.g. Word).
- `README.md` (primary mission) — points at the decompile plan; clarifies heuristic DKI vs EXE-led spec.
- `README.md`, `ROADMAP.md`, `tests/README.md`, `tests/DEMO.md`, `reversing-webapp/README.md`, `ASSESSMENT.md` — tone: removed hype, emoji-heavy headers, and speculative “vision” lists; kept factual content.
- `docs/DIRECTMEDIA_MISSION.md` — workflow updated; links plan; honest gap on packed `text.dki`.
- `docs/DIRECTMEDIA_REVERSING_TOOLKIT.md` — volume layout notes, index extensions, cross-links.
