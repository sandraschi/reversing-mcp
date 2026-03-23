# Digibib5.exe — plan of attack (full reverse)

**Purpose:** Single reference for **reversing `Digibib5.exe`** to learn the real **Directmedia / `.DKI`** read-and-decode path. **`Digibib5.exe` is a deliberately chosen example:** a modest-sized app used to **stress-test** reversing-mcp + webapp + Ghidra/ReVa — **not** a claim that the same workflow scales to enormous binaries (e.g. full Office).

**ReVa:** Decompilation and Ghidra-side MCP tools come from the **ReVa** server (`reverse-engineering-assistant`), **not** from reversing-mcp’s `server.py`.

The in-repo zlib-style **heuristic** (`directmedia_dki.py`) is **not** a substitute for EXE-led analysis on large **`text.dki`** volumes (see empirical notes below).

**Related:** [DIRECTMEDIA_MISSION.md](DIRECTMEDIA_MISSION.md) · [DIRECTMEDIA_REVERSING_TOOLKIT.md](DIRECTMEDIA_REVERSING_TOOLKIT.md)

---

## 1. Baseline and scope

| Item | Notes |
|------|--------|
| **Primary binary** | `Digibib5.exe` (PE). Also scan **co-installed DLLs** in the same folder for codec/UI code. |
| **Reference volumes** | Keep at least one **small** volume (e.g. `DBSK01`) and one **large** (e.g. `DB094`) on disk for structure checks. |
| **Success criterion** | Documented pipeline: **open file → parse headers → decode packed stream → text encoding** for `text.dki`, plus how **indices** reference body text. |

---

## 2. Tooling (fixed stack)

- **Ghidra** as primary IR + decompiler.
- **ReVa MCP** (`reverse-engineering-assistant`) for interactive IDE workflows.
- **Headless Ghidra** optional: `analyze_binary(..., ['ghidra'])` when `analyzeHeadless` is available.
- **This repo:** `get_hexdump`, `hex_peek.py`, `digibib_research_snapshot`, strings/PE — **supporting** evidence only.

Maintain one **evidence log** (addresses, renamed functions, struct layouts, file offsets verified against hex).

---

## 3. Phase A — Orientation

- PE: imports (**CreateFile**, **ReadFile**, **MapViewOfFile**, any **RtlDecompress** / **mspack** / zlib if present), sections, resources.
- String census: `TEXT.DKI`, `.dki`, `digibib.txt`, `index.`, `zlib`, `inflate`, `deflate`, UI errors.
- Find **WinMain** / message loop; note runtime (Delphi, MSVC, etc.) if identifiable.

**Exit:** 10–20 **anchor strings** to xref first.

---

## 4. Phase B — File I/O graph

- From **file APIs**, work **up** the call graph.
- Separate: **config** (`digibib.txt`), **TOC** (`tree.dki`, `tree.dka`), **body** (`text.dki`), **indices** (`index.htx`, `index.plx`, `index.ttx`, `index.wlx`, `index.set`, …).

For **`text.dki`**, locate logic that:

1. Reads the **first dwords** (header).
2. Consumes the **large `uint32` offset table** (monotonic file offsets).
3. Enters the **packed payload** reader for records.

**Exit:** Ghidra folder or tag set `text_dki_pipeline` with **entry** + 2–3 levels of callees named.

---

## 5. Phase C — Codec identification

On the packed-stream path, identify:

- Calls to **`inflate` / `uncompress` / zlib** (import or dynamic).
- **COM** / **Windows compression** APIs.
- **Custom** bitstream + tables (Huffman/LZ-style loops).

**Exit:** One-sentence verdict: e.g. *“Custom container + zlib per block”* or *“Fully custom Huffman/LZ”* — whatever Ghidra shows.

---

## 6. Phase D — Minimal written spec

Document (in-repo Markdown is fine):

- Header field layout and endianness.
- Offset table semantics (record boundaries: `[off[i], off[i+1])` or documented alternative).
- Post-decode **encoding** (e.g. CP1252 vs UTF-16).
- **Validation:** decode at least **one section** in a standalone script; compare to known TOC phrase or unique string.

---

## 7. Phase E — Indices and navigation

- **`tree.dka`:** binary tree; correlate with `tree.dki` text TOC.
- **Index family:** same **header family** as `text.dki` / `index.set` on sampled volumes (e.g. leading `CC 24 19 00` with varying second dword). Extensions **`.htx` / `.plx` / `.ttx` / `.wlx`** are **Directmedia-internal** index partitions; they are **not** the same as unrelated formats that reuse `.htx` (e.g. legacy Microsoft Index Server HTML templates).

**Exit:** Document how **search / jump** resolves to **record id or file offset** in `text.dki`.

---

## 8. Definition of “full decompile”

Target **full behavioral coverage** of the read/display pipeline, not necessarily every line of UI code decompiled. Prioritize: **`text.dki` → indices → rest.**

---

## 9. Risks and ethics

- If the PE is **packed**, establish **OEP / unpack** before deep analysis.
- Reverse only **your licensed** install; goal **interoperability / preservation**; no DRM circumvention narrative in tooling artifacts.

---

## 10. Empirical notes (fleet, 2026-03)

These observations inform the plan; they are **not** a format spec.

| Observation | Implication |
|-------------|-------------|
| **`tree.dki`** on sampled volumes (`DBSK01`, `DB094`) is often **plain CP1252-style text** (TOC), not zlib-wrapped. | Do not expect one decoder for all `*.dki` names. |
| **`text.dki`** on `DB094`: header + **~1.65 MiB `uint32` LE offset table**, then **binary packed stream** (not trivial whole-file zlib from file start). | Heuristic zlib scan **fails by design** here until real codec is found in EXE. |
| **`index.set`** shares the same **first dword** as `text.dki` on the sample; second dword differs (`02` vs `04`). | Treat indices as **same format family**, different subtype. |
| **Public GitHub:** no widely used **TEXT.DKI / Directmedia** decoder repo found; **DiBiLit** corpora are unrelated (TEI/text archive, not this binary format). | Expect **primary source = binary reverse**. |

---

## 11. Library paths (optional automation)

- Env **`DIGITALE_BIBLIOTHEK_ROOT`** or default resolver under `directmedia_dki.resolve_digitale_library_root()` for batch tools (`decompress_directmedia_library`). **Ghidra work** does not depend on path.
