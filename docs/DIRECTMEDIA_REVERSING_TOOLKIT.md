# Directmedia / Digibib5 — reversing toolkit

Goal: use **Digibib5.exe** and **Directmedia** (`.DKI` / `TEXT.DKI`) as the **reference test case** for whether we can **read, decode, and eventually display** that stack — a **small/medium app** exercise, not a goal to decompile arbitrary huge programs.

**Full EXE reverse (needed for packed body text):** **[DIGIBIB_DECOMPILE_PLAN.md](DIGIBIB_DECOMPILE_PLAN.md)** — phased Ghidra + **ReVa MCP** (ReVa is a **separate** server; reversing-mcp does not implement its tools), volume notes, and why zlib heuristics miss typical **`text.dki`**.

## 1. Target binary

| Location | Notes |
|----------|--------|
| `tests/fixtures/exe files/Digibib5.exe` | Local fixture (you copy the exe here; not in git) |
| `C:\Program Files (x86)\Digitale Bibliothek 5\Digibib5.exe` | Typical install |

## 2. Automated static snapshot (no Ghidra GUI)

**MCP (reversing-mcp):**

- `digibib_research_snapshot()` — tries fixture path, then Program Files.
- `digibib_research_snapshot("D:\\\\...\\\\Digibib5.exe")` — explicit path.

Returns: file size/type, PE summary, entropy outline, strings matching Directmedia-related keywords, `next_steps`, `viewer_roadmap`.

**Decode a .DKI (built-in):**

- MCP: `decode_dki_file("D:\\\\...\\\\TEXT.DKI")` — strategy + preview, no sidecar file.
- MCP: `analyze_directmedia_file(same_path)` — decode and write `TEXT_extracted.txt` beside the .DKI.

**CLI:**

```powershell
Set-Location D:\Dev\repos\reversing-mcp
uv run python scripts\analyze_digibib.py
uv run python scripts\analyze_digibib.py --output artifacts\digibib_snapshot.json
```

**PowerShell helper:**

```powershell
Set-Location D:\Dev\repos\reversing-mcp
.\scripts\Run-DigibibResearch.ps1
.\scripts\Run-DigibibResearch.ps1 -Output artifacts\digibib_snapshot.json
```

## 3. Headless Ghidra (optional)

If Ghidra is on `PATH` / `GHIDRA_HOME` / `GHIDRA_INSTALL_DIR` per `analyzers.py`:

- `analyze_binary("...\\Digibib5.exe", ["ghidra"])` — full headless JSON via `ghidra_scripts/analyze_binary.py`.

## 4. Interactive decompilation (ReVa)

1. Install Ghidra + **ReVa** extension (`external/reverse-engineering-assistant` clone or releases).
2. Add **ReVa** MCP in Cursor / Claude Desktop (`docs/GHIDRA.md`).
3. Import `Digibib5.exe`, auto-analyze, then use ReVa tools to:
   - list / filter strings (`DKI`, `ReadFile`, …);
   - xref from imports and candidate strings;
   - decompile readers and decompress paths.

## 5. Volume layout (observed, not a vendor spec)

On a typical band folder (`…\DBxxx\Data\`):

| Artifact | Typical role |
|----------|----------------|
| `digibib.txt` | INI-style metadata (caption, build, flags). |
| `tree.dki` | Often **plain text** TOC (CP1252-style); **not** the same as packed `text.dki`. |
| `tree.dka` | **Binary** navigation parallel to `tree.dki`. |
| `text.dki` | **Main body**: header + large **`uint32` offset table** + **packed** stream (codec from EXE). |
| `index.set`, `index.htx`, `index.plx`, `index.ttx`, `index.wlx` | **Search/navigation indices**; same header *family* as `text.dki` on sampled volumes. `.htx` here is **not** Microsoft Index Server HTML templates. |
| `*.bmp`, `lemmata.txt`, `*.tab`, `sigel.lib`, … | Assets / plain sidecars. |

## 6. Viewer milestones (summary)

1. **Baseline** — store `digibib_research_snapshot` JSON per build.
2. **Read path** — Ghidra: named functions for `text.dki` / indices (see **DIGIBIB_DECOMPILE_PLAN.md**).
3. **Format** — written spec + decoder matching EXE (replace guesswork where needed).
4. **Viewer** — decode pipeline + UI; parity checks against original app.

## 7. Legal / ethics

Interoperability and preservation only; comply with local law and licenses. Do not ship copyrighted ebook payload with tooling.

## 8. Related docs

- `docs/DIRECTMEDIA_MISSION.md` — mission statement
- `docs/DIGIBIB_DECOMPILE_PLAN.md` — phased decompile / spec plan
- `docs/GHIDRA.md` — ReVa vs headless
- `.cursor/skills/reversing-expert/SKILL.md` — agent workflows
