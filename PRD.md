# PRD: reversing-mcp - agent-driven feature-to-code-map platform

**Status:** living doc · **Owner:** sandraschi · **Updated:** 2026-10-11

## 1. Problem

Reverse-engineering knowledge is locked behind disassembler expertise (IDA/Ghidra proficiency),
while behavioral tools (CUA click-through) can show *what* an app does but never *which code*
does it. Format recovery (the Digibib5/DKI mission), interop work, and security triage all
stall in the gap between the two.

## 2. Product

One MCP server that triages, delegates, and correlates - so an agent can answer
"how does feature X work in closed app Y, show me the evidence" with zero disassembler skill
required from the operator:

- **Tier 1 (shipped):** static triage in-repo - strings, entropy, hexdump, PE, DKI/Digibib.
- **Tier 2 (shipped 2026-10-11):** REA sidecar bridge (`rea_investigate`) - JS/Electron, .NET,
  APK, firmware, browser, agent-driven native via Hopper/Ghidra/IDA. Tested (9 hermetic tests).
- **Tier 3 (spec):** CUA feature tour correlated to disassembly - `docs/CUA_DISASSEMBLY_COMBO.md`.
  Output: feature-to-code maps. MVP: runtime-strings-to-code on Digibib5.exe.

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
| F6 | Tour runner reusing fleet CUA harness (tour YAML, capture bundle v1) | 3 | Spec |
| F7 | Correlation v1: runtime-strings-to-code -> feature-to-code map | 3 | Spec |
| F8 | CUA/Frida captures feed REA process-capture inputs without conversion | 3 | Spec |

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
- S2: Hopper path verified from this fleet (WSL/2nd host TO-VERIFY closed).
- S3: Tier 3 MVP runs `tour -> capture -> correlate -> map` unattended on a sample target.

## 7. Roadmap

1. Field-test Tier 2 (Hopper verify, big-binary Ghidra timeouts, JS evidence snapshots).
2. Build Tier 3 MVP (F6+F7) against Digibib5.exe.
3. UIA-to-IPC + file-write-to-offset correlations; version-diff maps.
4. Webapp: "Ask about this app" surface over `rea_investigate` + map viewer.

## 8. References

- `docs/REA.md` (sidecar), `docs/CUA_DISASSEMBLY_COMBO.md` (Tier 3 spec), `docs/REVA.md`
- Fleet: `mcp-central-docs/integrations/{hopper,frida,cua-re-tour,re-tools-comparison}.md`
- Fleet project page: `mcp-central-docs/projects/reversing-mcp/README.md`
