# Reversing Gym (spec)

**Status: spec, not built.** Written 2026-10-12. Build order in section 9.

A webapp page where you hand in a Windows app and a few of its data files, and a staged
pipeline produces: a compatibility assessment, a behavioral map of the UI, a rebuilt UI,
and a clone that is tested against the original. The original app is the **oracle**: the
clone is correct when the original agrees with it, not when the disassembly says so.

Builds on Tier 3 ([CUA_DISASSEMBLY_COMBO.md](CUA_DISASSEMBLY_COMBO.md)): its tour YAML,
capture bundle and `scripts/tour/correlate.py` are reused, not reinvented.

---

## 1. Decisions (2026-10-12)

| Question | Decision | Revisit when |
|----------|----------|--------------|
| What is the oracle? | The **original app**, run on the test files. Its outputs are ground truth. | - |
| Where does the clicker run? | **Isolated**: Hyper-V VM / sandbox via virtualization-mcp, snapshot before each run, no network, no credentials. Never the user's desktop. | A target cannot run in a VM (dongle, GPU) - then an explicit, logged opt-out per run. |
| UI rebuild stack | **Tauri v2 + React** (fleet stack: `WEBAPP_SOTA_STANDARDS.md`, NSIS pipeline). | Pixel-faithful Win32 look matters more than build speed - then evaluate Slint. |
| Fully automatic? | **No.** Gates between stages; the user approves at stage 4 (assessment) and before stage 6 (build). | - |

## 2. Stages

| # | Stage | Input | Output (in the run directory) | Tools | Gate |
|---|-------|-------|-------------------------------|-------|------|
| 0 | **Intake** | path to `.exe` or `.lnk`, 1+ test files, notes | `run.json` (target, hashes, test file list) | - | target must be a local file you are entitled to analyze |
| 1 | **Triage** | target | `triage.json`: compiler/packer (DiE), capabilities (capa), PE sections/imports, entropy, strings, file formats referenced | DiE, capa, built-in static | packed/protected -> warn, continue only on confirm |
| 2 | **Oracle capture** | target + test files, VM | per test file: what the original read and wrote (Frida file-API trace), saved/exported outputs, screenshots | Frida, CUA, VM | - |
| 3 | **Clicker tour** | target, VM | Tier 3 capture bundle: screens, UIA trees, menu tree, dialogs, flows | CUA (pywinauto), tour YAML | - |
| 4 | **Assessment** | 1-3 | `assessment.md` + score (section 5) | - | **user go / no-go** |
| 5 | **Recovery** (only where needed) | formats/logic the clone needs that 2-3 did not explain | format spec (`formats/*.md`), feature-to-code map | Ghidra, IDR, IDA (if licensed), REA, `correlate.py` | specs only - no copied code (section 7) |
| 6 | **UI build** | 3 + 5 | Tauri app skeleton reproducing screens, menus, dialogs | Tauri, LLM codegen | **user approves before build** |
| 7 | **Round trip** | clone + test files | clone opens, reads, writes back each test file | clone CLI hook | - |
| 8 | **Compare** | 2 + 7 | `compare.md`: per test file, byte diff + semantic diff + oracle re-open verdict | VM, CUA, Frida | - |

## 3. Compare = three levels

1. **Byte diff** of clone output vs oracle output for the same operation. Expected to differ
   in timestamps/padding, so it is reported, not used as the verdict.
2. **Semantic diff**: both outputs parsed with the recovered format spec (stage 5) and
   compared field by field.
3. **Oracle re-open** (the verdict): the *original* opens the file the clone wrote, the
   clicker captures what it shows, and that is compared with what it showed for its own
   output. Pass = the original cannot tell the difference.

## 4. Job model

* Backend job runner, one run = one directory `gym/runs/<run-id>/` (gitignored):
  `run.json` (state machine: stage, status, timestamps, errors), one subdirectory per stage,
  `log.jsonl`.
* Stages are idempotent and resumable: a crashed or stopped run restarts at the failed stage.
* Long stages run in a worker (not on the event loop - see the 2026-10-12 `/ghidra/status`
  incident); the API only reads/writes run state.
* Planned endpoints (none exist yet): `POST /api/v1/gym/runs`, `GET /api/v1/gym/runs`,
  `GET /api/v1/gym/runs/{id}`, `POST /api/v1/gym/runs/{id}/advance` (gate approval),
  `POST /api/v1/gym/runs/{id}/stop`, `GET /api/v1/gym/runs/{id}/artifacts/{path}`.
* MCP surface: one portmanteau tool `gym(operation=start|status|advance|stop|list)` so
  agents can drive runs too.

## 5. Assessment score

Reported per dimension, not as one fake-precise number:

| Dimension | Green | Amber | Red |
|-----------|-------|-------|-----|
| Binary | unpacked, known compiler | packed by known packer | protected / anti-debug |
| UI coverage | tour reached every menu item and dialog | most | custom-rendered, OCR only |
| Format | test-file I/O fully seen in Frida trace, structure clear | partial | encrypted / opaque |
| Logic | outputs explainable from inputs | needs stage 5 | needs deep RE, high effort |
| Oracle | original runs in VM, scriptable | needs workarounds | does not run isolated |

## 6. The page

`/gym` in the sidebar. Intake form (target path, test files, notes), run list, and per run:
a horizontal stage stepper (0-8) with status, the gate button where a stage waits for the
user, and an artifact browser per stage (screenshots, JSON, reports). Polling, not
websockets, for v1.

## 7. Legal / safety

* Only targets you are entitled to analyze. EU Software Directive art. 6 (Austria: UrhG
  section 40e) permits decompilation where needed for interoperability; it does not permit
  copying the program. The clone implements **specs written in stage 5**, never decompiled
  code or the original's assets (icons, images, texts beyond what interoperability needs).
* Stages 2, 3 and 8 execute the target: VM only, snapshot before, no network, no credentials
  (Tier 3 section 7 rules apply in full).
* Screenshots, traces and disassembly go to the model provider when an LLM reads them - same
  data-policy rule as Tier 3.

## 8. Calibration target

**Digibib5** first: the DKI decoder and a first feature-to-code map already exist
(`directmedia_dki.py`, `maps/digibib5-search-v1.md`), so stages 5, 7 and 8 have a known
right answer to check the pipeline against.

## 9. Build order

| Phase | Delivers | Needs |
|-------|----------|-------|
| G1 | Page + job runner + stages 0, 1, 4 (triage-only assessment) | DiE, capa wrappers (done with phase 3 engines) |
| G2 | Stage 2 oracle capture | Frida wrapper, VM plumbing via virtualization-mcp |
| G3 | Stage 3 clicker tour | Tier 3 live tour runner (pywinauto driver) |
| G4 | Stage 6 UI build | Tauri template + codegen from capture bundle |
| G5 | Stages 7-8 round trip + compare | clone CLI hook, recovered format spec |

G1 is useful on its own: "should I even try to clone this?" in a few minutes.

## 10. Open questions

* Clone CLI hook: how does the gym tell the clone "open X, save as Y" without the clicker?
  Proposal: every generated clone ships a `--gym-roundtrip <in> <out>` flag.
* Test-file privacy: user documents go into VMs and possibly to a model provider - per-run
  consent checkbox?
* VM image: one golden Windows image per target bitness, or per target?
* ArtCraft-style UX-analysis bot: collect how they structure the UI map, align stage 3 output.
