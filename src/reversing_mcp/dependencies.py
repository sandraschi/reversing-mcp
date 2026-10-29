"""Dependency availability contract for external reverse-engineering engines.

Every tool that shells out to an external binary must fail with a structured,
actionable error instead of a bare prose string. An agent calling ``revops_*``
needs four things a sentence cannot reliably give it: which dependency is
missing, how to install it, how to point the server at it, and how to verify.

Contract returned by :func:`missing` / :func:`require`::

    {
      "success": false,
      "error_type": "dependency_missing",
      "dependency": "ghidra",
      "tool": "ghidra",
      "error": "Ghidra is not installed or not configured.",
      "mitigation": {
          "install": ["winget install ..."],
          "configure": ["Set GHIDRA_INSTALL_DIR to the extracted folder"],
          "verify": "revops_toolbox(operation='probe')",
          "docs": "docs/GHIDRA.md"
      },
      "recovery_options": ["...", "..."]
    }

``recovery_options`` flattens the same content for clients that only render a
list of strings; both are always populated so neither consumer has to branch.

Availability checks are lazy-imported inside :func:`available` to avoid a cycle
with :mod:`reversing_mcp.reva`, :mod:`reversing_mcp.engines` and
:mod:`reversing_mcp.rea_bridge`, which all import this module at load time.
"""

from __future__ import annotations

import importlib.util
import shutil
from typing import Any

#: id -> display label, install/config/verify guidance and docs page.
DEPENDENCIES: dict[str, dict[str, Any]] = {
    "ghidra": {
        "label": "Ghidra",
        "install": [
            "Download Ghidra from https://ghidra-sre.org/ and extract it",
            "Requires a JDK 17+ on PATH (or set JAVA_HOME)",
        ],
        "configure": ["Set GHIDRA_INSTALL_DIR to the extracted ghidra_*_PUBLIC folder"],
        "docs": "docs/GHIDRA.md",
    },
    "reva": {
        "label": "ReVa (mcp-reva)",
        "install": [
            "pip install reverse-engineering-assistant  (or the fleet venv under D:/Dev/tools/reva)",
            "Requires a working Ghidra install",
        ],
        "configure": ["Put mcp-reva on PATH, or install it to D:/Dev/tools/reva/.venv"],
        "docs": "docs/REVA.md",
    },
    "ida": {
        "label": "IDA Pro",
        "install": ["Install IDA Pro (headless analysis needs idat64/idat, not IDA Free)"],
        "configure": ["Set IDA_DIR, or install under one of the IDA_SEARCH_ROOTS folders"],
        "docs": "docs/IDA.md",
    },
    "rea": {
        "label": "REA (rea-agents)",
        "install": [
            "Install Node.js 22.19+ / 24.11+ / 26+",
            "Run: just setup-rea   (equivalent to: npx rea-agents setup)",
        ],
        "configure": ["REA is invoked through the `rea` shim, or npx -y rea-agents@latest as fallback"],
        "docs": "docs/REA.md",
    },
    "die": {
        "label": "Detect It Easy (diec)",
        "install": ["Install Detect It Easy and put diec on PATH"],
        "configure": ["Set DIE_DIR to the Detect It Easy install folder"],
        "docs": "docs/DIE.md",
    },
    "capa": {
        "label": "capa",
        "install": [
            "Install capa (standalone exe embeds rules + FLIRT sigs; the pip build does not)",
            "Put capa on PATH",
        ],
        "configure": ["Set CAPA_EXE, and optionally CAPA_RULES / CAPA_SIGS"],
        "docs": "docs/CAPA.md",
    },
    "frida": {
        "label": "Frida",
        "install": ["uv sync --extra dynamic"],
        "configure": ["No configuration needed once the extra is installed"],
        "docs": "docs/FRIDA.md",
    },
    "r2": {
        "label": "radare2",
        "install": ["Install radare2 and put r2 on PATH"],
        "configure": ["No configuration needed"],
        "docs": "docs/TOOLBOX.md",
    },
    "binwalk": {
        "label": "Binwalk",
        "install": ["Install binwalk and put it on PATH"],
        "configure": ["No configuration needed"],
        "docs": "docs/TOOLBOX.md",
    },
}


def _which(*names: str) -> str | None:
    """Return the first resolvable executable from ``names``."""
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def available(dep_id: str) -> bool:
    """Return True when ``dep_id`` can actually be invoked on this machine.

    Never raises: an unknown id or a broken probe reports False, because the
    caller's next action (a mitigated error) is the same either way.
    """
    try:
        if dep_id == "reva":
            from .reva import find_mcp_reva

            return find_mcp_reva() is not None
        if dep_id == "ghidra":
            from .reva import find_ghidra_run

            if find_ghidra_run().get("dir"):
                return True
            return _which("ghidraRun", "ghidraRun.bat") is not None
        if dep_id == "rea":
            from .rea_bridge import find_rea_runner

            return find_rea_runner() is not None
        if dep_id == "die":
            from .engines import find_diec

            return find_diec() is not None
        if dep_id == "capa":
            from .engines import find_capa

            return find_capa() is not None
        if dep_id == "frida":
            return importlib.util.find_spec("frida") is not None
        if dep_id == "r2":
            return _which("r2") is not None
        if dep_id == "binwalk":
            return _which("binwalk") is not None
        if dep_id == "ida":
            from .analyzers import AnalyzerEngine

            return bool(AnalyzerEngine().check_available_tools().get("ida", {}).get("available"))
    except Exception:  # a probe must never break the caller
        return False
    return False


def missing(dep_id: str, *, tool: str | None = None, detail: str | None = None) -> dict[str, Any]:
    """Build the structured ``dependency_missing`` error for ``dep_id``."""
    spec = DEPENDENCIES.get(dep_id, {})
    label = spec.get("label", dep_id)
    install = list(spec.get("install", []))
    configure = list(spec.get("configure", []))
    docs = spec.get("docs")
    verify = "revops_toolbox(operation='probe')"

    mitigation: dict[str, Any] = {"install": install, "configure": configure, "verify": verify}
    if docs:
        mitigation["docs"] = docs

    recovery = [f"Install {label}: {line}" for line in install]
    recovery += [f"Configure {label}: {line}" for line in configure]
    recovery.append(f"Verify with {verify}")
    if docs:
        recovery.append(f"Details: {docs}")

    error = f"{label} is not installed or not configured."
    if detail:
        error = f"{error} {detail}"

    payload: dict[str, Any] = {
        "success": False,
        "error_type": "dependency_missing",
        "dependency": dep_id,
        "error": error,
        "mitigation": mitigation,
        "recovery_options": recovery,
    }
    if tool:
        payload["tool"] = tool
    return payload


def require(dep_id: str, *, tool: str | None = None, detail: str | None = None) -> dict[str, Any] | None:
    """Return ``None`` when ``dep_id`` is available, else the mitigated error.

    Use as a guard::

        blocked = require("capa", tool="engine:capa")
        if blocked:
            return blocked
    """
    if available(dep_id):
        return None
    return missing(dep_id, tool=tool, detail=detail)
