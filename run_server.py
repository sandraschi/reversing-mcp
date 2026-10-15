"""PyInstaller entrypoint for reversing-mcp HTTP sidecar."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
else:
    base = Path(__file__).resolve().parent
if str(base / "src") not in sys.path:
    sys.path.insert(0, str(base / "src"))

# Eager imports for the frozen build (TAURI_PRODUCTION_PITFALLS.md §E):
# stdlib C extensions + the mcp bootstrap before fastmcp touches it.
import _datetime  # noqa: F401
import _strptime  # noqa: F401

import mcp.types  # noqa: F401

# Explicit MCP_TRANSPORT=stdio is how AI clients (Claude Desktop, Cursor, ...) launch this exe
# after the installer registers it; the Tauri shell sets nothing and gets the HTTP sidecar.
_STDIO = os.environ.get("MCP_TRANSPORT", "").lower() == "stdio"
os.environ.setdefault("MCP_TRANSPORT", "http")

if __name__ == "__main__" and _STDIO:
    from reversing_mcp.server import main

    main()
elif __name__ == "__main__":
    import uvicorn

    from reversing_mcp.server import app

    host = os.environ.get("REVERSING_MCP_HOST", os.environ.get("MCP_HOST", "127.0.0.1"))
    port = int(
        os.environ.get("PORT")
        or os.environ.get("REVERSING_MCP_PORT")
        or os.environ.get("MCP_PORT")
        or os.environ.get("WEB_PORT")
        or "10750"
    )
    log_level = os.environ.get("REVERSING_LOG_LEVEL", "info")
    uvicorn.run(app, host=host, port=port, log_level=log_level)
