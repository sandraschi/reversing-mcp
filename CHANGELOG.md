# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- **Security**: `tauri.conf.json` bundled `.env` (API keys) instead of `.env.example` — fixed
- **Port conflict**: `vite.config.ts` used port 10750 (same as backend) → changed to 10751
- **Stale `.bak` files**: Removed 7 orphaned backup files from `src/`, `web_sota/`, `mcpb/`

### Added
- `.env.example` at repo root (was missing entirely)
- `llms.txt` — LLM discovery index with all 13 tools listed and API reference
- `CLAUDE.md` — Agent behavioral instructions with tool table and quick start
- `.cursorrules` — Cursor IDE rules file
- Updated `AGENTS.md` with full 13-tool table, architecture map, and linting rules

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
