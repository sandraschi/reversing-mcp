# HANDOVER — reversing-mcp

Date: 2026-10-14 (updated through toolbox session). Session by Sandra + agent (opencode). Nothing committed.

## What was being worked on

1. **Gym ClickerLab (G1b + G3 + Tier 3 §5 correlate)** — the main thread.
   New: `src/reversing_mcp/clickerlab.py` (elicitation, UIA-BFS rip, tour
   executor, OCR/coordinate fallback, allowlist, capture bundle, correlate),
   `scripts/cua_tour.py`, `web_sota/src/pages/clickerlab.tsx` (`/clickerlab`),
   `gym` ops `elicit`/`clicker_*`/`correlate` + REST routes.
2. **ReVa lifecycle** — `src/reversing_mcp/reva.py` (probe/start/stop), Status
   page start buttons, `reva` MCP tool. Then: real install —
   `D:\Dev\tools\reva\.venv` (ReVa 7.3.1 + MCP-SDK-2.x compat patches, see
   `D:\Dev\tools\reva\README.md`), Ghidra extension upgraded to 7.3.1.
3. **Ghidra 12.0 → 12.1.3** — installed at `D:\Dev\tools\ghidra_12.1.3_PUBLIC`,
   User `GHIDRA_INSTALL_DIR` repointed, 12.0 kept as fallback. REA ghidra
   provider verified working on Digibib5.
4. **Launcher fix** — repo-root `start.ps1` replaced with fleet-engine
   delegation (was a stale Start-Job script); `fleet-start.config.ps1` now
   syncs `dev` + `clicker` extras.

## Last concrete action

Calibration run `cd4e4b014ae2` (Digibib5.exe): intake → triage → elicitation
(89k strings, 25 formats, 200 features) → live rip session (7/27 nodes, app
exited on its own, session concluded `done`) → correlate (14 seeds, 0 mapped /
11 ambiguous / 3 no-trace — correct: no function inventory, generic UIA names).
Backend healthy on :10750, frontend on :10751.

## Status of tests/gates

- Full suite (clickerlab+gym+reva+toolbox): 35 passed. `ruff check` clean,
  `biome ci src` clean, `tsc -b` exit 0. Backend :10750 + frontend :10751 live.

## Uncommitted files (assess the working tree, not HEAD)

M `src/reversing_mcp/clickerlab.py`, `reva.py`, `server.py`, `toolbox.py` (new),
`tests/test_clickerlab.py`, `tests/test_reva.py`, `tests/test_toolbox.py` (new),
`pyproject.toml`, `justfile`, `fleet-start.config.ps1`, `uv.lock`,
`web_sota/src/pages/{clickerlab,status}.tsx`, `scripts/cua_tour.py` (new),
docs (`GYM_SPEC`, `ELICITATION_AND_CLICKER`, `CUA_DISASSEMBLY_COMBO`, `REVA`,
`ONBOARDING`, `ENGINES`, `TOOLS`, `DEVELOPMENT`, `TOOLBOX` (new),
`ARCHITECTURE` (new)), `llms-full.txt`, `CHANGELOG.md`, `HANDOVER.md`.

## Machine-only state (not in git, invisible off this machine)

- Ghidra 12.1.3 `D:\Dev\tools\ghidra_12.1.3_PUBLIC` (+12.0 fallback in
  `C:\Program Files\`); User env `GHIDRA_INSTALL_DIR` repointed (stale in
  long-lived processes — backend was restarted to pick it up).
- ReVa venv `D:\Dev\tools\reva\.venv`, ext 7.3.1 in Ghidra user dir
  (old ext backed up `*.20261014_034500.bak`, dup jars in `_reva-pruned-7.3.1`).
- Tesseract 5.5 at `C:\Program Files\Tesseract-OCR`. Stale GhidraMCP ext
  disabled (`_disabled-GhidraMCP`).
- REA sidecar: works with ghidra provider now; `rea doctor` still flags
  Node 24.4.1 (< 24.11 wanted) — non-blocking.

## Live-fire bugs found and fixed (all have regression tests)

TimeoutError swallowed by pass-level excepts; unbounded `%TEMP%` snapshots
(20k budget now); UIA poking of exited processes (per-pass liveness check).
Residual slowness: session-final registry export takes minutes on a big hive.

## What changed since the first handover write (same day)

- **Toolbox session**: `toolbox.py` + `toolbox` MCP tool + 6 REST routes +
  Status Toolbox card (inventory, Install buttons) + FastAPI startup `ensure()`
  (discover, export env, autostart ReVa headless — verified live). IDA glom
  rule per instruction (running instance wins; licensing never checked).
  Live inventory: ghidra 12.1.3, reva, capa 9.4.0, die 3.21 ready; frida/r2
  one click away; hopper N/A-on-Windows; ida missing (glom when started).
- **Docs session**: new `docs/TOOLBOX.md` + `docs/ARCHITECTURE.md`; tool
  counts corrected to 20 everywhere; ONBOARDING zero-hand-editing flow;
  CHANGELOG 2026-10-14 entry; this handover.

## Ollama session (same day)

- Dashboard said "no Ollama, install it" while Ollama sat installed-but-idle
  (tray app up, `:11434` down). Same dead-end-notice disease as env editing.
- Fix: three-state Ollama (`serving` > `installed` > `missing`) in toolbox +
  `POST /api/llm/ollama/{start,install,pull}` + dashboard action button
  (`onboarding-action`, 10s poll shows progress). Toolbox inventory grew to 12.
- Live proof: pressed Start via API → daemon up → **32 models already on disk**,
  default `qwen3.8:27b`, cue cleared to `ready/chat`. Nothing was ever missing
  except the daemon.

## Dashboard hero session (same day)

- Dashboard had no identity (generic title, 4 static KPIs, dead-end Ollama
  notice). Rewrote `web_sota/src/pages/dashboard.tsx`: hero (what-this-is +
  4 CTAs), 6 live KPIs (backend+uptime, tools, toolbox ready/total, gym runs,
  AI models, Ghidra), active-operations panel (running Gym stages), mini-log
  (last 8 `/api/logs` entries). All feeds verified live; tsc/biome clean.
  Backend untouched (no new endpoints needed).

## Help engines session (same day)

- Help Engines tab had one-line wiring rows and Guide links pointing at GitHub
  blob URLs. Fixed: 11 what+does blurbs inline (several lines each, grounded in
  docs/*.md), new `GET /api/docs/{name}` (allowlisted to docs/, traversal
  probed → 404), in-app expandable viewer with a zero-dep markdown subset
  renderer (`Markdown.tsx`; local .md links recurse in-app), Help tab bar
  converted from overflowing two-line tabs to wrapping pills (killed the
  horizontal scrollbar). `docs/ENGINES.md` table expanded to per-engine
  what+does sections. tsc/biome clean, backend reloaded, endpoint smoked.

## Forensics session (same day)

- Suspect: `N:\Tixati\IDA v9.3.260213 Pro + Fix {CracksHash}\Crack Fix\Crack Fix.zip`
  (sha256 `9D501E3E…B8246BA9`) → quarantined to `D:\Dev\quarantine\crackfix-ida93\`.
  Gym run `4f1ab58368b3` (triage done, capa timed out honestly on 34 MB).
- Static: unpacked MSVC-2022 PE64, NotSigned, 4 benign URLs, no injection APIs.
  Verdict: patched crack, no malware signals, NOT proven clean.
- Reputation: CracksHash has documented malware history (r/Piracy, ANY.RUN Jan
  2024 flag, Vegas-Pro delayed-persistence precedent).
- Decisions: strip-repair needs a legit baseline that doesn't exist (no Pro
  trial per Hex-Rays FAQ; no purchase); deliverable is the patch-map, never a
  rebuilt binary. Sandbox detonation approved in principle, not yet run.
- Casefile: `reports/forensics-crackshash-ida93-2026-10-14.md`.

## Claude-review items 1-2 session (same day)

- **Item 1 (mapped rows) DONE**: root-caused "no function inventory" (auto
  tried r2 only; .bat+Jython dead on Ghidra 12; stale env pinned 12.0).
  Fixes: PyGhidra `ghidra_inventory()` (functions+strings+xrefs, JVM once per
  process, temp project dir), auto fallback r2→ghidra→ida, version-preferring
  detect, all-encodings string extraction (was ascii-only: hid all wide UI
  text), menu regex case fix. Live: notepad 499 fns/242 strings/131 xrefs;
  Digibib5 re-correlate **14 seeds, 5 mapped** (was 0).
- **Item 2 (hermetic calib) DONE**: `tests/fixtures/calib/` (calib_win32.c +
  calib_canvas.c + expected.json + built exes), `scripts/build_calib.py`
  (self-configures MSVC env), `just calib`, `tests/test_calib.py` known-answer
  tests (elicit features, correlate seeds, Ghidra structure) — all green.
- Item 3 (stage 2 oracle) NOT started — next.
- Regression note: an over-broad sed-style regex edit touched 14 unrelated
  except blocks; reverted via git checkout and re-applied surgically. Lesson
  kept: no bulk regex on source, ever.

## Next step

Commit decision (awaiting instruction). Then: B4 LLM layer, VM plumbing,
MCPB pack run, Playwright e2e — all open, see docs statuses.

## Deliberately NOT done

- No commit/push (not requested).
- No NSIS build (no makensis toolchain; Tauri work untouched).
- B4 LLM guidance, Hyper-V VM isolation, version-diff maps, UIA-to-IPC.
- Ghidra 12.0 NOT uninstalled (fallback stays until 12.1.3 proves itself).
- REA `doctor` still flags Node 24.4.1 (< 24.11 wanted) — non-blocking.
- Operator is currently scaffolding `sandraschi/lookcraft` (separate repo).
