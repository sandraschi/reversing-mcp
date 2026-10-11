# REA — Reverse Engineer Anything (sidecar)

[REA](https://rea.tools/) (`github.com/morluto/rea`, MIT) is an **agent-native RE bridge**: it exposes
Hopper / Ghidra / IDA plus JS-Electron / .NET / APK / firmware / browser-capture workflows
through an MCP server + matching CLI (`rea-agents` on npm).

**It is a separate server from reversing-mcp.** You run both side-by-side — reversing-mcp for
static triage (strings, entropy, PE, DKI/Digibib), REA when the target is JS/Electron/.NET/APK/
firmware/website, or when you want the agent to drive native disassembly with evidence.

Analyzed 2026-10-11 against REA latest (`npx rea-agents@latest`). REA moves fast — run
`rea update` (npm install) or `npx rea-agents@latest setup` (npx) before trusting this doc.

---

## 1. Architecture overview

```
Your agent (Claude Code / Cursor / Codex / Gemini CLI / ...)
  |-- reversing-mcp (stdio, FastMCP Python)  — strings, entropy, PE, DKI, digibib snapshot
  |-- reva-mcp (HTTP)                        — interactive Ghidra decompile/xrefs/rename (see REVA.md)
  |-- rea-agents (stdio MCP, Node)           — JS/Electron, .NET, APK, firmware, browser, native via provider
```

REA speaks MCP over **stdio** (local server, `node`). The same workflows are also available as
terminal commands (`npx -y rea-agents@latest <command> --json`), so scripting does not need an agent.

Evidence contract: every REA finding ships with the code/refs it came from **plus stated limits/
unknowns**. The agent uses that to ask follow-ups or write + test a re-implementation. See the
[showcases](https://rea.tools/showcase/): DX-Ball sound-pan (3,205 x86 tests, 63 bytes reproduced),
Notion Electron clipboard bridge, TH04 DOS bullet-ring.

---

## 2. When to use which server

| Question | Use |
|----------|-----|
| Strings / hexdump / entropy / PE headers / DKI decode / Digibib5 snapshot | reversing-mcp (`analyze_binary`, `extract_strings`, `analyze_pe_file`, `decode_dki_file`, `digibib_research_snapshot`) |
| Interactive Ghidra decompile, xrefs, rename, type edit | ReVa (see `docs/REVA.md`) |
| "How does feature X work in Electron app Y?" (modules, IPC, routes, preload bridge) | **REA** |
| .NET assembly (metadata, CIL, native deps), no native engine | **REA** |
| APK manifest/classes/methods, on-device adb (logcat, packages, screen) | **REA** |
| Firmware regions/extraction, EVM selectors, ELF layout, crash regs, HAR/mitmproxy captures, website structure | **REA** |
| Native pseudocode/asm/strings/symbols/calls driven by agent | **REA** (provider) *or* reversing-mcp headless *or* ReVa — pick one, don't triple-run |

Rule of thumb: reversing-mcp triages **first** (`check_tools` → `analyze_binary`), then hand off to
ReVa or REA. Never run all three on the same question without a reason.

---

## 3. Prerequisites

* Node.js **22.x (>=22.19), 24.x (>=24.11), or 26+** + npm (`node --version`).
* Native deep analysis needs **one** provider: Hopper, Ghidra, or IDA (existing install).
  Setup can install Hopper with approval. Static JS/.NET inspection needs **no** native engine.
* Target-dependent extras (Linux-heavy): pwntools (ELF/crashes), binwalk/unblob (firmware),
  headless JADX + full JDK (APK), `adb` (devices), Chrome-family browser (websites),
  mitmdump on Linux (native captures), Apktool (resources). See upstream per-guide requirements.
* **Windows (Goliath) status:** JS / .NET / APK / browser paths work. Windows-Ghidra support is
  marked experimental upstream; firmware/binwalk/pwntools paths expect Linux. For large binaries
  raise `REA_GHIDRA_STARTUP_TIMEOUT_MS`. Ghidra 16-bit DOS analysis is supported.

---

## 4. Install / setup

```powershell
node --version  # must be 22.19+/24.11+/26+
npx rea-agents setup
```

1. Choose your agents (Claude Code, Codex, Cursor, Gemini CLI, Grok Build supported; others via
   [manual MCP registration](https://github.com/morluto/rea/blob/main/docs/installation.md#mcp-registry)).
2. Review the proposed config changes (setup backs up existing config).
3. Approve, then **restart the agent**.
4. For regular CLI use: `npm install --global rea-agents` → `rea --help`.

Update often (frequent bug fixes):

```powershell
rea update              # npm install
# then re-run the setup command it prints + restart agent
npx rea-agents@latest setup   # npx flow
```

Check readiness: upstream [readiness guide](https://github.com/morluto/rea/blob/main/docs/installation.md#check-readiness-for-your-task)
diagnoses one agent or one analysis engine at a time.

---

## 5. MCP client config (side-by-side)

Keep reversing-mcp untouched, add REA next to it. Example for Cursor (`~/.cursor/mcp.json`)
and Claude Desktop (`claude_desktop_config.json`) — adapt paths:

```json
{
  "mcpServers": {
    "reversing-mcp": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/reversing-mcp", "run", "python", "-m", "reversing_mcp"]
    },
    "rea": {
      "command": "npx",
      "args": ["-y", "rea-agents@latest", "mcp"]
    }
  }
}
```

If your client needs the exact REA MCP command, run `npx rea-agents setup` first and copy what it
writes — the canonical form lives in upstream
[installation](https://github.com/morluto/rea/blob/main/docs/installation.md) and
[MCP contracts](https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md). Manual-registration
clients use the same command. Verify with your client's tool list: REA tools appear alongside
`analyze_binary`, `extract_strings`, etc.

JS/Electron one-shot without an agent:

```powershell
npx -y rea-agents@latest analyze-javascript-application D:/apps/example --json
```

Native provider selection, snapshots, import/export, and exit statuses: upstream
[CLI and Evidence guide](https://github.com/morluto/rea/blob/main/docs/cli.md).

---

## 5b. In-repo bridge (Tier 2): `rea_investigate`

You don't need the REA MCP registered to use REA through reversing-mcp. The
`rea_investigate` tool shells out to the `rea` CLI (global install preferred,
`npx -y rea-agents@latest` fallback) with an allowlisted kind:

| `kind` | Runs | Needs |
|--------|------|-------|
| `auto` (default) | dirs/`.asar` -> JS graph; files -> native overview | target |
| `javascript` | `analyze-javascript-application` | app dir or `.asar` |
| `native_overview` | `analyze` | binary |
| `native_search` / `native_trace` | `search` / `trace` | binary + `query` |
| `native_function` | `function` | binary + `symbol` |
| `native_decompile` / `native_xrefs` | `decompile` / `xrefs` | binary + `address` |
| `providers` / `capabilities` | inventory, no target | nothing |
| `doctor` | readiness diagnostic | optional `provider` |

```python
rea_investigate("D:/apps/notes")                                            # auto -> javascript
rea_investigate("prog.exe", kind="native_overview", provider="ghidra")      # native via Ghidra
rea_investigate("prog.exe", kind="native_search", query="decrypt")          # no provider = auto-select
rea_investigate(None, kind="providers")                                     # what engines exist here?
```

Behavior to know:

* `check_tools()` reports REA under `tools.rea` (version, path, node version) plus a
  `notes.rea_sidecar` pointer. No `rea`/`npx` on PATH -> tools still work, REA ones
  degrade to "run `just setup-rea`" instead of crashing.
* Native kinds accept `provider` (`hopper`, `ghidra`, `ida`); omit it for auto-select.
  Ranked happy path (fleet stance - cheap and legit first):
  1. **`hopper`** - recommended: commercial but ~$100-range, REA setup auto-installs it,
     first-class support. Caveat: macOS/Linux-native, no Windows build - Goliath needs WSL
     or a second host (unverified; see `mcp-central-docs/integrations/hopper.md`).
  2. **`ghidra`** - free, most knobs, but Windows support is experimental upstream and first
     import on big binaries is slow (raise `timeout_s` + `REA_GHIDRA_STARTUP_TIMEOUT_MS`).
  3. **`ida`** - bring-your-own-license only: IDA Pro + Hex-Rays + `mrexodia/ida-pro-mcp`
     wiring (`REA_IDA_MCP_CONFIG`). Best decompiler, most setup, narrower adapter coverage
     (function dossiers; no whole-binary overview, no mutation/debugging). REA never touches
     activation - keep the license clean.
  Fleet-wide five-way comparison (adds IDA Free + Frida, with decision matrix):
  `mcp-central-docs/integrations/re-tools-comparison.md`.
  `snapshot_path` passes `--snapshot` through for cached repeat queries.
* Outputs over 512 KB are **not parsed** (a real Electron evidence file can be 300+ MB).
  You get `stdout_preview` (20k chars) + `stdout_bytes` + a hint to re-run with
  `snapshot_path` and project a summary view. Exit 0 with warnings still counts as success.
* `timeout_s` defaults to 180s, clamps to 10-900s. Ghidra first-import on big binaries
  wants the high end (`REA_GHIDRA_STARTUP_TIMEOUT_MS` still applies provider-side).
* `just check-rea` = version + providers from the terminal; `just setup-rea` registers
  agents; `just update-rea` refreshes registrations (frequent upstream fixes).

---

## 6. Three-server workflow

Typical session (Digibib/Electron example):

| Step | Server | Action |
|------|--------|--------|
| Triage | reversing-mcp | `check_tools()`, `analyze_binary()`, `get_file_info()` |
| Route | you | PE/Delphi EXE → ReVa+IDR path; Electron unpacked dir/ASAR → REA |
| Electron map | **REA** | modules, imports, source maps, main/preload/renderer + IPC |
| Decompile fn | ReVa | `decompile_function(...)`, `get_xrefs_to(...)` |
| DKI/content | reversing-mcp | `decode_dki_file()`, `digibib_research_snapshot()` |
| Rebuild | agent | write + test implementation from REA/ReVa evidence |

Prompt shape that works (replace target):

```
Understand how search works in the Notes app, show me the evidence, and build a
similar feature for my project.
```

Start small: upstream [first investigation](https://rea.tools/first-investigation/) (Notes app + CSV formatter).

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| REA tools missing after setup | Agent not restarted | Restart agent, re-check tool list |
| Native op asks for provider | No Hopper/Ghidra/IDA found | Install one, or let setup install Hopper; see [provider setup](https://github.com/morluto/rea/blob/main/docs/installation.md#hopper), [IDA guide](https://github.com/morluto/rea/blob/main/docs/ida-provider.md) |
| Ghidra startup timeout on big binary | Default deadline too low | Set `REA_GHIDRA_STARTUP_TIMEOUT_MS` higher |
| `node --version` too old | REA needs 22.19+/24.11+/26+ | Upgrade Node, re-run setup |
| APK/JADX fails | No full JDK or headed JADX missing | Install full JDK + headless JADX per [Android guide](https://github.com/morluto/rea/blob/main/docs/android-analysis.md) |
| Firmware yields nothing on Windows | binwalk/unblob is Linux-only | Run that target on Linux/WSL |
| Bug that smells fixed | Stale install (REA churns) | `rea update` → re-run setup → restart agent → retry, then [open issue](https://github.com/morluto/rea/issues) with version + target type + repro |

---

## 8. Safety / legal

* Analyze **only** targets you are entitled to analyze (same rule as reversing-mcp README).
  REA docs carry the same lawful-RE disclaimer; commercial EULAs may forbid it — check first.
* Static JS/.NET reads files without running them. **Runtime/browser/process capture runs the
  target with your permissions** — treat suspicious binaries like malware: isolate first.
* REA analyzes locally, but the **agent's model provider receives the results** under its own data
  policy. Don't feed proprietary binaries to a cloud model without approval.
* No REA crypto/token affiliation: upstream warns that `REA`-named tokens are scams.

---

## 9. References

* Website/guides/showcases: [rea.tools](https://rea.tools/) · [guides](https://rea.tools/guides/) · [showcase](https://rea.tools/showcase/)
* Repo + install/setup: [github.com/morluto/rea](https://github.com/morluto/rea) · [installation](https://github.com/morluto/rea/blob/main/docs/installation.md)
* Contracts/prompts/CLI: [mcp-contracts](https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md) · [mcp-prompts](https://github.com/morluto/rea/blob/main/docs/mcp-prompts.md) · [cli](https://github.com/morluto/rea/blob/main/docs/cli.md)
* Capability deep-dives: [native](https://rea.tools/guides/native/) · [javascript](https://rea.tools/guides/javascript/) · [browser](https://rea.tools/guides/browser/) · [managed-code](https://github.com/morluto/rea/blob/main/docs/managed-code-analysis.md) · [android](https://github.com/morluto/rea/blob/main/docs/android-analysis.md) · [firmware](https://github.com/morluto/rea/blob/main/docs/firmware-analysis.md) · [EVM](https://github.com/morluto/rea/blob/main/docs/evm-bytecode.md) · [roadmap](https://github.com/morluto/rea/blob/main/docs/roadmap.md)
* Security reports: [SECURITY.md](https://github.com/morluto/rea/blob/main/SECURITY.md)
* This repo: [REVA.md](REVA.md) (interactive Ghidra) · [GHIDRA.md](GHIDRA.md) (headless) · [IDA.md](IDA.md) · [IDR.md](IDR.md)
