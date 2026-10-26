# Ghidra Integration Guide

Ghidra is the NSA's free and open-source reverse engineering framework ([Apache 2.0](https://ghidra-sre.org/)). There are three ways to use Ghidra with reversing-mcp.

---

## 1. The `ghidra` tool (interactive, recommended)

reversing-mcp forwards to ReVa through a single portmanteau tool, `ghidra`, so
you do not add a second MCP server to your client and do not boot a JVM until
you ask for one. ReVa exposes ~86 Ghidra tools; mounting them directly floods
the client tool list, so they stay behind one entry here.

The agent ALWAYS drives through a stdio `mcp-reva` child: no port, no API key,
no hunting. mcp-reva runs its own in-process Ghidra and manages ReVa's internal
random HTTP port and key itself; reversing-mcp never touches those. You just
start a session.

### Operations

| Operation | What it does |
|-----------|--------------|
| `status` | Session state: `stopped` / `starting` / `ready` / `error`, mode, `gui_window`, tool count |
| `start` | Boots a session (needs `confirm=True`). `mode="headless"` is just the stdio child; `mode="watch"` also opens a Ghidra window to look at |
| `stop` | Ends the session (JVM terminated; any watch window is closed too) |
| `tools` | Search the ReVa catalogue (`query`, `offset`, `limit`); returns `{name, summary}` |
| `describe` | Full description + input schema of one ReVa tool |
| `call` | Invoke one ReVa tool with `arguments` (see `describe`) |

### Two modes (same stdio driver)

- **headless** (default, `confirm=True`): spawns `mcp-reva` over stdio with its
  own Ghidra JVM. ~1-2 min cold boot (seconds when warm), ~1-2 GB RAM, no
  window. Needs `mcp-reva` (fleet venv at `D:/Dev/tools/reva`, see
  [REVA.md](REVA.md)) and `GHIDRA_INSTALL_DIR`. The stdio stream is driven over
  pipes by the bridge, never spawned bare: a child on our own stdout would
  corrupt the MCP JSON-RPC stream.
- **watch** (`confirm=True`): the same stdio child, PLUS the Ghidra desktop GUI
  launched alongside so you can see a project. IMPORTANT: that window is a
  SEPARATE Ghidra instance from the one the agent drives (mcp-reva runs its own
  in-process Ghidra). The window is for looking, not the one being edited.
  ReVa has no supported way to attach a second client to a running GUI's plugin
  without its internal port and key, which we deliberately do not handle, so
  "attach to a GUI and drive it live" is not offered. `mode="gui"` is accepted
  as an alias for `watch`.

### Workflow

```
ghidra(operation="start", confirm=True)    # or mode="watch" to also open a window
ghidra(operation="status")                 # poll until state="ready"
ghidra(operation="tools", query="decompil")
ghidra(operation="describe", tool="get-decompilation")
ghidra(operation="call", tool="get-functions", arguments={"programPath": "/prog.exe"})
ghidra(operation="stop")
```

### Notes

- **One session per process.** The webapp backend and a chat client (e.g.
  Claude Desktop over stdio) are separate processes, so each has its own
  session and its own mcp-reva child.
- Long output is truncated at `REVA_MAX_TEXT_CHARS` (default 60000) with a
  `truncated_from` marker; narrow the query rather than paging blindly.
- The older `reva` tool still manages ReVa's raw lifecycle. Its `headless`
  start routes through this bridge; its `gui` start launches the Ghidra desktop
  app (what `watch` uses under the hood).

### Webapp

The **Ghidra** section of the web UI (`/ghidra`) mirrors this: a Workbench to
start/stop a session and call tools, a searchable Tool catalogue, and a
per-browser Call history. Backend routes: `GET /api/v1/ghidra/session`,
`POST /api/v1/ghidra/session/start|stop`, `GET /api/v1/ghidra/tools[/{name}]`,
`POST /api/v1/ghidra/call`.

---

## 2. Headless analyzeHeadless (batch/script)

`analyze_binary(file_path, tools=['ghidra'])` uses Ghidra's `analyzeHeadless.bat` to run batch analysis without opening the GUI.

### Prerequisites

1. Ghidra installed (any version 10.x+)
2. `GHIDRA_INSTALL_DIR` set to the Ghidra root (folder containing `support/analyzeHeadless.bat`)

### How it works

```
analyzeHeadless <temp_project_dir> <project_name> \
  -import <file> \
  -noanalysis \
  -postScript <script> [args...] \
  -deleteProject
```

1. Creates a temporary Ghidra project
2. Imports the target binary
3. Runs our analysis script (`ghidra_scripts/analyze_binary.py`)
4. Saves results as JSON
5. Deletes the temporary project

### What you get

- Functions (name, address, size)
- Imported symbols
- Exported symbols
- Architecture info

### Custom scripts

Place scripts in `ghidra_scripts/` and call:

```python
analyze_binary("file.exe", tools=["ghidra"])  # uses default script
```

---

## 3. Ghidra scripts in this repo

| Script | Purpose | Called by |
|--------|---------|-----------|
| `ghidra_scripts/analyze_binary.py` | Extract functions, imports, exports, arch info | `analyze_binary(..., ['ghidra'])` |
| `ghidra_scripts/decompile_function.py` | Decompile a single function by name | `_analyze_with_ghidra_headless()` |
| `ghidra_scripts/test_script.py` | Test / validation | Manual |

All scripts use Ghidra's Python API (Jython) and output JSON.

---

## 4. analyzeHeadless CLI reference

Full reference: [Ghidra Headless Analyzer docs](https://ghidradocs.com/11.1_PUBLIC/support/analyzeHeadlessREADME.html)

### Key flags

| Flag | Purpose |
|------|---------|
| `-import <path>` | Import a file into the project |
| `-postScript <path>` | Run a script after import/analysis |
| `-preScript <path>` | Run a script before analysis |
| `-scriptPath <dir>` | Additional script search directory |
| `-noanalysis` | Skip auto-analysis |
| `-deleteProject` | Remove the temporary project after completion |
| `-process <file>` | Process an existing project file |
| `-analysisTimeoutPerFile <sec>` | Per-file analysis timeout |
| `-max-cpu <n>` | CPU threads for analysis |
| `-commit <"all">` | Save project changes |

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

## 5. Troubleshooting

### "analyzeHeadless.bat not found"
- `GHIDRA_INSTALL_DIR` is wrong or not set
- Verify the path contains `support/analyzeHeadless.bat`
- Common paths: `C:\ghidra_12.0_PUBLIC`, `C:\Program Files\ghidra_12.0_PUBLIC`

### "Ghidra not available" in check_tools()
- BinaryAnalyzer scans: `GHIDRA_HOME`/`GHIDRA_INSTALL_DIR` env vars, then `C:\ghidra*`, `D:\ghidra*`, `C:\Program Files\ghidra*`
- Set `GHIDRA_INSTALL_DIR` explicitly for reliable detection

### Headless analysis is slow
- Large binaries can take hours; use `-analysisTimeoutPerFile` and `-max-cpu`
- For quick checks, skip auto-analysis with `-noanalysis` and use targeted scripts

### Out of memory
- Increase JVM heap: set `-Xmx8G` in `support/analyzeHeadless.bat` or `ghidraRun.bat`

---

## 6. References

- [ReVa guide](REVA.md) — interactive Ghidra MCP setup
- [Ghidra homepage](https://ghidra-sre.org/)
- [Ghidra GitHub](https://github.com/NationalSecurityAgency/ghidra)
- [Ghidra Headless Analyzer README](https://ghidradocs.com/11.1_PUBLIC/support/analyzeHeadlessREADME.html)
- [Ghidra Book (Eagle & Nance)](https://nostarch.com/ghidrabook)
