# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Security (CRITICAL)
- `native/build.ps1`: Bundle `.env.example` instead of `.env` — prevents API key leaks in installer

### Fixed
- **Security**: `tauri.conf.json` bundled `.env` (API keys) instead of `.env.example` — fixed
- **Port conflict**: `vite.config.ts` used port 10750 (same as backend) → changed to 10751
- **Stale `.bak` files**: Removed orphaned backup files from `src/`, `web_sota/`, `mcpb/`
- **Tauri**: `tauri.conf.json` had duplicate `windows` key (JSON syntax error) — fixed
- **Tauri**: `targets` changed from `["msi", "nsis"]` to `["nsis"]` — single primary artifact
- **Tauri**: `backend.rs` `free_port()` upgraded to multi-layer kill pipeline (Stop-Process → taskkill → UAC → 240s poll)
- **Tauri**: `backend.rs` enabled stdout/stderr stream watching for `backend-status` events
- **CORS**: `transport.py` replaced `run_http_async()` with `uvicorn.Server` on `mcp.http_app()` — CORSMiddleware no longer dropped
- **REST**: Added `GET /api/v1/diagnostics` endpoint (CUA-NSIS smoke test compliance)
- **REST**: Added `POST /api/shutdown` endpoint for graceful server termination
- **MCP**: Added `shutdown()` tool with `confirm=True` guard
- **MCP**: Added `shutdown()` MCP tool with `confirm=True` guard

### Added
- `.env.example` at repo root (was missing entirely)
- `llms.txt` — LLM discovery index with all 13 tools listed and API reference
- `CLAUDE.md` — Agent behavioral instructions with tool table and quick start
- `.cursorrules` — Cursor IDE rules file
- Updated `AGENTS.md` with full 13-tool table, architecture map, and linting rules
- `.claude-plugin/plugin.json` + `hooks/hooks.json` — Claude Code session context injection
- `.windsurfrules` — Windsurf IDE rules (mirrors `.cursorrules`)
- `.github/copilot-instructions.md` — GitHub Copilot tool-awareness prompt
- `.opencode/skills/reversing-mcp/SKILL.md` — OpenCode skill with session context
- `start.ps1`: Port zombie clearing before backend start + health poll loop
- `.gitignore`: Added `reports/` and `*.bak` patterns
- `reports/assess-2026-07-25.md` — Full SOTA assessment report

## [Unreleased] — 2026-06-14

### Added
- Tauri native wrapper (native/ directory) with bundle.resources + std::process::Command
- CUA-NSIS: just cua-nsis-test recipe, scripts/cua-smoke.py, scripts/cua-nsis-config.json
- Tauri CORS: tauri://localhost origins for WebView API access
- NSIS installer at dist/ and native/target/release/bundle/nsis/

### Changed
- Frontend API calls use absolute http://127.0.0.1:{port} URLs in production build
- CORS middleware includes allow_origin_regex for tauri.localhost

## [0.4.0] — 2026-02-19

### Added
- Directmedia DKI decoder module
- DigiBib research snapshot for reversing
- Enhanced entropy and hexdump analysis
