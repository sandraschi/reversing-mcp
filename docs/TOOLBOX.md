# Toolbox - autodiscovery, install, autostart

`src/reversing_mcp/toolbox.py`. Contract: **no hand-editing env, no manual
installs.** The backend discovers the toolchain on boot, exports what it finds
into its own environment, installs what is missing, and starts policy services.
Status page Toolbox card (`GET /api/v1/toolbox`) + `toolbox()` MCP tool.

## Inventory (11 entries)

| Tool | Found how | Install | Note |
|------|-----------|---------|------|
| ghidra | `GHIDRA_INSTALL_DIR` → `D:\Dev\tools\ghidra_*` → `C:\Program Files\ghidra_*` (analyzeHeadless fingerprint) | GitHub NSA release zip → `D:\Dev\tools` (no admin) | 12.1.3 fleet default (REA needs 12.1.x); 12.0 kept as fallback |
| reva | PATH → `D:\Dev\tools\reva\.venv` | codified venv+pip+compat (see `D:\Dev\tools\reva\README.md`) | autostarts headless with backend (policy) |
| capa | `engines.find_capa` + `D:\Dev\tools\capa` | mandiant/capa release exe | |
| die | `engines.find_diec` (+`DIE_DIR`) | horsicq/DIE-engine portable zip | |
| frida | `engines.check_frida` | `pip install frida` | executing target = confirm-gated elsewhere |
| r2 | PATH (`radare2`/`r2`/`rizin`) | winget `RizinOrg.Rizin` | |
| hopper | running process → install paths | none silent (commercial) | Windows: platform_blocked (macOS/Linux builds only) |
| ida | **running process first (glom)** → `IDA_DIR` → standard paths | none silent (commercial) | licensing is never checked |
| java | PATH (`java -version` ≥ 17) | winget Temurin 21 | Ghidra runtime |
| tesseract | fleet path `C:\Program Files\Tesseract-OCR` | winget `UB-Mannheim.TesseractOCR` | ClickerLab B3 OCR |
| node | PATH | winget LTS | REA sidecar needs 22+ |

States: `ready` | `missing` (with installer ref) | `broken` (found but unusable +
reason) | `platform_blocked` | IDA glom rows carry `pid`.

## IDA glom rule (firm)

If `ida64.exe`/`ida.exe` is running, the toolbox reports `ready` and the
agent attaches — licensing is between the user and Hex-Rays, never the
detector's business. Absent entirely: `missing` + "start IDA or set IDA_DIR".

## Boot sequence (`ensure()`)

1. `probe()` all detectors (fast; only `--version` spawns).
2. Export discoveries into the backend process env (`GHIDRA_INSTALL_DIR`,
   `DIE_DIR`) when unset — this is why nobody edits env by hand.
3. Policy autostart (default: ReVa headless). Declared boot policy, logged;
   toggle via `GET/POST /api/v1/toolbox/policy`. Idempotent: re-runs skip
   running services. Runs on FastAPI startup only (never on stdio spawn).

## Routes / ops

REST: `GET /api/v1/toolbox`, `POST /api/v1/toolbox/{install,rescan,ensure}`,
`GET|POST /api/v1/toolbox/policy`. MCP: `toolbox(operation="probe"|"install"|"ensure"|"policy", name?)`.
