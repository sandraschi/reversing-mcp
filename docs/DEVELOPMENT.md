# Development — reversing-mcp

## Layout

- `src/reversing_mcp/server.py` — 15 MCP tools + FastAPI `_http_app` (36 routes) + `skill://` resources.
- `src/reversing_mcp/{analyzers,rea_bridge,directmedia_dki,digibib_research,transport,logging_config}.py`
- `src/reversing_mcp/skills/primary/SKILL.md` — served via `/api/skills` + `skill://primary`.
- `web_sota/` — Vite/React dashboard (:10751). LLM state in `src/store/llm.ts` (Zustand);
  vendored `src/lib/model-preference.ts` (canonical: `mcp-central-docs/templates/llm-detect/`).
- `tests/fixtures/MANIFEST.md` — ground-truth table for reverse targets.

## Gates (all must pass)

```powershell
uv run ruff check src/ tests/
uv run ruff format --check src/
uv run pyright src/
uv run pytest tests/ -q
# webapp:
bunx tsc --noEmit; bunx biome check src/   # (from web_sota/)
```

CI (`.github/workflows/ci.yml`, windows-latest) runs the same set.

## Conventions

- Portmanteau tools with `operation` enum; `Annotated[..., Field(...)]` params
  (no `Args:` blocks); `## Return Format` + `## Examples` in every docstring.
- Tool annotations: `_READ_ONLY` / `_MUTATING` / `_DESTRUCTIVE`.
- Every tool return carries a human-readable `message` key (dialogic returns).
- Logs to **stderr** (`logging_config.py`) — stdout is JSON-RPC in stdio transport.
- Outputs over 512 KB truncate with a snapshot hint (see `rea_bridge.py`).
- No `print()` in prod code, no bare `except: pass`, `S110`/`S112` stay enabled.
- Frontend: dark theme, `data-testid` ≥3 per page, no `text-xs` on UI text,
  no hardcoded ports (use `getApiBase()`), no undeclared mock models.
- Commits ≤10 files; timestamped `.bak` before 3+ file edits; prove launchers
  by running (`start.ps1 -BackendOnly` + `/health` 200) before committing them.
