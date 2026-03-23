# Reversing MCP — roadmap

## Current focus

- **Digitale Bibliothek 5 / Directmedia:** reverse `Digibib5.exe` per [docs/DIGIBIB_DECOMPILE_PLAN.md](docs/DIGIBIB_DECOMPILE_PLAN.md); align `directmedia_dki.py` with findings.
- **Stability:** keep static MCP tools, webapp, and tests passing on supported Python versions.
- **Ghidra:** ReVa MCP for interactive work; headless scripts where configured.

## Near term

- Document any proven `text.dki` / index layout in `docs/`.
- Optional: MCPB manifest, CI, packaging — see [ASSESSMENT.md](ASSESSMENT.md) if revived.

## Out of scope (unless explicitly picked up)

This repo does not commit to unrelated format catalogs (scientific archives, game engines, enterprise legacy systems) unless someone drives a concrete issue and maintenance plan.
