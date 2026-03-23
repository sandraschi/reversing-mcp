# Primary Mission: Directmedia / Digitale Bibliothek 5

## Goal and scope

**Digibib5.exe** and the **`.DKI`** / Directmedia stack are the **reference example and test case** for reversing-mcp and its webapp: a **small-to-medium** Windows reader (not a huge suite like Word). The point is to validate the toolchain on a real app and to learn **how those files are read and expanded** — **not** to target arbitrarily large binaries.

**ReVa:** Interactive Ghidra MCP tools (**decompile, xrefs, …**) are implemented by the **ReVa** project and exposed as a **separate MCP server**. This repository does **not** embed or re-export ReVa’s tool list; it provides **static** analysis, optional **headless** Ghidra, and DKI heuristics.

## Target binary

- **Path (typical install):** `C:\Program Files (x86)\Digitale Bibliothek 5\Digibib5.exe` (or fixture under `tests/fixtures/exe files\`)
- **Role:** Reader for Directmedia “Digitale Bibliothek” (1990s e‑book product); proprietary containers (e.g. DKI).
- **Objective:** Reverse the read/expand path enough to document or reimplement decoding (preservation / tooling).

## How this repo supports that

- **Ghidra via ReVa (separate MCP):** In Ghidra, use **ReVa** from your IDE’s MCP client for decompilation, xrefs, renames. Pair with **reversing-mcp** for strings, PE, hexdump, `digibib_research_snapshot`, etc. For large-volume **`text.dki`**, packed data is **not** reliably decoded by zlib heuristics alone — see **[DIGIBIB_DECOMPILE_PLAN.md](DIGIBIB_DECOMPILE_PLAN.md)**.
- **Binary analysis:** Strings, entropy, PE analysis to get an overview before deep dive in Ghidra.
- **Directmedia .DKI decoder:** In-repo **heuristic** decoder (`src/reversing_mcp/directmedia_dki.py`) tries zlib/gzip and common header skips. It may help **some** small or zlib-wrapped blobs; **`tree.dki`** on real volumes is often **plain CP1252 text**, while **`text.dki`** on large books uses a **header + offset table + proprietary packed stream** — extend or replace logic only after the EXE path is understood. MCP: `decode_dki_file` / `analyze_directmedia_file`.
- **Web UI + Ollama:** Load the binary, run analyses, and use the chat to reason about findings with a local LLM.

## Suggested workflow

See **[DIRECTMEDIA_REVERSING_TOOLKIT.md](DIRECTMEDIA_REVERSING_TOOLKIT.md)** for CLI/MCP commands (`digibib_research_snapshot`, `scripts/analyze_digibib.py`). **Phased reverse plan:** **[DIGIBIB_DECOMPILE_PLAN.md](DIGIBIB_DECOMPILE_PLAN.md)**.

1. Import `Digibib5.exe` into Ghidra (create a project, run analysis).
2. Add **ReVa** to your MCP client and connect it; use ReVa tools (names differ from old `ghidra_*` — discover via your host).
3. Use MCP from the IDE: list functions, search strings (“DKI”, “expand”, “read”, …); decompile; follow xrefs. Use this repo’s webapp/static tools for overview (strings, PE, entropy, `get_hexdump` / `scripts/hex_peek.py` on small files).
4. Follow **Phase B–C** in **DIGIBIB_DECOMPILE_PLAN.md** until the **`text.dki`** reader and codec are identified; then update `directmedia_dki.py` or add a spec-driven module.
5. Document the read/expand logic in-repo (`docs/`) and implement a faithful decoder or viewer pipeline.

## Legal / ethics

Reverse engineering for **interoperability and preservation** of abandoned software and formats is the stated use. Ensure your use complies with local law and any applicable licenses.
