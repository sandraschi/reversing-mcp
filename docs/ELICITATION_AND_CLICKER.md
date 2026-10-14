# Elicitation & Clicker Playbook (Gym stages 1b + 3, detailed)

Companion to `docs/GYM_SPEC.md` §§2b–2c. This file is the *how*; the spec holds the
*what* and the gates. Status: G1b elicitation + G3 clicker built (`src/reversing_mcp/clickerlab.py`,
`/clickerlab` page, `gym` ops `elicit`/`clicker_*`/`correlate`, `just cua-tour`);
B3 OCR + coordinate fallback built (Tesseract, fleet path); B4 LLM-guidance layer still open.

---

## Part A — Elicitation (stage 1b): read before you click

Goal: for a new target, produce `formats/*.md` stubs, a help inventory, a feature
list, and a generated tour-YAML draft — all without executing anything.

### A1. Format candidates from triage output

Inputs: `triage/triage.json` (strings, PE imports, DiE compiler line).

1. **Extensions:** collect dotted tokens (`\.[a-zA-Z0-9]{2,4}`) from strings, drop
   `.exe`/`.dll`/version noise (`.00`, `.040`). Each survivor is a format lead.
2. **Magic bytes:** collect 4CC-style constants and `MZ`/`PK`/`RIFF`-adjacent markers;
   cross-check against the extension list (mismatch = custom container, flag it).
3. **Format names:** grep strings for `format`, `codec`, `compress`, `encrypt`, `parser`,
   `import`, `export`, `filter` and read the 80 chars around each hit. Names of formats
   the app claims to handle usually sit within two lines of these verbs.
4. **API surface:** PE imports (`ReadFile`, `CreateFileMapping`, `InternetOpen`,
   `CryptDecrypt`, `Inflate`) tell you *how* it touches data before you know *what*.

### A2. Spec lookup protocol (per candidate format)

Search order, stop at the first that answers "what are the record boundaries?":

1. Vendor documentation (SDKs, file-format SDK notes, developer blogs).
2. Standards track (RFCs, ISO, MS-X/MS-[MSDOCS] pages, OASIS/ECMA).
3. Community specs (file-format wikis, reverse-engineering write-ups, Wireshark
   dissectors, 7-Zip/ffmpeg/libreoffice source support tables).
4. Compatible implementations (open-source readers/converters — their parsers are
   executable specs; note version skew).

Record per format in `formats/<ext>.md`:

```markdown
# <ext> — candidate spec (elicited YYYY-MM-DD, status: lead|confirmed|contradicted)
- Claimed by: <strings offsets / import names>
- Public spec: <url or "none found">
- Record boundaries per spec: <one paragraph>
- App dialect notes: <filled during oracle capture, never before>
- Verdict: <pending oracle>
```

Rule (spec §2b): specs are leads, never truth. When the oracle contradicts the spec,
the app wins and the stub records the dialect. A contradicted stub is still valuable —
it documents exactly where the dialect diverges.

### A3. Help-file mining (the clicker's target list)

Apps document themselves better than any crawler discovers:

1. **Inventory:** `.chm`/`.hlp` beside the EXE, `.pdf` manuals, Help-menu items
   (enumerated live later, but menu *strings* are already in the binary — grep
   `Help`, `About`, `Tip`, `Tutorial`, `Contents`, `Index`, `Search`).
2. **CHM parsing:** CHM is a parseable container (7-Zip extracts it; `chmlib` reads
   the `#SYSTEM`/`#TOPICS` streams). Extract the topic tree → each topic is a feature.
3. **TOC → feature list:** every help topic + every menu string becomes one row in
   `features.json`: `{id, title, source: "help"|"menu"|"strings", file_io: bool,
   priority: 1-3}`. Priority 1 = anything touching files (Open/Save/Export/Import/
   Print-to-file); 2 = dialogs and views; 3 = decoration (skins, toolbars, About).
4. **Tour-YAML generation:** the stage-1b draft maps priority-1 features to tour steps
   mechanically (menu path from the UIA snapshot comes later at stage 3; the draft
   records *intent*, the driver resolves *paths*). Hand-authoring tours is deprecated
   from this point on.

### A4. Prior-art search

REA web kinds + plain web search, one pass per target, time-boxed to an hour:

- Existing specs, SDKs, plugins, converters for the app's formats.
- Teardown write-ups, CTF solutions, forum threads about the file format.
- Compatible apps (anything that already reads the format is an oracle *and* a reference).

A found SDK or parser collapses weeks. Log dead ends too (`prior-art.md`) — the next
target benefits from knowing what does not exist.

---

## Part B — Clicker strategy (stage 3): how it knows where to click

Four layers, cheapest reliable signal first. Each layer has an explicit stop/escalate
condition — the clicker never thrashes.

### B1. Algorithmic base: GUI ripping (always on)

BFS over the live UIA tree, classic GUITAR style (Memon et al.): enumerate windows →
menus → toolbars → dialogs → tabs → controls; record `{AutomationId, Name,
ControlType, patterns}` per node; walk edges (invoke, expand, select, set-value);
model visited state to avoid loops. Coverage metric: % of enumerated nodes visited,
% of menus opened, % of dialogs reached. Deterministic, offline, reproducible —
re-running the same build must produce the same walk (flakes are bugs, file them).

Stop/escalate: a window/dialog whose UIA subtree is empty or a single canvas node
means custom rendering — escalate to B3, do not re-click blindly.

### B2. Docs-seeded ordering (from Part A)

The BFS in B1 is complete but blind; the feature list gives it eyes. Walk priority-1
(file I/O) first so oracle capture (stage 2 needs the same features) and the tour
share evidence. Practically: the driver consumes the stage-1b tour-YAML draft as an
ordered target list and falls back to raw BFS for anything unlisted. New dialogs
discovered mid-walk get appended to the feature list with source `discovered`.

### B3. Screenshot + OCR fallback (custom-rendered UI)

For Delphi/Directmedia-style owners that draw their own widgets:

1. Snapshot per window; diff against the previous snapshot to find *changed regions*
   (a button that highlights on hover tells you where it is for free).
2. OCR each stable region; proposed click targets = text blobs + rectangular contours.
3. Drive by coordinates, verify by screenshot diff (the click "worked" iff pixels
   changed as expected, plus UIA focus events where available).
4. Same coverage metric as B1, counted in regions rather than nodes.

This is the Tier 3 Delphi lesson, promoted into the pipeline. Slower than B1 by an
order of magnitude — only where B1 sees canvas.

### B4. Learned guidance (optional, gated on need)

When the tree is huge (Office-scale menus), an LLM prioritizes branches likely to own
file I/O, and proposes input values for text fields (filenames, search terms) from the
feature context. It never drives directly in v1: it *ranks* targets, the deterministic
driver *executes*. Every LLM-suggested click is logged with its rationale; wrong
suggestions are data (which priors mislead), not failures.

Reading list (pointers — read before building G3, in this order):

| Work | Steal this |
|------|------------|
| GUITAR / Memon et al. (Univ. of Maryland, GUI ripping + testing) | rip-then-walk architecture; coverage model; determinism discipline |
| DroidBot (Li et al. 2017, model-based Android exploration) | pre-LLM state of the art for systematic exploration without models |
| AppAgent (Zhang et al. 2023) | explore-then-deploy split; screenshot+XML fusion; self-exploration memory |
| UFO (Microsoft 2024, Windows UI-automation agent) | Windows-native control interaction; application-aware action selection |
| OmniParser (MSR 2024) | screen → structured elements parsing (for B3 region proposals) |
| OSWorld / WindowsAgentArena | task design + success metrics to benchmark our tours against |
| SeeClick / UGround / OS-Atlas | visual grounding when coordinates are all you have |
| ScreenSpot | element-localization benchmark for tuning B3 |

### Coverage + stop conditions (whole of stage 3)

- Menu coverage: every top-level menu opened, every item invoked or explicitly skipped
  (with reason: destructive, needs license, needs network).
- Dialog coverage: every reachable dialog opened; every tab selected.
- Stability: two consecutive runs agree on the walk (same nodes, same order modulo
  timestamps). Disagreement → investigate, never average.
- Budget: step cap per run (default 500 actions) + wall-clock cap; hitting either is a
  finding about app size, not a failure.

---

## Outputs and their consumers

| Artifact | Produced by | Consumed by |
|----------|-------------|-------------|
| `formats/*.md` | A2 | stage 5 recovery, stage 8 semantic diff |
| `features.json` | A3 | stage 3 ordering, stage 6 UI rebuild scope |
| tour-YAML draft | A3 | stage 3 driver input |
| `prior-art.md` | A4 | stage 5 (what not to re-derive) |
| capture bundle | B1–B4 | stage 2 correlation, stage 6 rebuild, stage 8 compare |

## Why no-disassembly can work (and where it stops)

The ArtCraft case forces the question: how far does public sources + behavior get you
without ever opening a disassembler? Decomposed by knowability:

- **File I/O — public.** PSD is Adobe-published; TIFF/JPEG/PNG open; XLSX/DOCX are
  ECMA-376 + ISO 29500. The biggest chunk of clone value is just reading.
- **Algorithms — prior art.** Krita reimplemented most painting behavior; LibreOffice
  did OOXML; LibRaw did demosaicing. Reading third-party open code is neither
  disassembly nor legally fraught — it is A4 working as designed.
- **Topology + workflows — behavioral.** Dialogs, shortcuts, menus: all observable
  by the clicker. No depth required.
- **Enumeration — the docs themselves.** Help files list what exists.

That stack reaches an 80% clone with correct round-trips — layouts, sliders, layers,
all surface. What it cannot yield: proprietary color science, healing/content-aware
algorithms, resampling edge behavior, GPU tuning, plugin ABI compat, performance
within 10x, bug-compatibility with the original's quirks. The 2,000-issue tracker is
the shape of that residue: vectors, feather parity, codecs, flicker — all depth.

Implication for the Gym: stage 1b is the highest-leverage stage (specs + prior art
first, always); the clicker owns topology, never algorithms; stage 5 exists exactly
for the residue public sources cannot reach. When a target's depth lives in
proprietary algorithms with no prior art, say so in the assessment (Logic: red) —
that honesty is the feature.

## Ghidra or no Ghidra: the evidentiary gradient (legal posture)

Whether a disassembler was ever opened is not just a technical choice — it is evidence:

- **No-disassembly (ArtCraft posture):** checkable clean-room claim. Commit history,
  tooling, and contributor attestations can show no decompiled code ever entered the
  repo. Strongest defense against misappropriation claims; trade-dress remains the
  exposure (Tetris test).
- **Disassembly for interoperability (our posture):** lawful in the EU (Software
  Directive art. 6; Austria UrhG section 40e) and defensible in the US under
  Sega v. Accolade interoperability reasoning — but it is a *defense to raise*, not
  a claim that needs no defense. Decompiler artifacts in history are discoverable,
  so stage-5 output must be specs, never pasted code, and the pipeline must enforce it.
- **Exposure gradient:** private hobby use + friends (no distribution) = no plaintiff,
  no damages, no case. Public rocket + hundreds of contributors = every commit is
  discoverable and every gap-fill is attributable. The Gym's isolation, logging, and
  specs-only rules exist for the second world, not the first.

## The contributor funnel (why popularity compounds depth)

A high-profile clone does not just get bug reports — it recruits the exact people who
can fix them. Feathering parity stalls an AI and a clicker; a domain expert who knows
the algorithm closes it in a weekend. The issue tracker is a hiring funnel for depth.
Design consequence for stage 8: every failed oracle compare emits an **expert-ready
gap report** (failing input, both outputs, traces, format stub section) that a domain
expert can pick up with zero project context. Make depth contributions easy and the
funnel works for us too.

## Open (carried from GYM_SPEC §10, unchanged)

Clone `--gym-roundtrip` hook design, test-file privacy consent, VM image strategy.
Plus: CHM parser choice (7-Zip CLI vs chmlib — decide at G1b build time).
