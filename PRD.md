# PRD: reversing-mcp - the Reversing Gym (clone arbitrary apps)

**Status:** living doc · **Owner:** sandraschi · **Updated:** 2026-10-12

## 1. Problem

Reverse-engineering knowledge is locked behind disassembler expertise (IDA/Ghidra proficiency),
while behavioral tools (CUA click-through) can show *what* an app does but never *which code*
does it. Cloning a closed app for interoperability means bridging that gap by hand, per app,
with no verdict except a human's judgment.

## 2. Product

**The Reversing Gym** (`docs/GYM_SPEC.md`): hand in a Windows app and a few of its data
files; a staged pipeline produces a compatibility assessment, a behavioral UI map, a rebuilt
UI, and a clone tested against the original. The original app is the **oracle** — the clone
is correct when the original agrees with it. CUA clicker bot copies UI/UX; Ghidra/IDA/REA go
deep only where the tour cannot explain what it sees.

Substrate (all shipped): Tier 1 static triage, Tier 2 REA bridge, Tier 3 static correlation,
DiE/capa/Frida engine wrappers, single FastAPI backend, standard chat + Inbox/Skills webapp.

- **Tier 1 (shipped):** static triage in-repo - strings, entropy, hexdump, PE, DKI/Digibib.
- **Tier 2 (shipped 2026-10-11):** REA sidecar bridge (`rea_investigate`) - JS/Electron, .NET,
  APK, firmware, browser, agent-driven native via Ghidra/IDA (Hopper: macOS/Linux hosts only,
  verified unsupported on win32). Tested (9 hermetic tests).
- **Tier 3 (static half shipped 2026-10-11):** `scripts/tour/correlate.py` + first Digibib5 map
  (171 hits). Live CUA tour runner is Phase 2 (Gym stage 3).
- **Gym G1 (this build):** page + job runner + stages 0/1/4 — "should I even try to clone this?"
  in minutes: intake, DiE/capa/PE triage, assessment score, user go/no-go.

## 3. Users

- **Sandra (primary):** Digibib5/DKI format recovery; wrappee inspection for the fleet.
- **Security researchers:** fast triage of unknown binaries with evidence trails.
- **Interop/devs/modders:** "see feature in app X, rebuild it" with code refs, not guesses.

## 4. Requirements

### Functional (by tier)

| ID | Requirement | Tier | Status |
|----|-------------|------|--------|
| F1 | Static triage tools (binary, strings, hexdump, entropy, PE, DKI) | 1 | Done |
| F2 | `check_tools` reports all engines incl. REA (soft-degrade, never crash) | 1-2 | Done |
| F3 | `rea_investigate` allowlisted kinds, auto-routing, 512 KB parse cap + snapshot hint | 2 | Done, 9 tests |
| F4 | `just setup-rea/check-rea/update-rea` sidecar lifecycle | 2 | Done |
| F5 | Provider ranking Hopper > Ghidra > IDA-BYO (license hygiene) | 2 | Done (docs) |
| F6 | Tour runner reusing fleet CUA harness (tour YAML, capture bundle v1) | 3 | Spec (Gym stage 3) |
| F7 | Correlation v1: runtime-strings-to-code -> feature-to-code map | 3 | Static half done (`correlate.py` + Digibib5 map) |
| F8 | CUA/Frida captures feed REA process-capture inputs without conversion | 3 | Spec |
| G1 | Gym intake + triage + assessment (stages 0/1/4): job runner, REST, MCP tool, /gym page | Gym | This build |
| G2 | Gym oracle capture (stage 2): Frida file-API trace + outputs + screenshots in VM | Gym | Spec (needs Frida tools installed + VM plumbing) |
| G3 | Gym clicker tour (stage 3): live pywinauto driver behind gates | Gym | Spec |
| G4 | Gym UI build + round trip + compare (stages 6-8) | Gym | Spec |

### Non-functional

- NF1: No bundled disassembler, no license touching (REA adapter model).
- NF2: Large outputs truncate, never OOM the agent (512 KB parse cap pattern).
- NF3: Lawful targets only; tours execute targets - isolation mandatory.
- NF4: Ruff clean, hermetic tests (declared monkeypatch doubles, no live engines in CI).

## 5. Non-goals

- No interactive disassembler UI (ReVa/Ghidra/IDA GUIs stay external).
- No auto-exploit, no credential-touching tours (allowlist only, named skips).
- No second source of truth: fleet catalog pages point here, not copies.

## 6. Success criteria

- S1: One end-to-end Digibib5 feature map (behavioral tour -> code refs) reviewed by human.
- S2: Hopper closed (unsupported on win32, verified 2026-10-11); Ghidra 12.1 upgrade unlocks REA-ghidra.
- S3: Gym G1 answers "should I clone this?" for Digibib5 with a green/amber/red assessment.
- S4: Gym oracle verdict: the original cannot tell the clone's output from its own (stage 8).

## 7. Roadmap

1. Gym G1 (this build) → G2 oracle capture → G3 clicker tour → G4 UI build → G5 round trip + compare.
2. Field-test Tier 2 (big-binary Ghidra timeouts, JS evidence snapshots, Ghidra 12.1 upgrade).
3. UIA-to-IPC + file-write-to-offset correlations; version-diff maps.
4. Webapp: "Ask about this app" surface over `rea_investigate` + map viewer.

## 8. References

- `docs/GYM_SPEC.md` (the product), `docs/REA.md` (sidecar), `docs/CUA_DISASSEMBLY_COMBO.md` (Tier 3 spec), `docs/REVA.md`
- Fleet: `mcp-central-docs/integrations/{hopper,frida,cua-re-tour,re-tools-comparison}.md`
- Fleet project page: `mcp-central-docs/projects/reversing-mcp/README.md`
