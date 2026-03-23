# Cursor Handoff — reversing-mcp

**Created:** 2026-03-23  
**Purpose:** Orient Cursor agents to the current state of this repo, especially the
three external reference clones and what to do with them.

---

## Current Status: LaurieWired bridge removed (2026-03-23)

**Done:** `bridge_mcp_ghidra.py` deleted; all `ghidra_*`, `start_ghidra`, and
`ghidra_setup_help` MCP tools removed from `server.py`. **reversing-mcp** is a
**companion server** (static analysis + Directmedia). **Ghidra MCP:** add **ReVa**
(reverse-engineering-assistant) in the client. See `docs/GHIDRA.md` and
`TODO_REFACTOR.md` Phases 2+.

**Reference repos under `external/`** (ReVa vs mrphrazer, etc.) remain for evaluation
and optional second MCP server.

**What still works and is NOT changing:**
- `analyze_binary`, `extract_strings`, `analyze_entropy`, `get_hexdump`, `analyze_pe_file`
- Directmedia `.DKI` decoder tools
- All scripts in `scripts/`

---

## The Three External Repos

All cloned to `external/` on 2026-03-23. Do not modify them — they are reference copies.
Update with `git pull` inside each directory if you need latest.

### `external/GhidraMCP/` — LaurieWired (7.6k ⭐)
**What it is:** Java Ghidra plugin (HTTP server on :8080) + Python bridge.
**Architecture:** GUI-required. Plugin runs inside Ghidra, exposes ~40 tools over HTTP.

> ⚠️ **FUNDAMENTAL LIMITATION — READ THIS FIRST**
>
> LaurieWired's GhidraMCP is **not headless and cannot be made headless**. It is
> architected around a human sitting at a running Ghidra GUI, with a binary already
> loaded and the plugin manually started. Every single Ghidra operation requires that
> human precondition. An agent cannot open Ghidra, cannot load a binary, cannot start
> the plugin — it can only call tools against an already-running GUI session.
>
> This makes it **unsuitable for any agentic or automated workflow** — batch analysis,
> overnight runs, CI/CD pipelines, unsupervised RE tasks. It is an interactive
> co-pilot tool for a human using Ghidra, nothing more. This is why it is being
> deprecated in this project.

**Verdict:** This is what we're already using via `bridge_mcp_ghidra.py`. Do not
invest further in this approach. It is being replaced.
**Key file:** `bridge_mcp_ghidra.py` in repo root — the Python MCP bridge (to be deleted).

### `external/ghidra-headless-mcp/` — mrphrazer (24 ⭐, March 2026)
**What it is:** Pure Python, `pyghidra` backend — **no GUI needed at all**.
**Architecture:** Starts Ghidra headlessly via pyghidra JVM bridge. 212 tools, 34 groups.
**Unique capabilities not in LaurieWired:**
- P-code access (semantic IR, cross-architecture reasoning)
- Full type system (structs, enums, unions, C declarations)
- Transaction + undo/redo (safe agentic mutation)
- `ghidra.eval` / `ghidra.call` — raw Ghidra Python scripting access
- CFG edges, basic block extraction
- Fake backend mode (`--fake-backend`) — test without Ghidra installed
**Key files:**
- `ghidra_headless_mcp.py` — the entry point (run this)
- `ghidra_headless_mcp/` — server implementation
- `FEATURE_SUPPORT.md` — full 212-tool catalog
- `README.md` — setup and Claude Desktop config
**Status:** Very new (3 commits, no releases). **Windows compatibility unconfirmed.**
**How to test without Ghidra:**
```powershell
cd D:\Dev\repos\reversing-mcp\external\ghidra-headless-mcp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python ghidra_headless_mcp.py --fake-backend
# Should start and list 212 tools via MCP
```

### `external/reverse-engineering-assistant/` — ReVa / cyberkaida (619 ⭐)
**What it is:** Ghidra extension (Java) + Python MCP. Two modes: GUI assistant and headless.
**Architecture:**
- Assistant mode: ReVa plugin in Ghidra GUI, serves MCP on `:8080/mcp/message`
- Headless mode: `mcp-reva` binary, pyghidra backend, no GUI — **requires Ghidra 12.0+**
**Design philosophy:** Small tools that return context (xrefs, namespace) alongside
results — specifically designed to reduce LLM hallucination in long RE sessions.
**Claude Code skills included:** Binary Triage, Deep Analysis, Crypto Analysis, CTF
**Key files:**
- `README.md` — full setup for both modes
- `ReVa/skills/` — the Claude Code skill files
- `pyproject.toml` — Python package (`uv tool install reverse-engineering-assistant`)
- `build.gradle` — Java extension build
**Status:** Actively maintained. v7.1.1 released Jan 7, 2026. **PRIMARY RECOMMENDATION.**
**How to install (assistant mode, any Ghidra version):**
```powershell
# Download release zip from GitHub releases page
# In Ghidra: File → Install Extensions → + → select zip → restart
# Enable plugin in: Project view → File → Configure → all plugins → ReVa Application Plugin
# Enable in Code Browser: File → Configure → all plugins → ReVa Plugin → File → Save Tool
# Ghidra now serves MCP at http://localhost:8080/mcp/message
```
**How to install (headless mode, Ghidra 12.0+ required):**
```powershell
$env:GHIDRA_INSTALL_DIR = "D:\path\to\ghidra"
uv tool install reverse-engineering-assistant
# Now run: mcp-reva
```

---

## Architecture Decision: What to Build Next

**Option A — Companion server (RECOMMENDED)**

Keep `reversing-mcp` as a static analysis + Directmedia server only.
Use ReVa (or ghidra-headless-mcp) as a separate dedicated Ghidra MCP server.
Claude Desktop / Cursor connects to both simultaneously.

```
Claude Desktop config:
  reversing-mcp  →  static analysis tools (entropy, PE, hex, strings, Directmedia)
  ReVa           →  all Ghidra tools (decompile, xrefs, rename, p-code)
```

**What to remove from reversing-mcp under Option A:**
- `src/reversing_mcp/bridge_mcp_ghidra.py` — delete
- All `ghidra_*` tool registrations in `server.py` (the `if ghidra_available:` block)
- `start_ghidra` tool
- `ghidra_setup_help` tool
- Optional: one of the two web frontends (keep `web_sota/`, delete `reversing-webapp/`)

**Option B — Integrate pyghidra directly**

Pull mrphrazer's pyghidra approach into reversing-mcp as an optional backend.
More work, single server, full control. Only attempt this after Option A is tested.

---

## First Steps for a Cursor Agent

**Step 1 — Check Ghidra version on this machine:**
```powershell
Get-ChildItem "D:\", "C:\Program Files\" -Recurse -Filter "application.properties" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -like "*ghidra*" } |
    Select-Object -First 3 |
    ForEach-Object { Get-Content $_.FullName | Select-String "application.version" }
```
- Ghidra 12.0+ → ReVa headless mode available
- Ghidra 11.x → ReVa assistant mode only (still good)
- Ghidra not found → install from https://github.com/NationalSecurityAgency/ghidra/releases

**Step 2 — Test mrphrazer fake backend (no Ghidra needed):**
```powershell
cd D:\Dev\repos\reversing-mcp\external\ghidra-headless-mcp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
python ghidra_headless_mcp.py --fake-backend
```
Verify it starts and responds to MCP tool listing. If Windows path issues appear,
check pyghidra JVM setup — known friction point on Windows.

**Step 3 — Install ReVa in assistant mode:**
See instructions in `external/reverse-engineering-assistant/README.md`.
Download the release zip matching your Ghidra version from GitHub releases.

**Step 4 — Add ReVa to Claude Desktop config:**
```json
{
  "mcpServers": {
    "ReVa": {
      "command": "mcp-reva",
      "env": { "GHIDRA_INSTALL_DIR": "D:\\path\\to\\ghidra" }
    }
  }
}
```
Or for assistant mode (Ghidra GUI running with ReVa plugin):
Add `"url": "http://localhost:8080/mcp/message"` transport entry.

---

## What NOT to Do

- Do not modify anything in `external/` — reference clones only
- Do not try to merge LaurieWired's bridge with pyghidra — different architectures
- Do not start the webapp (`start-webapp.ps1`) expecting Ghidra to work — it uses the
  old LaurieWired HTTP bridge on :8080
- Do not `pip install pyghidra` standalone — it must be installed via Ghidra's own
  `support/pyghidra_install.py` script to get the right JVM bindings
- Do not assume `external/ghidra-headless-mcp` works on Windows without testing —
  it was developed on Linux, Windows path handling is untested as of March 2026

---

## Existing Documentation

| File | Content |
|------|---------|
| `README.md` | Install, tools, Digibib5 mission |
| `GHIDRA_PLUGIN_SETUP.md` | LaurieWired plugin setup (historical) |
| `ROADMAP.md` | Current focus: Directmedia / Digibib5 |
| `ASSESSMENT.md` | Original self-assessment |
| `external/README.md` | Index of the three cloned repos |
| `.cursor/skills/reversing-expert/SKILL.md` | RE workflow skill (uses old LaurieWired tools — update after migration) |
| `docs/GHIDRA.md` | Ghidra setup notes |
| `docs/DIRECTMEDIA_MISSION.md` | Directmedia format reversing mission |

**Central docs** (mcp-central-docs):
- `projects/reversing-mcp/README.md` — fleet index, links to upstream docs
- `projects/reversing-mcp/CHANGELOG.md` — fleet doc sync log
- `projects/reversing-mcp/GHIDRA_SOTA_2026.md` — Ghidra/ReVa notes (if present in your clone)
- `projects/reversing-mcp/NEXT_STEPS.md` — action items (if present)
- `research/agentic-ide/CLIENT_CAPABILITY_MATRIX.md` — which MCP clients support sampling
  (relevant: RE agentic workflows need Antigravity or Claude Code, not Claude Desktop)

---

## Skill File Status

`.cursor/skills/reversing-expert/SKILL.md` is **stale** — it documents the old
LaurieWired `ghidra_*` tool names. After the migration to ReVa, update it to reflect
ReVa's tool names and headless workflow. Do not update it until the migration is chosen
and tested.
