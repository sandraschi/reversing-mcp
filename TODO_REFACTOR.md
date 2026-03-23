# Refactor TODO — reversing-mcp → Headless Ghidra

**Created:** 2026-03-23  
**Goal:** Remove LaurieWired GUI-dependent bridge, adopt headless approach (ReVa or
mrphrazer), retain static analysis + Directmedia tools.  
**Architecture decision:** Option A — companion server. See `CURSOR_HANDOFF.md`.  
**Estimated effort:** 1–2 days with AI assistance.

---

## Why This Refactor

LaurieWired's GhidraMCP **requires a human sitting at a running Ghidra GUI**. Every
`ghidra_*` tool in the current `server.py` is dead code unless a human has manually
opened Ghidra, loaded a binary, and started the plugin. This is not agentic — it is
remote control of a GUI session.

The goal is: an agent can say "analyse this binary" and get a full RE analysis back,
with no human intervention, no GUI, no manual plugin startup.

---

## Phase 0 — Prereqs (do before touching code)

- [ ] **P0.1** Find Ghidra install path on Goliath:
  ```powershell
  Get-ChildItem "D:\", "C:\Program Files\" -Recurse -Filter "ghidraRun.bat" `
      -ErrorAction SilentlyContinue | Select-Object -First 5 | Select-Object FullName
  ```

- [ ] **P0.2** Check Ghidra version:
  ```powershell
  # Replace path with result from P0.1
  Get-Content "D:\path\to\ghidra\Ghidra\application.properties" |
      Select-String "application.version"
  ```
  - 12.0+ → ReVa headless mode available (preferred)
  - 11.x → ReVa assistant mode only (still good, GUI-based but plugin is less friction
    than LaurieWired)
  - Not found → download from https://github.com/NationalSecurityAgency/ghidra/releases

- [ ] **P0.3** Test mrphrazer fake backend (no Ghidra needed, validates Windows compat):
  ```powershell
  Set-Location "D:\Dev\repos\reversing-mcp\external\ghidra-headless-mcp"
  python -m venv .venv-test
  .\.venv-test\Scripts\Activate.ps1
  pip install -e .
  python ghidra_headless_mcp.py --fake-backend
  # Should start cleanly and respond to MCP tool listing
  # If it errors on Windows path handling → note the issue, proceed with ReVa
  ```

- [ ] **P0.4** Decide: ReVa or mrphrazer?
  - ReVa → most mature, actively maintained, good LLM-optimised tool design
  - mrphrazer → 212 tools, p-code, transactions — more powerful but Windows untested
  - Default: **start with ReVa**, add mrphrazer later if needed

---

## Phase 1 — Strip the LaurieWired Bridge

These are pure deletions. Do them on a branch: `git checkout -b refactor/drop-lauriewired`

- [ ] **1.1** Delete `src/reversing_mcp/bridge_mcp_ghidra.py`

- [ ] **1.2** In `src/reversing_mcp/server.py` — remove the entire bridge import block
  (lines ~30–65, the `try: from .bridge_mcp_ghidra import ...` block and the
  `ghidra_available` flag)

- [ ] **1.3** In `server.py` — remove the entire `if ghidra_available:` tool registration
  block (~280 lines, all the `@mcp.tool() async def ghidra_*` wrappers)

- [ ] **1.4** In `server.py` — remove or gut `start_ghidra()` tool
  (launches Ghidra GUI subprocess — irrelevant for headless approach)

- [ ] **1.5** In `server.py` — remove or gut `ghidra_setup_help()` tool
  (checks LaurieWired plugin connectivity — no longer relevant)

- [ ] **1.6** In `server.py` — update the docstring / module header to remove Ghidra
  bridge references. New description: "Static binary analysis + Directmedia tools.
  For Ghidra integration, connect ReVa MCP server separately."

- [ ] **1.7** In `pyproject.toml` — remove `requests` dependency (only used by the
  bridge to call LaurieWired's HTTP API). Verify nothing else uses it:
  ```powershell
  Select-String -Path "src\reversing_mcp\*.py" -Pattern "import requests" -Recurse
  ```

- [ ] **1.8** In `pyproject.toml` — fix target-version inconsistency:
  `requires-python = ">=3.12"` but `[tool.ruff] target-version = "py310"` — change
  ruff target to `py312`

- [ ] **1.9** Run ruff and fix any new lint errors exposed by deletions:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ruff check src/ --fix
  ruff format src/
  ```

- [ ] **1.10** Run existing tests to confirm nothing static broke:
  ```powershell
  pytest tests/ -x -q
  ```
  Note: Ghidra-dependent tests will now correctly fail/skip — that's expected.
  Static analysis tool tests should all pass.

- [ ] **1.11** Commit: `refactor: remove LaurieWired GUI bridge and ghidra_* tools`

---

## Phase 2 — Install and Configure ReVa

- [ ] **2.1** Install ReVa Ghidra extension:
  - Download release zip from https://github.com/cyberkaida/reverse-engineering-assistant/releases
  - Match the release to your Ghidra version (check release notes)
  - In Ghidra: `File → Install Extensions → + → select zip → restart Ghidra`
  - Enable in Project view: `File → Configure → all plugins → ReVa Application Plugin ✓`
  - Enable in Code Browser: `File → Configure → all plugins → ReVa Plugin ✓ → File → Save Tool`

- [ ] **2.2** Verify ReVa serves MCP:
  - Open Ghidra, open a project, open a binary in Code Browser
  - ReVa should start its HTTP server automatically
  - Test: `Invoke-WebRequest http://localhost:8080/mcp/message -Method GET`
  - Or: open a binary and check Ghidra console for "ReVa MCP server started on port 8080"

- [ ] **2.3** Add ReVa to Claude Desktop config
  (`C:\Users\sandr\AppData\Roaming\Claude\claude_desktop_config.json`):

  **Assistant mode (GUI running — any Ghidra version):**
  ```json
  "ReVa": {
    "url": "http://localhost:8080/mcp/message",
    "transport": "streamable-http"
  }
  ```

  **Headless mode (Ghidra 12.0+ only):**
  ```json
  "ReVa": {
    "command": "mcp-reva",
    "env": {
      "GHIDRA_INSTALL_DIR": "D:\\path\\to\\ghidra"
    }
  }
  ```
  Install headless first: `uv tool install reverse-engineering-assistant`

- [ ] **2.4** Add ReVa to Cursor config (`C:\Users\sandr\.cursor\mcp.json`) — same entries

- [ ] **2.5** Verify ReVa tools are visible in Claude Desktop:
  Load a binary in Ghidra, open Claude Desktop, ask "what functions are in this binary?"
  Expected: Claude calls ReVa tools, gets function list, responds with analysis.

---

## Phase 3 — Update reversing-mcp as Companion Server

With Ghidra handled by ReVa, reversing-mcp becomes a focused static-analysis server.
Update it to reflect this clearly.

- [ ] **3.1** Update `server.py` description and `check_tools()` output:
  - Remove references to Ghidra from `check_tools()` summary
  - Add a note: "For Ghidra analysis, use ReVa MCP server"

- [ ] **3.2** Update `README.md` — rewrite the Ghidra section:
  - Old: "reversing-mcp connects to Ghidra via LaurieWired plugin"
  - New: "For Ghidra analysis, run ReVa alongside this server. See `CURSOR_HANDOFF.md`."

- [ ] **3.3** Update `glama.json` — the current description says "Ghidra and free tools".
  New description: static analysis + Directmedia tools. Remove Ghidra bridge claims.
  This unblocks Glama publication if desired.

- [ ] **3.4** Remove or archive one of the two web frontends:
  - Keep: `web_sota/` (Vite/React, more modern)
  - Archive: `reversing-webapp/` (Next.js, heavier, more complex)
  ```powershell
  # Soft archive — move to git-ignored location, not delete
  Move-Item "reversing-webapp" "archive\reversing-webapp"
  ```
  Add `archive/` to `.gitignore`.

- [ ] **3.5** Update `web_sota/` FastAPI backend (`web_sota/src/`) — remove any
  LaurieWired bridge calls it makes. Replace with: "Ghidra analysis available via
  ReVa — connect ReVa to your MCP client directly."

- [ ] **3.6** Bump version in `pyproject.toml` to `0.2.0`:
  This is a breaking change (ghidra_* tools removed), so minor version bump is correct.

- [ ] **3.7** Commit: `feat: pivot to static-analysis companion server (drop Ghidra bridge)`

---

## Phase 4 — Update Cursor Skill

The `.cursor/skills/reversing-expert/SKILL.md` is now stale — it lists the old
`ghidra_*` tool names. Rewrite for the new split:

- [ ] **4.1** Rewrite the Ghidra section of `SKILL.md`:
  - Old: lists `ghidra_decompile_function`, `ghidra_list_strings`, etc.
  - New: "For Ghidra analysis, use **ReVa** MCP server tools. ReVa tool names differ
    from the old LaurieWired bridge — call `tool_search` on the ReVa server to
    discover available tools."

- [ ] **4.2** Update the "Stack and integration" section:
  - Remove: LaurieWired plugin on :8080
  - Add: ReVa MCP server (assistant mode :8080/mcp/message or headless mcp-reva)
  - Note: for agentic RE workflows (multi-step autonomous analysis), use
    Antigravity or Claude Code — they support `ctx.sample()`. Claude Desktop does not.

- [ ] **4.3** Update workflow sections to use ReVa tool discovery pattern:
  ```
  1. tool_search(query="decompile function") → get ReVa tool schemas
  2. Call ReVa decompile tool with correct params
  ```

---

## Phase 5 — Optional: mrphrazer Integration

Only if ReVa proves insufficient. mrphrazer's headless-mcp adds:
- P-code access (semantic IR)
- Full type system (define structs/enums from C)
- Transaction + undo (safe agentic patching)
- `ghidra.eval` — raw Ghidra Python scripting from MCP

- [ ] **5.1** Confirm Windows compatibility (P0.3 result)
- [ ] **5.2** Install with real Ghidra backend:
  ```powershell
  Set-Location "D:\Dev\repos\reversing-mcp\external\ghidra-headless-mcp"
  .\.venv\Scripts\Activate.ps1
  $env:GHIDRA_INSTALL_DIR = "D:\path\to\ghidra"
  python ghidra_headless_mcp.py --ghidra-install-dir $env:GHIDRA_INSTALL_DIR
  ```
- [ ] **5.3** Add to Claude Desktop config alongside ReVa:
  ```json
  "ghidra_headless": {
    "command": "python",
    "args": [
      "D:\\Dev\\repos\\reversing-mcp\\external\\ghidra-headless-mcp\\ghidra_headless_mcp.py",
      "--ghidra-install-dir", "D:\\path\\to\\ghidra"
    ]
  }
  ```
- [ ] **5.4** Evaluate: does mrphrazer add enough over ReVa to justify running both?
  Decision criteria: need p-code? need transaction/undo for patching? need ghidra.eval?

---

## Phase 6 — Cleanup

- [ ] **6.1** Remove Ghidra project files from repo root:
  - `debug_proj.gpr` (empty Ghidra project file)
  - `debug_proj.lock`, `debug_proj.lock~`
  - `debug_proj.rep/` (Ghidra project directory)
  - `GhidraMCP.zip` (9 bytes, placeholder)
  - `headless_log.txt` (old headless analyzeHeadless run log)

- [ ] **6.2** Clean up test fixtures:
  In `tests/fixtures/` — check `dangerous/` subdirectory contents are appropriate.
  Remove test binaries that were only used for LaurieWired bridge testing.

- [ ] **6.3** Remove stale ruff reports from repo root:
  - `ruff_core.txt` (51KB)
  - `ruff_report.txt` (209KB)
  Add `*.txt` exception or move to `.gitignore`.

- [ ] **6.4** Remove stale test artifacts:
  - `test_results.json`
  - `test_results.txt`
  These are run artifacts, not test definitions — add to `.gitignore`.

- [ ] **6.5** Update `.gitignore` — verify `external/` is listed (added 2026-03-23).
  Also add: `archive/`, `*.txt` (with exceptions for README-type docs), `debug_proj.*`

- [ ] **6.6** Final commit: `chore: cleanup stale files and artifacts`

---

## Phase 7 — Final Verification

- [ ] **7.1** Server starts cleanly with no Ghidra running:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  reversing-mcp
  # Should start, log available tools (static only), no Ghidra errors
  ```

- [ ] **7.2** `check_tools()` returns clean status — no failed Ghidra bridge warnings

- [ ] **7.3** ReVa running in Claude Desktop: decompile a test binary end-to-end

- [ ] **7.4** Static analysis tools verified on a test binary:
  `analyze_entropy`, `extract_strings`, `analyze_pe_file`, `get_hexdump`

- [ ] **7.5** Update memops note — mark refactor complete, note ReVa version installed

---

## File Change Summary

| File | Action |
|------|--------|
| `src/reversing_mcp/bridge_mcp_ghidra.py` | **DELETE** |
| `src/reversing_mcp/server.py` | Heavy edit — remove bridge import block + all `ghidra_*` tools |
| `pyproject.toml` | Remove `requests` dep, fix ruff target-version, bump to 0.2.0 |
| `README.md` | Rewrite Ghidra section |
| `glama.json` | Update description, remove Ghidra bridge claims |
| `.cursor/skills/reversing-expert/SKILL.md` | Rewrite Ghidra tool section for ReVa |
| `reversing-webapp/` | Archive or delete |
| `debug_proj.*`, `GhidraMCP.zip`, `headless_log.txt` | Delete |
| `ruff_*.txt`, `test_results.*` | Delete + gitignore |
| `GHIDRA_PLUGIN_SETUP.md` | Archive or mark OBSOLETE |

**Files NOT changing:**
- `src/reversing_mcp/analyzers.py` — static analysis, keep as-is
- `src/reversing_mcp/logging_config.py` — keep
- `src/reversing_mcp/transport.py` — keep
- `scripts/` — all utility scripts, keep
- `ghidra_scripts/` — keep for reference (may be useful with headless approach)
- `docs/` — keep, update GHIDRA.md to point to ReVa
- `web_sota/` — keep, minor updates to remove bridge references
- `tests/` — keep test structure, some tests will need updating

---

## Branch Strategy

```
main
└── refactor/drop-lauriewired    ← Phase 1 (deletions)
    └── refactor/add-reva        ← Phase 2-3 (ReVa integration)
        └── refactor/cleanup     ← Phase 6 (file cleanup)
```

Merge to main only after Phase 7 verification passes.
