# Tier 3 (spec): Disassembly + CUA click-through = feature-to-code maps

**Status: spec, not built.** This doc describes the target; nothing here is implemented yet.

## 1. Thesis

The Adobe-reversing wave proved *behavioral* RE is legible: drive the app, watch what it does,
everyone understands the output. No disassembler required - the artmarket dev said so explicitly
("i am not disassembling") and still got the whole scene interested.

We have no such qualms. White-box (REA / reversing-mcp: *which code implements feature X?*)
and black-box (CUA tour: *what happens when the user does X?*) are orthogonal, and each
alone leaves the gap the other fills:

| | Answers | Blind to |
|---|---|---|
| Disassembly (REA, ReVa, `analyze_binary`) | which code, which IPC, which bytes | what the feature feels like, which clicks reach it |
| CUA click-through (pywinauto tour) | what the app does step by step, with screenshots | which code ran |

**The product is the correlation: a feature-to-code map.** "Clicking Export calls
`ExportDialog::write` in module Y via function Z, writes bytes matching offset range W."
Neither side produces that alone. This repo is positioned to own it: it already has the
static core, the REA bridge, the DKI/Digibib mission - and the fleet CUA harness.

## 2. Pipeline: Tour -> Capture -> Correlate -> Map

```
Target app (isolated: VM or snapshot, no creds, filtered network)
  |
  v
TOUR      scripted feature walk, fleet CUA stack (pywinauto, title-first UIA,
          existing scripts/cua-smoke.py phases as the base: kill -> launch -> tour -> kill)
  |
  v
CAPTURE   per-step bundle: screenshot, UIA tree, file/registry diff, process diff,
          network/HAR where feasible, clipboard, spawned command lines -> JSONL log + artifacts/
  |
  v
CORRELATE observed runtime strings/behaviors -> static seeds:
          UI labels, URLs, filenames, error text -> extract_strings / rea_investigate(native_search)
          file writes -> hexdump/entropy/DKI offsets
          network endpoints -> string search -> xrefs -> function dossiers
  |
  v
MAP       feature -> { UI evidence, system evidence, code evidence + stated limits }
```

Tour first, disassembly second, always. Triage with `analyze_binary` before launching anything;
never point an executing tour at a target you haven't statically eyeballed.

## 3. Tour runner (reuse, don't reinvent)

Base it on the existing fleet pieces in this repo:

* `scripts/cua-smoke.py` (33 KB, template v14 family): kill -> install/launch -> window verify ->
  screenshot -> diagnostics -> uninstall. The tour replaces the nav-walk phase: instead of
  walking *our own* sidebar, it walks the *target's* UI from a tour script.
* `scripts/just/cua-nsis-test.ps1` / `cua-webapp-test.ps1` wrappers: same pattern, new recipe
  (`just cua-tour <tour.yaml>`) when built.
* Fleet rules that carry over unchanged: pywinauto as a real dev dep (no silent false-pass -
  see `mcp-central-docs/standards/rules/cua_nsis_smoke_testing.md` pitfall #1), title-first
  UIA matching with coordinate fallback, OCR keyword scan per step, mouse safety
  (`_release_mouse`, warn-first banner), backend-receipt thinking (every behavioral claim
  needs a captured artifact, not just "the click didn't throw").

Tour script format (v1, YAML): ordered steps of `action` (launch, click, type, hotkey, wait,
screenshot, capture-point) with `expect` (OCR substring or UIA title) and `capture` flags.
No auth/purchase/paywall steps - tour allowlist only; a step requiring credentials aborts
the tour with a named skip, never improvises.

## 4. Capture bundle v1 (file-based handoff)

Each tour run emits one directory: `captures/<target>-<date>/` with `tour.jsonl` (one record
per step: action, timestamp, OCR text, UIA snapshot ref, artifact refs) plus raw artifacts
(screenshots, UI trees, file/registry diffs, HAR/pcap where captured). Formats align with
what REA's runtime guides already consume (browser-observation, Electron-observation,
process-capture, HAR/mitmproxy) so the same bundle feeds `rea_investigate(..., snapshot_path=...)`
without conversion. Bundle sizes stay small by construction: capture-points only, not video.

## 5. Correlation v1: runtime-strings-to-code (the MVP)

One correlation, done well, proves the pipeline:

1. Harvest strings from the capture bundle: OCR text, URLs, filenames, dialog titles, error messages.
2. De-duplicate against baseline (strings present without any interaction) to isolate
   *feature-specific* strings per step.
3. Feed each as a seed: `extract_strings` (is it even in the binary?), then
   `rea_investigate(target, kind='native_search', query=<seed>)` -> refs, then
   `native_function` / `decompile` on the best hits, then ReVa for interactive follow-up.
4. Emit the map row: step -> observed behavior (screenshot ref) -> matching code refs
   (with REA's evidence + limits verbatim) -> verdict (mapped / ambiguous / no static trace).

Later, in order: file-write-to-offset mapping (writes observed at runtime vs entropy/hexdump
regions), UIA-to-IPC mapping for Electron targets (clicked control -> IPC message -> handler),
auto-tour discovery (the v14 discovered-nav idea applied to target apps), version-diff maps
("feature X moved from module A to B in v2").

## 6. Why this repo (and why Delphi/Digibib first)

Digibib5.exe is the ideal first target: Delphi, custom-rendered UI that resists UIA element
discovery (coordinate fallback territory), DKI content behind viewer interactions no static
pass can reach. A CUA tour that opens volumes, pages text, and captures what changes -
correlated against `decode_dki_file` / `digibib_research_snapshot` - is the mission's missing
half. If the pipeline maps one Digibib feature end to end, it generalizes to anything.

## 7. Safety / legal (non-negotiable)

* Targets you are entitled to analyze, same rule as the README. Commercial EULAs may forbid
  both halves - check first.
* The tour *executes* the target with your permissions: isolated machine/VM or filesystem
  snapshot, no credentials, no real identity, filtered or no network. Treat every target as
  potentially hostile until triage says otherwise.
* Cloud-model data policy applies to both halves: screenshots and disassembly alike go to
  the model provider. No proprietary targets without approval.
* Human reviews every map before it leaves the machine. The agent proposes correlations;
  stated limits travel with them, never trimmed.

## 8. Open questions

* Attribution noise: background processes pollute per-step diffs; need a quiet-machine
  protocol or baseline-subtraction before maps are trustworthy.
* Custom-rendered UIs (Delphi, Directmedia, games): OCR-only verification, no UIA names -
  how far does title-matching get us, and where does template-image clicking take over?
* Packed/obfuscated natives: entropy pre-check should route around disassembly dead ends -
  what does the map say when static yields nothing? (Answer: the behavioral half alone,
  honestly labeled.)
* Who owns the tour corpus: per-target YAML in-repo, or a shared fleet tour library?

## 9. References

* This repo: `docs/REA.md` (sidecar + Tier 2 bridge), `docs/REVA.md`, `docs/DIRECTMEDIA_MISSION.md`,
  `scripts/cua-smoke.py`, `scripts/cua-webapp-test.py`
* Fleet: `mcp-central-docs/standards/rules/cua_nsis_smoke_testing.md` (pywinauto stack, false-pass
  pitfalls, mouse safety), `.../rules/cua_webapp_testing.md`
* Upstream REA runtime guides: browser-observation, browser-scenario-contract,
  electron-observation, javascript-runtime-observation, process-capture
  (`github.com/morluto/rea/blob/main/docs/`)
