# Reversing MCP — roadmap

## Current focus

- **Digitale Bibliothek 5 / Directmedia:** reverse `Digibib5.exe` per [docs/DIGIBIB_DECOMPILE_PLAN.md](docs/DIGIBIB_DECOMPILE_PLAN.md); align `directmedia_dki.py` with findings.
- **Stability:** keep static MCP tools, webapp, and tests passing on supported Python versions.
- **Ghidra:** ReVa MCP for interactive work; headless scripts where configured.

## Near term

- Document any proven `text.dki` / index layout in `docs/`.
- Optional: MCPB manifest, CI, packaging — see [ASSESSMENT.md](ASSESSMENT.md) if revived.
- **Engine wrappers (phase 3):** Frida (`frida_trace`, `frida_script` - see [docs/FRIDA.md](docs/FRIDA.md)),
  Detect It Easy (compiler/packer ID), capa (capability-to-function map). Each ships with a
  `docs/<ENGINE>.md`, tests, and a row in [docs/ENGINES.md](docs/ENGINES.md).
- **Verify unverified engines** on a host that has them: radare2 `afl` parsing, binwalk `-J`
  output, IDA 9.x detection.

## Later

- **CUA clicker for new targets (UI/UX analysis first, then deep static).** Workflow for an
  unknown app: (1) CUA bot clicks through the UI and records screens, controls and flows;
  (2) rebuild the UI from that record (UX analysis / reimplementation reference);
  (3) Ghidra & co. for the functionality behind it, where possible. Steps 1 and 3 are the
  Tier 3 spec ([docs/CUA_DISASSEMBLY_COMBO.md](docs/CUA_DISASSEMBLY_COMBO.md)); step 2 (UI
  rebuild) is new and not yet specced. Reference approach: the ArtCraft team's CUA
  UX-analysis bot (details to be collected).

## Out of scope (unless explicitly picked up)

This repo does not commit to unrelated format catalogs (scientific archives, game engines, enterprise legacy systems) unless someone drives a concrete issue and maintenance plan.
