# reversing-mcp — latest changes

## 2026-10-26 — `ghidra` forwarding tool + webapp section

Interactive Ghidra now goes through a single `ghidra` portmanteau that forwards
to ReVa's ~86 tools, instead of mounting ReVa as a second MCP server and booting
a JVM at client start.

### MCP
- `ghidra` tool: `status` / `start` / `stop` / `tools` / `describe` / `call`.
  - **headless**: spawns `mcp-reva` over stdio (lazy JVM, `confirm=True`).
  - **gui**: attaches over streamable HTTP to a running Ghidra's ReVa plugin,
    so the agent's renames/comments land live in the window.
  - Startup runs as a background task (poll `status` until `ready`); `call`
    truncates at `REVA_MAX_TEXT_CHARS` (default 60000); the session is torn
    down on backend shutdown.
- `reva(start, headless)` routes through the bridge; GUI spawn no longer
  inherits our stdio (a child on stdout corrupts the MCP stream).

### Backend REST
`GET /api/v1/ghidra/session`, `POST /api/v1/ghidra/session/start|stop`,
`GET /api/v1/ghidra/tools[/{name}]`, `POST /api/v1/ghidra/call`.

### Webapp (`/ghidra`)
Workbench (start/stop + call panel with schema-filled argument skeletons),
Tool catalogue (search / filter / sort / paginate / count), Call history
(localStorage, replay). Sidebar entry, dashboard hero CTA, Help coverage.

### Tests
`tests/test_ghidra_bridge.py` — fake in-memory ReVa server, 5 cases (full gui
cycle, not-ready guards, unreachable error, missing launcher, transport failure).
All green; `bun run build` clean.
