# Ghidra Integration

## Current model (2026)

**reversing-mcp** no longer ships LaurieWired **GhidraMCP** HTTP bridge tools (`ghidra_*`, `ghidra_setup_help`, `start_ghidra`). Those required a human at the Ghidra GUI with the plugin running.

For **Ghidra over MCP**, add **[ReVa](https://github.com/cyberkaida/reverse-engineering-assistant)** (reverse-engineering-assistant) as a **separate MCP server** in your client:

- **Assistant mode:** Ghidra GUI + ReVa extension; HTTP endpoint (e.g. streamable HTTP to `/mcp/message`).
- **Headless (Ghidra 12.0+):** `mcp-reva` with `GHIDRA_INSTALL_DIR` set — see ReVa release notes for your Ghidra version.

Discover ReVa tools from your host’s tool list; names differ from the old `ghidra_*` wrappers.

### Do you need both reversing-mcp and ReVa?

| If you only want… | Enough with… |
|-------------------|----------------|
| Decompile, xrefs, rename, etc. **in Ghidra** via MCP | **ReVa** (plus Ghidra + extension). reversing-mcp is **not** required for that. |
| **Strings, PE, entropy, hexdump** without starting Ghidra | **reversing-mcp** (or any other static analyzer). |
| **Digitale Bibliothek** helpers: `digibib_research_snapshot`, heuristic `.DKI` decode/batch, doc’d workflow | **reversing-mcp** (ReVa does not replace these). |
| **Web upload** static overview + LLM dashboard | **reversing-mcp** webapp / API — it is **not** a UI for **reva-chat** / ReVa CLI; it calls this repo’s FastAPI + `BinaryAnalyzer`. |

So: **not barking up the wrong tree** — ReVa is the right MCP surface **for Ghidra**. **reversing-mcp is not superfluous** if you care about static-only triage, DKI experiments, headless `analyzeHeadless` from `analyze_binary`, or the webapp. For “Ghidra session only,” ReVa alone can be sufficient.

### `GHIDRA_INSTALL_DIR` (headless / ReVa tooling)

Point this at the **root of your Ghidra distribution** (the folder that contains `support\analyzeHeadless.bat` and `Ghidra\` or equivalent). Examples:

- `C:\Program Files\ghidra_12.0_PUBLIC` (common system install)
- `C:\Users\<you>\AppData\Roaming\ghidra\ghidra_12.0_PUBLIC` (user-local install — use this if that is where your **actual** 12.0 tree lives)

If you have **two** trees, use the one that matches how you launch Ghidra and where `analyzeHeadless` runs.

### Cursor (`~/.cursor/mcp.json`)

**Assistant mode** (Ghidra GUI + ReVa extension listening on default port):

```json
"reva-assistant": {
  "url": "http://127.0.0.1:8080/mcp/message"
}
```

1. Install the ReVa **Ghidra extension** for your Ghidra version ([releases](https://github.com/cyberkaida/reverse-engineering-assistant/releases)), enable **ReVa Application Plugin** and **ReVa Plugin** in Ghidra per upstream README.
2. Start Ghidra, open a project (and a binary if you want tools to return data).
3. Confirm the MCP endpoint is up (default **8080**; change port in Ghidra ReVa settings if needed — then update the URL above).
4. **Restart Cursor** (or reload MCP) so it picks up `mcp.json`.

**Headless:** Upstream documents `mcp-reva` for newer releases; the PyPI tool `reverse-engineering-assistant` may ship `reva-server.exe` / `reva-chat.exe` instead — use whatever matches your installed version and set `GHIDRA_INSTALL_DIR` to your Ghidra root (e.g. `C:\\Program Files\\ghidra_12.0_PUBLIC`).

## Static analysis in this repo

`analyze_binary(..., ['ghidra'])` can still use **Ghidra’s headless analyzer** (`analyzeHeadless`) when Ghidra is installed, via `BinaryAnalyzer` in `analyzers.py`. That is batch/script style, not the old plugin HTTP bridge.

## Headless and automation

- **Batch / CI:** `support/analyzeHeadless` with `-preScript` / `-postScript`.
- **ReVa headless:** preferred MCP path when Ghidra 12+ and ReVa support it.
- **Alternatives:** PyGhidra, or other headless MCP stacks (e.g. community pyghidra-mcp projects) — separate from reversing-mcp.

## References

- [Ghidra](https://ghidra-sre.org/)
- [ReVa](https://github.com/cyberkaida/reverse-engineering-assistant)
- [Ghidra Headless Analyzer](https://ghidradocs.com/11.1_PUBLIC/support/analyzeHeadlessREADME.html)
- [PyGhidra](https://pypi.org/project/pyghidra/)
- [LaurieWired GhidraMCP](https://github.com/LaurieWired/GhidraMCP) — legacy GUI plugin pattern (removed from this server)
