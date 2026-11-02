# HANDOVER — reversing-mcp

Date: 2026-11-02 (v0.5.0 Release — Hercules DJ Console MK1 2003 Hardware Virtualizer, HID Decoder, MIDI Bridge, and Shell CAD). Session by Sandra + agent.

## What was being worked on

1. **Hercules DJ Console (MK1 - 2003) Hardware Virtualizer (`/hardware/hercules_mk1.py`)**:
   - 16-byte raw USB interrupt IN report decoder on EP 1 IN (`0x06F8:0xB100`).
   - Virtual console state machine emulating dual jog wheels (relative velocity ticks), 45mm crossfader, pitch sliders, 3-band EQs, and 28 rubber tactile buttons.
   - EP 2 OUT 4-byte interrupt LED report encoder.
   - `HerculesMK1MidiBridge` translating raw HID events into standard MIDI CC and Note On/Off for modern software (Mixxx, Ableton, FL Studio).
   - 5 FastMCP tools: `hercules_hw_info`, `hercules_virtual_spin`, `hercules_virtual_fader`, `hercules_virtual_button`, `hercules_decode_packet`.
   - Parametric OpenSCAD design for replacement faceplate guard / deck-saver and carrying strap clamp (`hardware/hercules-mk1/shell_carrier.scad`) replacing the lost original smoked clamshell.
   - Complete technical documentation in `docs/hardware/HERCULES_DJ_CONSOLE_MK1.md`.
   - Unit tests: 6/6 tests passing in `tests/test_hercules_mk1.py`.

2. **HP 200LX Palmtop PC Station (`/hardware-hp200lx`)**:
   - Intel 80186-compatible Hornet ASIC SoC @ 7.91 MHz (static CMOS, overclockable to 16 MHz).
   - 640×200 CGA monochrome transflective LCD with rotary contrast and desk lamp illumination controls.
   - Interactive 3D clamshell model with adjustable lid hinge angle (0° to 180°), 80-key chiclet keyboard with blue application keys, PCMCIA slot, serial port, and IrDA window.
   - Built-in ROM software switcher: Lotus 1-2-3 Rel 2.4 (live spreadsheet with formulas), HP 19BII Business Consultant II Calculator (financial & RPN modes), MS-DOS 5.0 prompt with directory listing, and Filer.
   - Authentic 2400 Hz piezo buzzer audio click synthesis and full physical PC keyboard capture in fullscreen.
   - Technical dossier in `docs/HP200LX.md` covering silicon architecture, 3MB ROM memory map, PCMCIA/CF storage, 32 MHz crystal overclocking mod, and emergency ham radio / packet TNC field usage.
2. **GRiDCase 1550 SX Flagship Station (`/hardware-grid1550`)**:
   - Intel 80386SX @ 20 MHz, full 640×480 VGA amber gas-plasma panel (10-inch un-letterboxed).
   - Authentic 3D magnesium case geometry, twin barrel hinges, rear heat vents, and DB-25/DB-9/Centronics connectors.
   - IsoPoint roller-bar pointing device beneath the spacebar with thumb clickers.
   - Modular Power Pod system: hot-swap toggle between AC Mains Supply Pod and Rechargeable NiCad Battery Pod.
   - One-click fullscreen toggle (`requestFullscreen`).
   - Active physical PC keyboard capture in fullscreen or live mode: typing directly sends scan codes into the terminal.
   - MS-DOS 5.00 + Ashton-Tate Framework III: preloaded with the Austrian Energy Corporation (Wien) Grid Telemetry Application (`AUSTRIA.FW3`).
3. **GRiDCase 1520 Restorations (`/hardware-grid`)**:
   - Die-cast magnesium tub body, Citizen floppy bay, cooling louvers, Micro Switch ST keyboard, dual GRiDROM slots, Framework II runtime, fullscreen PC keyboard input capture.
4. **Korg M1 Music Workstation Studio (`/hardware-m1`)**:
   - Studio lighting, 61-key ivory/black keybed, KLM-1266 PCB 3D inspection view with chip inspection.
   - Complete 100 Factory Programs (Prog 00–99) & 100 Factory Combinations (Combi 00–99) soundbank explorer (`web_sota/src/data/korg-m1-bank.ts`).
   - Removed toy minisynth oscillator attempt; documented the AI PCM Rompler architecture (4 MB 16-bit 32 kHz mask ROMs, Fujitsu MB87402 TG, MB87404 VDF, MB87405 MDE).
   - Live Web MIDI Output Router to connect via virtual MIDI cable (`loopMIDI`) to DAW tracks running Korg M1 VST3 or hardware M1, broadcasting Program Changes (`0xC0 [num]`) and Note On/Off (`0x90`/`0x80`).
   - Comprehensive VST3 & Reversed Emulation architecture analysis covering Korg Collection M1 (bit-accurate C++ oracle) and Vintage Emulator Studio (VES, JUCE + MAME core).
   - SysEx Preload Data Loader & 64 KB NVRAM (`0x00000–0x0FFFF`) memory map breakdown.
5. **Software History Archive in `mcp-central-docs`**:
   - Created `reference/SOFTWARE_HISTORY.md` covering S-100 bus, SCP 86-DOS (including user's framed 8-inch disk Serial #87 before Gates buyout), Ashton-Tate Framework & FRED (including the 15-year Vienna energy plant telemetry system), Borland Turbo Pascal, and other early software greats.
6. **Gym ClickerLab (G1b + G3 + Tier 3 §5 correlate)** — earlier session:
   - `src/reversing_mcp/clickerlab.py`, `scripts/cua_tour.py`, `web_sota/src/pages/clickerlab.tsx`, ReVa lifecycle, Ghidra 12.1.3 integration.

## Last concrete action

1. Built HP 200LX interactive 3D station (`/hardware-hp200lx`) and documented in `docs/HP200LX.md`.
2. SOTA webapp build verified with zero errors (`bun run build` exit 0, built in 7.67s).
3. Korg M1 updated with 100 Factory Programs + 100 Combinations, VST3 architecture analysis, and Web MIDI Output routing.
4. Documented in `docs/KORG_M1.md` and `mcp-central-docs/reference/SOFTWARE_HISTORY.md`.

## Status of tests/gates

- Frontend: `bun run build` (`tsc -b && vite build`) completed cleanly with 0 errors.
- Working tree verified with `.bak` files present for modified files.

## Uncommitted files (assess the working tree, not HEAD)

- `web_sota/src/pages/hardware-hp200lx.tsx` (new)
- `web_sota/src/pages/hardware-m1.tsx`
- `web_sota/src/pages/hardware-grid1550.tsx` (new)
- `web_sota/src/pages/hardware-grid.tsx`
- `web_sota/src/pages/hardware-index.tsx`
- `web_sota/src/data/korg-m1-bank.ts` (new)
- `web_sota/src/App.tsx`
- `web_sota/src/components/layout/sidebar.tsx`
- `docs/HP200LX.md` (new)
- `docs/KORG_M1.md`
- `mcp-central-docs/reference/SOFTWARE_HISTORY.md` (new)

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
- Item 3 (stage 2 oracle) DONE: Frida file-API agent (CreateFileW/ReadFile/
  WriteFile/CloseHandle, handle-tracked offsets, OVERLAPPED honored, 64 B head
  samples) + cancellable `frida_oracle()` (one session, per-slice agent reload,
  stop lands in seconds) + `_stage_oracle` in the G1 flow (confirm + accept_local
  gates, `refused` results fail quietly without tracebacks) + `advance` params
  (MCP + REST). Live on calib_win32: 24 events, font-cache read mapped with
  offset. Two live-fire fixes: CloseHandle counted non-file handles (now
  `known`-gated), process_exited sampled post-kill (now pre-cleanup).
- Regression note #2: same bulk-regex lesson re-learned on analyzers.py —
  reverted, re-applied surgically. Rule stands.
- Regression note: an over-broad sed-style regex edit touched 14 unrelated
  except blocks; reverted via git checkout and re-applied surgically. Lesson
  kept: no bulk regex on source, ever.

## Claude items 5-6 session (same day)

- **Item 5 (correctness) DONE**: snapshot `(dict, truncated)` tuple carried
  into every diff record; liveness checks inside menu/control/canvas loops;
  `compare_sessions()` determinism scorer (timestamps/pids/shots excluded by
  design) + artifact; live double-run of a 4-step calib tour scored
  **4/4 identical (1.00)** — intent resolution, OCR reads, probe-file
  detection all agreed. Tests for truncation, compare/diverge, liveness.
- **Item 6 (map export) DONE**: `export_map()` — Ghidra plate comments on
  defined-string addresses (NOT file math: loader rebases, proven live),
  opt-in FUN_* renames, plus `map_import_ida.py` with a rebase guard
  (verifies bytes before commenting). Live on calib: **22 Ghidra comments**,
  IDA script with real VAs. `file_offset_to_va()` kept (struct-only PE
  parse) for the IDA path; two of its bugs found live (6-byte header read,
  PE32+ base offset).
- Item 4 (VM isolation) + item 7 (static depth) still open.

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
