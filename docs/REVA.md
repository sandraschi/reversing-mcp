# ReVa — Ghidra MCP Server

[ReVa](https://github.com/cyberkaida/reverse-engineering-assistant) (reverse-engineering-assistant) exposes Ghidra's analysis engine as an MCP server. It gives you 30+ tools for interactive reverse engineering: decompile, xrefs, rename, search strings, navigate functions, etc.

**It is a separate server from reversing-mcp.** You run both — reversing-mcp for static analysis (strings, PE, entropy, DKI), ReVa when you need Ghidra access.

---

## Contents

1. [Architecture overview](#1-architecture-overview)
2. [Install Ghidra](#2-install-ghidra)
3. [Install ReVa](#3-install-reva)
4. [Mode A: Assistant (Ghidra GUI + plugin)](#4-mode-a-assistant-ghidra-gui--plugin)
5. [Mode B: Headless (standalone, Ghidra 12.0+)](#5-mode-b-headless-standalone-ghidra-120)
6. [MCP client config](#6-mcp-client-config)
7. [Verify it works](#7-verify-it-works)
8. [Tool surface](#8-tool-surface)
9. [Two-server workflow](#9-two-server-workflow)
10. [Troubleshooting](#10-troubleshooting)
11. [References](#11-references)

---

## 1. Architecture overview

```
Your IDE (Cursor / Claude Desktop)
  ├── reversing-mcp (stdio)       — strings, entropy, PE, DKI, digibib
  └── reva-mcp (HTTP)             — decompile, xrefs, rename, symbols, Ghidra
```

ReVa speaks the MCP protocol over **Streamable HTTP**. The Ghidra side runs either as a plugin inside the Ghidra GUI (assistant mode) or as a standalone headless process.

---

## 2. Install Ghidra

If you don't have Ghidra yet:

1. Download the [latest release](https://github.com/NationalSecurityAgency/ghidra/releases) (12.1.2 as of mid-2026)
2. Extract to a stable path, e.g. `C:\ghidra_12.0_PUBLIC`
3. Set environment variable:

```powershell
[Environment]::SetEnvironmentVariable("GHIDRA_INSTALL_DIR", "C:\ghidra_12.0_PUBLIC", "User")
```

This variable is used by both ReVa and our headless `analyze_binary(..., ['ghidra'])`.

> **Note:** Headless mode requires Ghidra 12.0+. Assistant mode works with any version that has a matching ReVa extension.

---

## 3. Install ReVa

```powershell
pip install reverse-engineering-assistant
```

Or clone from [github.com/cyberkaida/reverse-engineering-assistant](https://github.com/cyberkaida/reverse-engineering-assistant) and follow upstream README.

Check installation:

```powershell
pip show reverse-engineering-assistant
```

---

## 4. Mode A: Assistant (Ghidra GUI + plugin)

Best for active RE sessions where you want the Ghidra GUI open for visual navigation.

### 4.1 Install the Ghidra extension

1. Download the ReVa extension `.zip` from [GitHub releases](https://github.com/cyberkaida/reverse-engineering-assistant/releases) matching your Ghidra version
2. In Ghidra: `File → Install Extensions`, click `+`, select the `.zip`, restart Ghidra

### 4.2 Enable plugins

`File → Configure → Tool` → check **ReVa Application Plugin** and **ReVa Plugin**

### 4.3 Start Ghidra and the MCP listener

1. Launch Ghidra, open a project, load a binary
2. `Edit → Tool Options → ReVa` → enable `server.enabled` (default port **8080**)

### 4.4 Connect your MCP client

See [MCP client config](#6-mcp-client-config) below.

---

## 5. Mode B: Headless (standalone, Ghidra 12.0+)

No Ghidra GUI needed. ReVa starts Ghidra headless and exposes the same MCP surface.

```powershell
$env:GHIDRA_INSTALL_DIR = "C:\ghidra_12.0_PUBLIC"
mcp-reva
```

ReVa listens on an HTTP port (default varies — check upstream docs). Configure your MCP client to point at that endpoint.

---

## 6. MCP client config

### Cursor (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "reversing-mcp": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/reversing-mcp", "run", "python", "-m", "reversing_mcp"]
    },
    "reva": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp/message"
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "reversing-mcp": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/reversing-mcp", "run", "python", "-m", "reversing_mcp"]
    },
    "reva": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp/message"
    }
  }
}
```

**Important:** The `"type": "http"` field is required for streamable HTTP MCP servers. Without it, Cursor/Claude may show ReVa as "not starting" or "no tools."

---

## 7. Verify it works

```powershell
# Check the port is listening
Test-NetConnection -ComputerName 127.0.0.1 -Port 8080
# Expect: TcpTestSucceeded: True
```

Once connected, your MCP client will list ReVa's tools alongside reversing-mcp's. You should see 30+ tools.

---

## 8. Tool surface

ReVa provides roughly 30+ tools. Key categories:

| Category | Example tools |
|----------|---------------|
| **Decompilation** | `decompile_function`, `decompile_range`, `pseudocode` |
| **Functions** | `list_functions`, `get_function`, `rename_function`, `set_function_type` |
| **Navigation** | `go_to_address`, `get_xrefs_to`, `get_xrefs_from`, `get_calling_functions` |
| **Strings** | `search_strings`, `list_strings`, `get_string_at` |
| **Symbols** | `list_imports`, `list_exports`, `get_symbol_at`, `list_namespaces` |
| **Types** | `get_data_type`, `list_data_types`, `create_structure` |
| **Program** | `get_program_info`, `list_sections`, `get_image_base`, `analyze` |

Tool names differ from the old `ghidra_*` wrappers that were removed from reversing-mcp. Discover the full list via your client's tool discovery.

---

## 9. Two-server workflow

The typical DigiBib reversing session uses both servers:

| Step | Server | Tool |
|------|--------|------|
| Static triage | reversing-mcp | `check_tools()`, `analyze_binary()`, `digibib_research_snapshot()` |
| IDR symbols | *(manual)* | IDR → export .map → load into Ghidra |
| Decompile a function | **ReVa** | `decompile_function("TTextReader_ReadLn")` |
| Find xrefs | **ReVa** | `get_xrefs_to(address)` |
| Rename a function | **ReVa** | `rename_function("FUN_1234", "DKI_ReadHeader")` |
| Search for strings | **ReVa** | `search_strings("decompress")` |
| PE / entropy check | reversing-mcp | `analyze_pe_file()`, `analyze_entropy()` |
| DKI decode | reversing-mcp | `decode_dki_file()`, `decompress_directmedia_library()` |

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| ReVa shows "No tools" | Ghidra not running or no binary open | Start Ghidra, open a project, load a binary |
| "Connection refused" on port 8080 | ReVa HTTP listener not enabled | `Edit → Tool Options → ReVa` → enable `server.enabled` |
| Port 8080 in use | Another app on that port | Change port in ReVa settings, update MCP config URL |
| Client shows "not starting" | Missing `"type": "http"` in config | Add `"type": "http"` to the ReVa entry |
| `mcp-reva` not found | ReVa not installed or not on PATH | `pip install reverse-engineering-assistant` |
| `GHIDRA_INSTALL_DIR` not set | Env var missing | Set to your Ghidra root (the folder with `support/analyzeHeadless.bat`) |
| No decompiler output | Binary not analyzed yet | Wait for auto-analysis, or run `analyze` in ReVa |

---

## 11. References

- [ReVa GitHub](https://github.com/cyberkaida/reverse-engineering-assistant) — upstream source, issues, releases
- [Ghidra homepage](https://ghidra-sre.org/) — download, docs
- [Ghidra Headless Analyzer README](https://ghidradocs.com/11.1_PUBLIC/support/analyzeHeadlessREADME.html)
- [reversing-mcp Ghidra guide](GHIDRA.md) — our headless analyzeHeadless integration + ghidra_scripts
- [reversing-mcp IDR guide](IDR.md) — Delphi symbol recovery (prerequisite before ReVa)
