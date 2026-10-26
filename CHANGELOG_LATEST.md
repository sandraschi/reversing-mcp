# reversing-mcp — latest changes

## 2026-10-26 — `ghidra` forwarding tool + webapp section (no port/program hunting)

Interactive Ghidra goes through a single `ghidra` portmanteau that forwards to
ReVa's ~86 tools. The agent always drives a stdio `mcp-reva` child: no port, no
API key, no program to pick. You just start a session.

### MCP
- `ghidra` tool: `status` / `start` / `stop` / `tools` / `describe` / `call`.
  - `mode="headless"` (default, `confirm=True`): stdio mcp-reva, no window.
  - `mode="watch"` (alias `gui`): same child, plus a Ghidra desktop window to
    look at - a SEPARATE instance from the one driven (mcp-reva runs its own).
  - Startup is a background task (poll `status` until `ready`); `call` truncates
    at `REVA_MAX_TEXT_CHARS` (default 60000); the session and any watch window
    are torn down on stop and on backend shutdown.
- Dropped the "attach to a running Ghidra over an HTTP URL" path: it needs
  ReVa's internal random port and key, which the bridge deliberately does not
  handle, so it was never smooth.
- `reva(start, headless)` routes through the bridge; GUI spawn no longer
  inherits our stdio.

### Backend REST
`GET /api/v1/ghidra/session`, `POST /api/v1/ghidra/session/start|stop`,
`GET /api/v1/ghidra/tools[/{name}]`, `POST /api/v1/ghidra/call`.

### Webapp (`/ghidra`)
Workbench (one-button start + call panel with schema-filled argument
skeletons), Tool catalogue (search / filter / sort / paginate / count), Call
history (localStorage, replay). Sidebar entry, dashboard hero CTA, Help coverage.

### Verified live
Headless start loaded 86 tools in ~12s (warm). Search, describe, call
(list-project-files round-tripped real JSON from Ghidra) and clean stop all
confirmed against real mcp-reva.

### Tests
`tests/test_ghidra_bridge.py` - 8 cases over a fake in-memory ReVa (stdio).
Full suite green; `bun run build` clean.
