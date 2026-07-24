# IDA Pro Integration

[IDA Pro](https://hex-rays.com/ida-pro/) is a commercial disassembler and decompiler. This guide covers headless integration with reversing-mcp.

**Cost:** Subscription-only (no perpetual licenses). The edition you need depends on whether you want scripting/headless mode, and how many architectures you need.

---

## Contents

1. [What works](#1-what-works)
2. [Detection](#2-detection)
3. [Headless analysis](#3-headless-analysis)
4. [Function finding](#4-function-finding)
5. [IDA scripts in this repo](#5-ida-scripts-in-this-repo)
6. [Troubleshooting](#6-troubleshooting)
7. [References](#7-references)

---

## 1. What works

| Operation | How | Status |
|-----------|-----|--------|
| **Full analysis** | `analyze_binary(file, ['ida'])` — runs IDA headless, extracts functions, imports, segments | ✅ Implemented |
| **Function list** | `find_functions(file, 'ida')` — wraps the same headless path | ✅ Implemented |
| **Decompilation** | Via `ida_scripts/decompile_function.py` (address → pseudocode) | ✅ Script ready, not yet wired as a tool |
| **Interactive GUI** | Manual — launch IDA, open binary, use ReVa or IDA's native MCP | Not in scope |

All headless operations output JSON files that the MCP server reads back.

---

## 2. Detection

`check_tools()` scans these locations (in order):

| Path | Version |
|------|---------|
| `%IDA_DIR%\ida64.exe` | Any (set env var for custom paths) |
| `C:\Program Files\IDA Pro 8.3\ida64.exe` | 8.3 |
| `C:\Program Files\IDA Pro 8.3\ida.exe` | 8.3 (32-bit) |
| `C:\Program Files\IDA Pro 8.2\ida64.exe` | 8.2 |
| `C:\Program Files\IDA Pro 8.1\ida64.exe` | 8.1 |

Set `IDA_DIR` to your IDA installation root to override, e.g.:
```powershell
$env:IDA_DIR = "D:\Tools\IDA Pro 8.3"
```

---

## 3. Headless analysis

Command that runs under the hood:
```powershell
ida64.exe -A -S"ida_scripts\analyze_binary.py <output_json>" "<binary>"
```

Flags:
- `-A` — enable auto-analysis (no UI prompts)
- `-S"<script> [args]"` — run IDAPython/IDC script, optional args

The script produces a JSON file with:

| Key | Contents |
|-----|----------|
| `processor` | CPU architecture (e.g. `metapc`) |
| `image_base` | Preferred load address |
| `functions` | List of `{address, end, size, name}` |
| `segments` | List of `{name, start, end, perm}` |
| `imports` | Per-DLL import list `{module, imports: [{name, address}]}` |

---

## 4. Function finding

`find_functions(file, 'ida')` runs the same headless pipeline and returns the function list with `tool: "ida"` on each entry.

---

## 5. IDA scripts in this repo

| Script | Purpose |
|--------|---------|
| `ida_scripts/analyze_binary.py` | Extract functions, imports, segments to JSON |
| `ida_scripts/decompile_function.py` | Decompile a function by address (for future use) |

Scripts use **IDAPython** (Python 3, bundled with IDA 8.x). They run inside IDA's embedded interpreter via `-S`.

---

## 6. Troubleshooting

| Symptom | Likely cause |
|---------|-------------|
| `check_tools()` shows IDA not found | Install path not in standard locations. Set `IDA_DIR`. |
| IDA headless hangs | Large binary or slow analysis. Increase timeout in `_analyze_with_ida()`. |
| `Analyzer is not available` | IDA Pro required. IDA Free has no scripting. |
| `IDA script ran but produced no output` | IDAPython or import error. Run the script manually from IDA's Script Manager first. |
| `ida64.exe` not used | The scan list prefers `ida64.exe` over `ida.exe` for 64-bit headless. |

---

## 7. References

- [IDA Pro headless mode (Hex-Rays)](https://hex-rays.com/products/ida/support/idadoc/417.shtml)
- [IDAPython docs](https://www.hex-rays.com/products/ida/support/idapython_docs/)
- [IDA command-line flags](https://hex-rays.com/products/ida/support/idadoc/index.shtml)

## Edition comparison (2026 pricing)

| Edition | Price/yr | Scripting? | Headless? | Architectures | Decompiler | Use case |
|---------|----------|-----------|-----------|--------------|------------|----------|
| **IDA Free** | Free | ❌ No API/SDK | ❌ | x86/x64 only | Cloud x86/x64 | Evaluating UI — **useless for automation** |
| **IDA Home** | €365 | ✅ IDAPython + C++ SDK | ✅ | **1** of PC/ARM/MIPS/PPC/RISC-V | Cloud (2 of 1 family) | Hobbyist, non-commercial only |
| **IDA Pro Essential** | €1,099 | ✅ | ✅ | All 60+ | Cloud (2 of 1 family) | Cheapest commercial with headless |
| **IDA Pro Expert 2** | €2,999 | ✅ | ✅ | All 60+ | **Local** (2 of your choice) | Serious RE — local decompilers |
| **IDA Pro Ultimate** | €8,599 | ✅ | ✅ | All 60+ | All local | Everything |

**Key takeaway:** IDA Home (€365/yr) is the cheapest option that can run our headless scripts, but only supports **one** CPU architecture and is **non-commercial**. If all you need is x86 analysis for DigiBib5.exe (a 32-bit PE), IDA Home with x86/x64 decompiler covers it. Still €365/yr vs Ghidra being free for the same x86 job.

**IDA Free is useless for our integration** — no `-S` scripting flag, no IDAPython, no C++ SDK. It can't run `ida_scripts/analyze_binary.py`. It exists purely as a GUI demo.

### Alternatives (free)

If you don't have IDA Pro, the free alternatives are:
- **Ghidra** — full decompiler, multi-arch, local (not cloud) — [guide](GHIDRA.md)
- **IDR** — Delphi-only, but free — [guide](IDR.md)
- **radare2 / rizin** — no decompiler, but powerful analysis
