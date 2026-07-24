# Ghidra Integration Guide

Ghidra is the National Security Agency's free and open-source reverse engineering framework ([Apache 2.0](https://ghidra-sre.org/)). This guide covers both ways to use Ghidra with reversing-mcp.

---

## Contents

1. [Quick comparison: two paths](#1-quick-comparison-two-paths)
2. [Path A — Interactive Ghidra via ReVa MCP](#2-path-a--interactive-ghidra-through-reva-mcp)
3. [Path B — Headless analyzeHeadless](#3-path-b--headless-analyzeheadless)
4. [ReVa reference: assistant vs headless mode](#4-reva-reference-assistant-vs-headless-mode)
5. [Ghidra scripts in this repo](#5-ghidra-scripts-in-this-repo)
6. [analyzeHeadless CLI reference](#6-analyzeheadless-cli-reference)
7. [Troubleshooting](#7-troubleshooting)
8. [References](#8-references)

---

## 1. Quick comparison: two paths

| Aspect | Path A (ReVa MCP) | Path B (Headless) |
|--------|-------------------|-------------------|
| Interaction | Real-time — decompile, xrefs, rename | Batch only — script runs, exits |
| Ghidra GUI needed | Yes (assistant mode) or no (headless mode) | No |
| MCP tools | Full ReVa surface (30+ tools) | `analyze_binary(..., ['ghidra'])` |
| Setup complexity | Medium (Ghidra + extension + MCP config) | Low (Ghidra install + env var) |
| Best for | Active RE sessions, exploring unknowns | CI, bulk analysis, headless servers |

**You can use both.** Run ReVa for deep interactive work; use `analyze_binary` with `['ghidra']` for quick headless passes.

---

## 2. Path A — Interactive Ghidra through ReVa MCP

**[ReVa](https://github.com/cyberkaida/reverse-engineering-assistant)** (reverse-engineering-assistant) exposes Ghidra's analysis engine as an MCP server. It is a **separate install** — not bundled in reversing-mcp.

### 2.1 Install Ghidra

1. Download the latest release from [ghidra-sre.org](https://ghidra-sre.org/) or [GitHub releases](https://github.com/NationalSecurityAgency/ghidra/releases)
2. Extract to a stable path (e.g. `C:\ghidra_12.0_PUBLIC`)
3. Set environment variable `GHIDRA_INSTALL_DIR` to that path (used by both ReVa and headless scripts)

### 2.2 Install ReVa

```
pip install reverse-engineering-assistant
```

Or clone from [github.com/cyberkaida/reverse-engineering-assistant](https://github.com/cyberkaida/reverse-engineering-assistant) and follow upstream README.

### 2.3 Choose ReVa mode

#### Assistant mode (Ghidra GUI + ReVa extension)

1. Install the ReVa Ghidra extension (download from GitHub releases for your Ghidra version)
2. In Ghidra: `File → Install Extensions`, select the ReVa `.zip`, restart Ghidra
3. Enable plugins: `File → Configure → Tool`, check **ReVa Application Plugin** and **ReVa Plugin**
4. Start Ghidra, open a project and a binary
5. Enable the HTTP MCP listener: `Edit → Tool Options → ReVa`, enable `server.enabled` (default port `8080`)

**Cursor MCP config:**
```json
{
  "reva-assistant": {
    "type": "http",
    "url": "http://127.0.0.1:8080/mcp/message"
  }
}
```

**Claude Desktop config:**
```json
{
  "mcpServers": {
    "reva-assistant": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp/message"
    }
  }
}
```

#### Headless mode (ReVa standalone, Ghidra 12.0+)

ReVa's `mcp-reva` tool runs Ghidra headless and exposes the same MCP surface without the GUI:

```
set GHIDRA_INSTALL_DIR=C:\ghidra_12.0_PUBLIC
mcp-reva
```

Configure your MCP client to point at the ReVa HTTP endpoint (default port varies — check ReVa docs).

### 2.4 Verify ReVa is working

```powershell
# Check port is listening (Ghidra must be running in assistant mode)
Test-NetConnection -ComputerName 127.0.0.1 -Port 8080
# Should show TcpTestSucceeded: True
```

Once connected, your MCP client will show ReVa's tools (30+): `decompile_function`, `list_functions`, `get_xrefs`, `rename_function`, `search_strings`, etc. Names differ from the old `ghidra_*` wrappers — discover them via your host's tool list.

---

## 3. Path B — Headless analyzeHeadless

`analyze_binary(file_path, tools=['ghidra'])` uses Ghidra's `analyzeHeadless.bat` to run batch analysis without opening the GUI.

### 3.1 Prerequisites

1. Ghidra installed (any version 10.x+)
2. `GHIDRA_INSTALL_DIR` set to the Ghidra root (e.g. `C:\ghidra_12.0_PUBLIC`)
3. No other setup needed — `BinaryAnalyzer` finds `analyzeHeadless.bat` under `<GHIDRA_INSTALL_DIR>/support/`

### 3.2 How it works

```
analyzeHeadless <temp_project_dir> <project_name> \
  -import <file> \
  -noanalysis \
  -postScript <script> [args...] \
  -deleteProject
```

1. Creates a temporary Ghidra project
2. Imports the target binary
3. Runs the analysis script (`ghidra_scripts/analyze_binary.py`)
4. Saves results as JSON in the current directory
5. Deletes the temporary project

### 3.3 What you get

The headless analysis produces a JSON file with:
- Functions (name, address, size)
- Imported symbols
- Exported symbols
- Architecture info

### 3.4 Custom scripts

Place your own Ghidra (Python) scripts in `ghidra_scripts/` and call:

```python
analyze_binary("file.exe", tools=["ghidra"])  # uses default script
```

For custom scripts, `BinaryAnalyzer._analyze_with_ghidra_headless()` accepts `script_path` and `script_args` parameters.

---

## 4. ReVa reference: assistant vs headless mode

| | Assistant mode | Headless mode (`mcp-reva`) |
|---|---|---|
| Ghidra GUI | Required — runs in foreground | Not needed — background process |
| Project management | Manual — user opens project | Auto — managed by ReVa |
| MCP transport | HTTP (port 8080 by default) | HTTP or stdio |
| Use case | Active RE with visual feedback | Scripted / CI pipelines |
| Ghidra version | Any with matching ReVa extension | 12.0+ (verify upstream) |

**Switching:** You can run both on different ports if needed.

---

## 5. Ghidra scripts in this repo

| Script | Purpose | Called by |
|--------|---------|-----------|
| `ghidra_scripts/analyze_binary.py` | Extract functions, imports, exports, arch info | `analyze_binary(..., ['ghidra'])` |
| `ghidra_scripts/decompile_function.py` | Decompile a single function by name | `_analyze_with_ghidra_headless()` |
| `ghidra_scripts/test_script.py` | Test / validation | Manual |

All scripts use Ghidra's Python API (Jython) and output JSON.

---

## 6. analyzeHeadless CLI reference

Full reference: [Ghidra Headless Analyzer docs](https://ghidradocs.com/11.1_PUBLIC/support/analyzeHeadlessREADME.html)

### Key flags

| Flag | Purpose |
|------|---------|
| `-import <path>` | Import a file into the project |
| `-postScript <path>` | Run a script after import/analysis |
| `-preScript <path>` | Run a script before analysis |
| `-scriptPath <dir>` | Additional script search directory |
| `-noanalysis` | Skip auto-analysis (run analysis from script) |
| `-deleteProject` | Remove the temporary project after completion |
| `-process <file>` | Process an existing project file |
| `-readOnly` | Open project read-only |
| `-analysisTimeoutPerFile <sec>` | Per-file analysis timeout |
| `-max-cpu <n>` | CPU threads for analysis |
| `-commit <"all">` | Save project changes |
| `-prescript` | Pre-analysis script |
| `-postscript` | Post-analysis script |

### Common patterns

```powershell
# Extract functions only (no auto-analysis)
analyzeHeadless C:\temp MCP_Proj -import binary.exe -noanalysis -postScript extract_functions.py -deleteProject

# Full analysis with decompilation
analyzeHeadless C:\temp MCP_Proj -import binary.exe -postScript decompile_all.py -deleteProject

# Custom analysis with timeout
analyzeHeadless C:\temp MCP_Proj -import binary.exe -postScript my_script.py -analysisTimeoutPerFile 300 -deleteProject
```

---

## 7. Troubleshooting

### "analyzeHeadless.bat not found"
- `GHIDRA_INSTALL_DIR` is wrong or not set
- Verify the path contains `support/analyzeHeadless.bat`
- Common paths: `C:\ghidra_12.0_PUBLIC`, `C:\Program Files\ghidra_12.0_PUBLIC`

### "Ghidra not available" in check_tools()
- `BinaryAnalyzer` scans: `GHIDRA_HOME`/`GHIDRA_INSTALL_DIR` env vars, then `C:\ghidra*`, `D:\ghidra*`, `C:\Program Files\ghidra*`
- Set `GHIDRA_INSTALL_DIR` explicitly for reliable detection

### ReVa shows "No tools" in MCP client
1. Ghidra must be running with a project open and a binary loaded
2. The ReVa HTTP listener must be enabled in Ghidra's tool options
3. Check port: `Test-NetConnection 127.0.0.1 -Port 8080`
4. Verify Cursor/Claude config uses `"type": "http"` (not just `"url"`)

### ReVa HTTP server won't start
- Check Ghidra logs (Help → Logs)
- Ensure port 8080 is not in use: `netstat -an | findstr :8080`
- In ReVa tool options, verify `server.enabled` is checked
- Try changing port in ReVa settings, then update MCP client URL

### Headless analysis is slow
- Large binaries can take hours; use `-analysisTimeoutPerFile` and `-max-cpu`
- Ghidra's headless mode is single-process; parallelize by running separate instances
- For quick checks, skip auto-analysis with `-noanalysis` and use targeted scripts

### "Analysis completed but result file not found"
- The Ghidra script may have failed silently
- Check `stderr` in the returned error dict
- Run the script manually in Ghidra's GUI Script Manager first

### Out of memory
- Increase JVM heap: set `-Xmx8G` or higher in `support/analyzeHeadless.bat` or `ghidraRun.bat`
- Default heap is often too small for large binaries

---

## 8. References

- [Ghidra homepage](https://ghidra-sre.org/)
- [Ghidra GitHub](https://github.com/NationalSecurityAgency/ghidra)
- [Ghidra Headless Analyzer README](https://ghidradocs.com/11.1_PUBLIC/support/analyzeHeadlessREADME.html)
- [ReVa GitHub](https://github.com/cyberkaida/reverse-engineering-assistant)
- [PyGhidra](https://pypi.org/project/pyghidra/) — alternative headless path
- [LaurieWired GhidraMCP](https://github.com/LaurieWired/GhidraMCP) — legacy GUI plugin (removed from this server)
- [Ghidra Book (Eagle & Nance)](https://nostarch.com/ghidrabook)
