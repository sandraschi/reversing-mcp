# Ghidra Integration

## How Reversing-MCP Uses Ghidra

Reversing-MCP **does not run or embed Ghidra**. All `ghidra_*` tools talk to **LaurieWired's GhidraMCP plugin** over HTTP.

1. **You run Ghidra** (GUI) with the GhidraMCP plugin installed.
2. The **plugin** runs inside Ghidra and starts an **HTTP server** (default `http://127.0.0.1:8080/`).
3. **Reversing-MCP** sends HTTP GET/POST requests to that API; the plugin calls Ghidra's Java API and returns results.

If Ghidra (with the plugin) is not running, or the plugin is not listening, `ghidra_*` tools will return connection errors. Other tools (binary analysis, Directmedia, etc.) do not depend on Ghidra.

## Setup (GUI Path)

1. Install [Ghidra](https://ghidra-sre.org/) (e.g. 11.x or 12.x).
2. Install the [GhidraMCP plugin](https://github.com/LaurieWired/GhidraMCP) (e.g. `GhidraMCP.zip`) via Ghidra **File → Install Extensions**.
3. Start Ghidra, create or open a project, import a binary, run analysis.
4. Start the GhidraMCP HTTP server from the plugin (default port 8080).
5. Use `ghidra_*` tools from Reversing-MCP; they call the plugin API.

Use the MCP tool **`ghidra_setup_help(check_connection=True)`** to verify setup and whether the plugin is reachable.

## Headless Use

**The GhidraMCP plugin is built for the Ghidra GUI.** There is no documented headless mode for the plugin. `analyzeHeadless` runs scripts and exits; it does not keep a long-lived HTTP server.

- **With this setup (plugin + Reversing-MCP):** Headless is **not** supported. You must run the Ghidra GUI with the plugin.
- **For true headless** (no display, CI, batch):
  - Use **Ghidra's headless analyzer**: `support/analyzeHeadless` with `-preScript` / `-postScript` for batch analysis (no MCP/HTTP).
  - Or use a **headless MCP stack**: e.g. [pyghidra-mcp](https://clearbluejar.github.io/posts/pyghidra-mcp-headless-ghidra-mcp-server-for-project-wide-multi-binary-analysis/) (PyGhidra-based, project-wide analysis). That is a different integration from Reversing-MCP's plugin-based one.
  - **Ghidra 12+** and **PyGhidra 3.x** allow Python 3 scripting in headless for automation without the plugin.

## Why Headless Matters

- **Servers / CI / SSH:** No display (e.g. GitHub Actions, Docker, remote boxes).
- **Batch:** Analyze many binaries without opening the GUI.
- **Resources:** Headless typically uses less RAM/CPU than the GUI.
- **Automation:** Scripts and pipelines that do not require a human at the desktop.

## Plugin URL

Default: `http://127.0.0.1:8080/`. The bridge in `bridge_mcp_ghidra.py` uses this; it can be overridden via the bridge module's `ghidra_server_url` if your plugin is configured on another port.

## References

- [Ghidra](https://ghidra-sre.org/) — official site
- [GhidraMCP (LaurieWired)](https://github.com/LaurieWired/GhidraMCP) — plugin used by this server
- [Ghidra Headless Analyzer](https://ghidradocs.com/11.1_PUBLIC/support/analyzeHeadlessREADME.html) — batch/CLI usage
- [PyGhidra](https://pypi.org/project/pyghidra/) — Python 3 API (Ghidra 12+); option for headless scripting
