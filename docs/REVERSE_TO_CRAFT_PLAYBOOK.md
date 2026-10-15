# Reverse-to-Craft Playbook: Rebuilding Closed Apps into Agent-Native Rust Crafts

**Status:** Living Standard & Architectural Playbook  
**Date:** 2026-10-15  
**Originating Repos:** `reversing-mcp` (Gym & ClickerLab) + `mcp-central-docs` (`adobe-offensive` / `UPSTREAM_CRAFT_DOCTRINE.md`)  
**Parent Specs:** [`docs/GYM_SPEC.md`](GYM_SPEC.md), [`docs/CUA_DISASSEMBLY_COMBO.md`](CUA_DISASSEMBLY_COMBO.md), [`docs/ELICITATION_AND_CLICKER.md`](ELICITATION_AND_CLICKER.md)

---

## 1. Executive Summary & The Core Thesis

Classical reverse engineering terminates at understanding: producing a Ghidra project, a writeup, or a single-format extractor script. 

The **Reverse-to-Craft Playbook** expands this horizon into complete, clean-room product reconstruction:
1. **The Reversing Gym (`reversing-mcp`)** acts as the automated **extractor and behavioral oracle**. It systematically inspects, drives, and traces a proprietary legacy Windows application (e.g. Digibib5, classic Outlook, AutoCAD, or Win32 utilities) using both white-box disassemblers and black-box Computer Use Agent (CUA) tours.
2. **The ArtCraft Playbook (`_upstream/<craft>`)** acts as the modern **reconstruction blueprint**. Using the canonical, pure-Rust desktop pattern pioneered by the ArtCraft/FigCraft family, the recovered specification is implemented as a single-workspace Rust application with instant CLI parity, native GUI controls, and an embedded Model Context Protocol (MCP) server.
3. **The Fleet Launcher (`fleet-start.config.ps1`)** provides centralized operational readiness: lifecycle management, assigned ports, and autonomous agent access across the entire fleet from day one.

---

## 2. End-to-End Architectural Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: GYM EXTRACTION & ORACLE CAPTURE (reversing-mcp)               │
│                                                                        │
│   Target Legacy App (Isolated VM or Local Sandbox)                     │
│     │                                                                  │
│     ├─ Stage 1 / 1b: Triage & Elicitation (DiE, capa, string mining)   │
│     ├─ Stage 2: Frida API Tracing (file handles, memory, registry)    │
│     ├─ Stage 3: CUA Clicker Tour (pywinauto, OCR, UIA tree)            │
│     └─ Correlate: Feature-to-Code Synthesis (correlate_session)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                        Emits Clean-Room Specs:
                        - Data & File Format Specs (spec/format_v1.md)
                        - Action & State Machine Tree (features.json)
                        - UI Layout & Visual Tokens (tour-draft.yaml)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: ARTCRAFT SCAFFOLDING & MODULE HARVESTING                      │
│                                                                        │
│   Single Rust Workspace (FigCraft / CadCraft Reference Layout)        │
│     ├─ apps/<name>-cli       : clap CLI + built-in `rmcp` server       │
│     ├─ apps/<name>-desktop   : egui / Tauri v2 desktop shell           │
│     ├─ crates/core           : State machine & domain document model   │
│     ├─ crates/format         : Spec-compliant binary parser/encoder    │
│     ├─ crates/mcp            : First-class agent tool definitions      │
│     └─ crates/ui-egui        : Menus, command palette, canvas          │
│                                                                        │
│   Harvested Modules from D:\Dev\repos\_upstream\<craft>\ (MIT/Apache):  │
│     • MCP Envelope & Tools   <-- figcraft/crates/mcp                  │
│     • Canvas / Viewport      <-- cadcraft / photocraft                 │
│     • Command Palette / IA   <-- figcraft/crates/ui-egui              │
│     • Search & FTS5 Index    <-- lookcraft-core / rusqlite             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: ORACLE VERIFICATION & FLEET DEPLOYMENT                        │
│                                                                        │
│   The Three-Level Oracle Test (Gym Stage 8)                            │
│     Level 1: Byte-level output differential                            │
│     Level 2: Semantic schema & field verification                     │
│     Level 3: Oracle Re-Open (Original legacy app opens clone's files) │
│                                                                        │
│   Central Fleet Launcher Integration                                   │
│     • fleet-start.config.ps1 + starts/<name>-start.bat                 │
│     • Dual-transport: Standalone GUI + MCP server for AI agents        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Phase Breakdown

### Phase 1: Automated Reverse Engineering via the Gym

The legacy app is deployed to a clean test harness. `reversing-mcp` executes Gym stages 0 through 4:

1. **Intake & Triage (Stages 0 & 1)**:
   - Identify compiler, packer, and architecture via Detect It Easy (`engine(operation="die")`) and capability heuristics (`engine(operation="capa")`).
   - Extract string catalogs and calculate block Shannon entropy to isolate packed/encrypted regions.
2. **Feature Elicitation (Stage 1b)**:
   - Mine UI strings and format indicators via `clickerlab.elicit_run`.
   - Automatically draft the initial user tour (`tour-draft.yaml`) and prioritize candidate file formats.
3. **Oracle Capture (Stage 2)**:
   - Instrument file I/O and process memory using Frida runtime hooks (`engine(operation="frida_trace")`).
   - Log exact buffer offsets, file read/write calls, and API parameters during target execution.
4. **Behavioral CUA Tour (Stage 3)**:
   - `clickerlab` executes scripted accessibility tours via `pywinauto`.
   - Captures timestamped window states, OCR text, and accessibility elements (`File -> Open`, dialog popups, search queries).
5. **Feature-to-Code Correlation**:
   - `correlate_session` bridges the black-box UI evidence with white-box disassembly (PyGhidra / ReVa).
   - Translates human-visible UI triggers directly into function addresses, generating **Ghidra plate comments** and **IDA import scripts** (`map_import_ida.py`).

---

### Phase 2: Clean-Room Specification (Gym Stage 5)

Under international reverse-engineering case law and EU Software Directive art. 6 (Austria: UrhG §40e), interoperability allows decompilation to extract interfaces and formats, but strictly prohibits copying original assembly code, graphics, or assets into the new product.

Stage 5 formalizes the clean-room boundary:
* **Binary Format Specification**: Emits a deterministic spec covering magic headers, offset tables, compression algorithms (zlib/LZW/gzip), endianness, and padding.
* **Semantic Document Schema**: Defines the target's data model as typed structs (e.g. JSON schema / Rust structs).
* **UI/UX Interaction Tree**: Details the command hierarchy, shortcuts, and navigation graph without copying copyrighted trade-dress bitmaps.

---

### Phase 3: Scaffolding the Craft App (The FigCraft / CadCraft Standard)

The new application is scaffolded as a pure-Rust workspace following the **Upstream Craft Doctrine** (`UPSTREAM_CRAFT_DOCTRINE.md`):

```
<craft-app>/
├── Cargo.toml
├── apps/
│   ├── <name>-cli/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── main.rs         # clap CLI parsing; delegates to core or mcp
│   │       └── commands/       # CLI verb implementations
│   └── <name>-desktop/
│       ├── Cargo.toml
│       └── src/
│           ├── main.rs         # Desktop GUI main entry
│           └── app.rs          # egui / Tauri v2 application state
├── crates/
│   ├── core/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs          # Unified domain model
│   │       ├── commands.rs     # Canonical Command IDs (used across CLI/UI/MCP)
│   │       └── state.rs        # Undo/redo, session history, document state
│   ├── format/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs          # Parser / encoder implementing Stage 5 spec
│   │       ├── reader.rs       # Zero-copy binary parser (nom / binread)
│   │       └── writer.rs       # Clean format serializer
│   ├── mcp/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs          # rmcp server definition
│   │       └── tools.rs        # Tool definitions exposing core commands
│   └── ui-egui/
│       ├── Cargo.toml
│       └── src/
│           ├── canvas.rs       # Main viewport / canvas rendering
│           ├── palette.rs      # Command palette (fuzzy search over commands)
│           └── menu.rs         # Native top-level menus
└── corpus/
    ├── fixtures/               # Test files from original target
    └── tests/roundtrip.rs      # Round-trip parse/encode regression test
```

#### The Unified Command ID Pattern
Every user action is assigned a canonical string ID in `crates/core/src/commands.rs`:
```rust
pub const CMD_FILE_OPEN: &str = "file.open";
pub const CMD_FILE_EXPORT: &str = "file.export";
pub const CMD_SEARCH_EXECUTE: &str = "search.execute";
```
- **In GUI**: Triggered by menu item click, shortcut key, or command palette selection.
- **In CLI**: Triggered by `<name>-cli export --format ...`.
- **In MCP**: Triggered by an AI agent calling the `execute_command` or dedicated MCP tool.

---

### Phase 4: Harvesting Upstream Craft Modules (The Basilica Rule)

Because all 12 Craft apps in `D:\Dev\repos\_upstream\` (`figcraft`, `cadcraft`, `photocraft`, `wordcraft`, etc.) are licensed under **MIT OR Apache-2.0**, proven production modules are harvested directly rather than reinvented:

```
From D:\Dev\repos\_upstream\figcraft\crates\mcp\
  ↳ Direct copy of rmcp server harness, tool registration, and stdio/SSE adapters.

From D:\Dev\repos\_upstream\figcraft\crates\ui-egui\
  ↳ Command palette modal, keyboard shortcut registry, and status bar.

From D:\Dev\repos\_upstream\cadcraft\
  ↳ Pan-and-zoom viewport, geometric canvas, and transform matrices.

From D:\Dev\repos\_upstream\wordcraft\
  ↳ Document layout, text flow, pagination, and printing pipeline.
```

**Attribution Hygiene**:
Every borrowed file preserves upstream copyright notices and includes a one-line provenance header:
```rust
// Harvested from storytold/figcraft@bcedfeb on 2026-10-15 per UPSTREAM_CRAFT_DOCTRINE.md.
// Licensed under MIT OR Apache-2.0.
```

---

### Phase 5: The Three-Level Oracle Test (Gym Stage 8)

The rebuild is verified by turning the original legacy application into a test oracle:

1. **Level 1 — Deterministic Byte Differential**:
   - For operations producing static headers or known byte streams (e.g. decompression), verify output equality.
2. **Level 2 — Semantic Schema Differential**:
   - Both the original app and the Craft clone process identical test data.
   - The resulting intermediate structures are parsed with the format spec and checked field-by-field.
3. **Level 3 — Oracle Re-Open (The Final Verdict)**:
   - The Craft clone exports a project/archive file.
   - The legacy application is launched in the Gym harness (via Frida/pywinauto).
   - The original app is instructed to open the newly generated file.
   - **Verdict: If the legacy application opens, displays, and edits the Craft clone's file without error or warnings, interoperability is proven 100%.**

---

### Phase 6: Central Fleet Launcher Integration

To ensure the newly created Craft application runs seamlessly alongside all existing fleet servers, it integrates with the central launcher:

1. **Port Registration**: Claim an unassigned port pair in `mcp-central-docs/operations/WEBAPP_PORTS.md`.
2. **`fleet-start.config.ps1`**:
   ```powershell
   @{
       Name = "<app-name>"
       DisplayName = "<App Name> (Agentic Craft)"
       Kind = "native"
       Backend = @{
           Command = "cargo"
           Args = @("run", "--bin", "<name>-cli", "--", "mcp")
           Port = 10xxx
           HealthCheck = "http://127.0.0.1:10xxx/health"
       }
       Frontend = @{
           Command = "cargo"
           Args = @("run", "--bin", "<name>-desktop")
           Port = 10xxy
       }
   }
   ```
3. **Launcher Script (`starts/<name>-start.bat`)**:
   - Standard non-elevated fleet start wrapper delegating to `Invoke-FleetWebappStart.ps1`.
   - Provides immediate desktop launch and registers the MCP endpoint in Claude Desktop and Antigravity IDE.

---

## 4. Checklist: Taking a Binary from Raw Machine Code to Fleet Craft

| Step | Action | Tooling / Recipe | Output |
|---|---|---|---|
| **1** | Binary Intake & Triage | `gym(operation="start")`, DiE, capa | `triage.json` (compiler, architecture, packer) |
| **2** | Feature Elicitation | `clickerlab.elicit_run` | `features.json`, `tour-draft.yaml`, format stubs |
| **3** | Dynamic API Trace | `engine(operation="frida_trace")` | `trace.jsonl` (file writes, heap buffers, syscalls) |
| **4** | CUA Feature Walk | `clickerlab.clicker_start` | `tour.jsonl`, screenshots, OCR string inventory |
| **5** | Feature-to-Code Mapping | `clickerlab.correlate_session` | `map.md`, Ghidra plate comments, `map_import_ida.py` |
| **6** | Clean-Room Format Spec | Human / Agent Spec Extraction | `docs/spec/format_v1.md` (zero original source code) |
| **7** | Scaffold Rust Workspace | `cargo new --workspace <name>` | FigCraft reference layout (`apps/`, `crates/`) |
| **8** | Harvest Upstream Modules | Copy from `_upstream/<craft>` | Core UI, command palette, `rmcp` server harness |
| **9** | Implement Format Codec | Implement `crates/format` in Rust | Pure Rust zero-copy parser and encoder |
| **10** | Level 3 Oracle Verification | Gym Stage 8 Oracle Re-open | Legacy app opens clone's files without warning |
| **11** | Fleet Launcher Wireup | `fleet-start.config.ps1` | `starts/<name>-start.bat` verified green |
