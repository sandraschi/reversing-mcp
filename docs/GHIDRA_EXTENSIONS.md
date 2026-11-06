# Ghidra Community Extensions - download + CRUD

`src/reversing_mcp/ghidra_extensions.py` + MCP `ghidra_extensions(operation=...)` + REST `/api/v1/extensions/*` + webapp `/extensions`.

## Why this exists

Stock Ghidra 12.1.3 ships 39 processors but **no 65c816** (SNES Ricoh 5A22) - only
`6502` + `65C02` in `Processors/6502/data/languages/6502.ldefs`. The stock
`Ghidra/Extensions` dir is empty. SNES work needs a community extension, and
agents kept hand-installing zips. This page owns that lifecycle.

## Curated catalog (SNES-first, URLs verified 2026-11-06)

| Name | Repo | Kind | Notes |
|------|------|------|-------|
| ghidra-65816 | achan1989/ghidra-65816 | processor | WDC 65816 SLEIGH. Install FIRST (language 65816:LE:16:default) |
| ghidra-snes-loader | Raikaru/ghidra-snes-loader | loader | LoROM/HiROM + DBR/DP tracker. Modern fork of the archived achan1989 loader |
| ghidra-snes-loader-upstream | achan1989/ghidra-snes-loader | loader | Archived upstream, provenance only (manual) |
| ghidra-snes-scripts | joshleaves/ghidra-snes | scripts | Scripts, not an Extension zip (manual clone into ghidra_scripts) |
| ghidra-findcrypt | TorgoTorgo/ghidra-findcrypt | analyzer | Crypto constants auto-analysis |
| FindCrypt-Ghidra | d3v1l401/FindCrypt-Ghidra | scripts | Older script line (manual) |
| Ghidrathon | cmu-sei/Ghidrathon | scripting | CPython 3 in Ghidra (manual, version-pinned) |
| BinExport | google/binexport | diffing | BinDiff exporter (manual, version-pinned) |

Entries with `install_kind=github_release` install from the repo Releases page
(asset regex match, latest unless `version` given). `manual` entries refuse
honestly with the repo pointer - no guessed URLs.

## Operations

MCP `ghidra_extensions(operation="list|catalog|install|remove|enable|disable", name?, version?, confirm?)`:

- `catalog` - curated entries + installed/enabled flags.
- `list` - dirs found in `%APPDATA%/ghidra/ghidra_*_PUBLIC/Extensions` (incl. `<name>.disabled` rows).
- `install` - catalog name, `owner/repo` shorthand, or direct https `.zip` URL. Unzips into the user Extensions dir.
- `remove` - needs `confirm=True` (deletes the dir).
- `enable`/`disable` - reversible rename `<name>` <-> `<name>.disabled`. Restart Ghidra to pick up.

REST mirrors: `GET /api/v1/extensions`, `GET /api/v1/extensions/catalog`,
`POST /api/v1/extensions/install {name, version?}`,
`POST /api/v1/extensions/remove {name, confirm}`,
`POST /api/v1/extensions/enabled {name, enabled}`.

Build-from-source extensions (SLEIGH/Java gradle) report `needs_build` with the
repo pointer rather than faking a zip install.

## SNES bring-up order

1. `install ghidra-65816`, restart Ghidra, verify `65816:LE:16:default` in language list.
2. `install ghidra-snes-loader`, restart, import SMC/SFC via the SNES loader.
3. Optional: clone `joshleaves/ghidra-snes` scripts into `ghidra_scripts`.

## Webapp

`/extensions` page: catalog table (installed badge, kind, targets) + installed
table (enabled toggle, remove with confirm) + install-by-name/URL box. Dark
Slate-950 cards, `data-testid="extensions-page"`.
