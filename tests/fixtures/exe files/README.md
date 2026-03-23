# Executable fixtures (local only)

Place **`Digibib5.exe`** here for reproducible analysis:

`tests/fixtures/exe files/Digibib5.exe`

Binaries are **not committed** (see `.gitignore` in this folder). Copy from:

`C:\Program Files (x86)\Digitale Bibliothek 5\Digibib5.exe`

Then run:

- MCP: `digibib_research_snapshot()` (auto-discovers this path) or pass `exe_path`
- CLI: `uv run python scripts/analyze_digibib.py`

See `docs/DIRECTMEDIA_REVERSING_TOOLKIT.md` for the full workflow toward a modern viewer.
