# Ghidra Integration Guide

Ghidra is the NSA's free and open-source reverse engineering framework ([Apache 2.0](https://ghidra-sre.org/)). There are two ways to use Ghidra with reversing-mcp.

---

## 1. ReVa MCP (interactive, recommended)

ReVa is a **separate MCP server** that exposes Ghidra's decompiler, xrefs, rename, and 30+ tools over MCP. Run it alongside reversing-mcp.

**Setup:** See the [dedicated ReVa guide](REVA.md) — covers install, both modes (assistant + headless), MCP client config, and two-server workflow.

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
