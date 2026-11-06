"""Ghidra community extensions: curated catalog + download/CRUD into the user Extensions dir.

Covers the gap the toolbox left open (``Extension install is separate - see probe``):
stock Ghidra 12.1.3 ships 39 processors but no 65c816/SNES path and an empty
``Ghidra/Extensions`` dir. This module manages the *user* extensions dir
(``%APPDATA%\\ghidra\\ghidra_<ver>_PUBLIC\\Extensions``):

- ``catalog()`` - curated community entries (SNES/65816 first) + installed status.
- ``list_installed()`` - dirs found on disk with manifest fingerprint.
- ``install_extension()`` - GitHub release asset (catalog name or owner/repo) or
  direct https .zip URL, unzipped into the user Extensions dir.
- ``remove_extension()`` - destructive, needs ``confirm=True``.
- ``set_enabled()`` - reversible enable/disable via ``<name>`` <-> ``<name>.disabled``
  rename (Ghidra only loads the plain dir on next start; no GUI state hacked).

Build-from-source extensions (SLEIGH/Java gradle builds) are reported as
``needs_build`` with the repo + docs pointer rather than faked: this module
only ships prebuilt release zips.
"""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

from .logging_config import get_logger

logger = get_logger("reversing_mcp.ghidra_extensions")

# ---------------------------------------------------------------------------
# curated catalog (verified 2026-11-06 via web receipts; asset_pattern=None
# means "grab the right zip from the repo Releases page", never a guessed URL)


CATALOG: list[dict[str, Any]] = [
    {
        "name": "ghidra-65816",
        "repo": "achan1989/ghidra-65816",
        "kind": "processor",
        "targets": ["SNES (Ricoh 5A22 / WDC 65c816)", "Apple IIgs"],
        "description": "WDC 65816 processor module (SLEIGH). Required before any SNES loader. Language 65816:LE:16:default.",
        "asset_pattern": r"65816.*\.zip$",
        "install_kind": "github_release",
    },
    {
        "name": "ghidra-snes-loader",
        "repo": "Raikaru/ghidra-snes-loader",
        "kind": "loader",
        "targets": ["SNES LoROM/HiROM SMC/SFC"],
        "description": "SNES ROM loader (header decode, memory map, vectors) + DBR/DP tracking analyser. Needs ghidra-65816. Modernised fork of the archived achan1989/ghidra-snes-loader.",
        "asset_pattern": r".*\.zip$",
        "install_kind": "github_release",
    },
    {
        "name": "ghidra-snes-loader-upstream",
        "repo": "achan1989/ghidra-snes-loader",
        "kind": "loader",
        "targets": ["SNES LoROM/HiROM"],
        "description": "Original SNES loader (archived upstream). Prefer Raikaru fork for current Ghidra; kept for provenance.",
        "asset_pattern": None,
        "install_kind": "manual",
    },
    {
        "name": "ghidra-snes-scripts",
        "repo": "joshleaves/ghidra-snes",
        "kind": "scripts",
        "targets": ["SNES ROM scripts"],
        "description": "Ghidra scripts for SNES ROM RE (not an Extension zip - clone into ghidra_scripts).",
        "asset_pattern": None,
        "install_kind": "manual",
    },
    {
        "name": "ghidra-findcrypt",
        "repo": "TorgoTorgo/ghidra-findcrypt",
        "kind": "analyzer",
        "targets": ["crypto constants (AES/DES/etc.)"],
        "description": "Auto-analysis module labelling crypto constants. Successor line to d3v1l401/FindCrypt-Ghidra script.",
        "asset_pattern": r".*\.zip$",
        "install_kind": "github_release",
    },
    {
        "name": "FindCrypt-Ghidra",
        "repo": "d3v1l401/FindCrypt-Ghidra",
        "kind": "scripts",
        "targets": ["crypto constants"],
        "description": "IDA FindCrypt port as Ghidra script (older line; TorgoTorgo fork is the maintained analyzer).",
        "asset_pattern": None,
        "install_kind": "manual",
    },
    {
        "name": "Ghidrathon",
        "repo": "cmu-sei/Ghidrathon",
        "kind": "scripting",
        "targets": ["Python 3 in Ghidra"],
        "description": "CPython 3 interpreter + scripting for Ghidra. Manual install per repo docs (version-pinned to Ghidra).",
        "asset_pattern": None,
        "install_kind": "manual",
    },
    {
        "name": "BinExport",
        "repo": "google/binexport",
        "kind": "diffing",
        "targets": ["BinDiff export"],
        "description": "BinExport exporter for BinDiff-style function matching. Manual install per repo docs (version-pinned).",
        "asset_pattern": None,
        "install_kind": "manual",
    },
]

_CATALOG_BY_NAME = {e["name"].lower(): e for e in CATALOG}


def _user_roots() -> list[Path]:
    roots: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        base = Path(appdata) / "ghidra"
        if base.is_dir():
            roots += sorted(base.glob("ghidra_*_PUBLIC"))
    home = Path.home() / ".ghidra"
    if home.is_dir():
        roots += sorted(home.glob("ghidra_*_PUBLIC"))
    return roots


def user_extensions_dirs() -> list[Path]:
    """All user Extensions dirs (usually exactly one). Never raises."""
    dirs: list[Path] = []
    for root in _user_roots():
        ext = root / "Extensions"
        if ext.is_dir():
            dirs.append(ext)
    return dirs


def primary_extensions_dir(create: bool = False) -> Path | None:
    """Newest user Extensions dir, optionally created. None when no Ghidra user dir."""
    dirs = user_extensions_dirs()
    if dirs:
        return sorted(dirs)[-1]
    roots = _user_roots()
    if not roots:
        return None
    ext = sorted(roots)[-1] / "Extensions"
    if create:
        ext.mkdir(parents=True, exist_ok=True)
        return ext
    return ext if ext.is_dir() else None


def _fingerprint(ext_dir: Path) -> dict[str, Any]:
    props = ext_dir / "extension.properties"
    manifest = ext_dir / "Module.manifest"
    info: dict[str, Any] = {"name": ext_dir.name, "path": str(ext_dir)}
    try:
        if props.is_file():
            text = props.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    info[k.strip()] = v.strip()[:120]
        elif manifest.is_file():
            info["manifest"] = True
    except OSError as e:
        info["error"] = str(e)[:150]
    return info


def list_installed() -> dict[str, Any]:
    """Dirs in the user Extensions dir(s), incl. `<name>.disabled` rows. Never raises."""
    items: list[dict[str, Any]] = []
    searched: list[str] = []
    try:
        for ext_root in user_extensions_dirs():
            searched.append(str(ext_root))
            for child in sorted(ext_root.iterdir()):
                if not child.is_dir():
                    continue
                row = _fingerprint(child)
                row["enabled"] = not child.name.endswith(".disabled")
                row["root"] = str(ext_root)
                items.append(row)
    except Exception as e:
        logger.debug("list_installed failed: %s", e)
        return {"success": False, "error": str(e)[:300], "extensions": [], "searched": searched}
    return {"success": True, "extensions": items, "count": len(items), "searched": searched}


def catalog() -> dict[str, Any]:
    """Curated entries enriched with installed/enabled status. Never raises."""
    installed = {r.get("name", "").lower().removesuffix(".disabled"): r for r in list_installed().get("extensions", [])}
    entries: list[dict[str, Any]] = []
    for entry in CATALOG:
        key = entry["name"].lower()
        row = dict(entry)
        hit = installed.get(key)
        row["installed"] = hit is not None
        row["enabled"] = bool(hit and hit.get("enabled")) if hit else False
        row["installed_path"] = hit.get("path") if hit else None
        entries.append(row)
    return {"success": True, "entries": entries, "count": len(entries)}


def _resolve_target(name_or_url: str) -> dict[str, Any]:
    from urllib.parse import urlparse

    text = (name_or_url or "").strip()
    if text.lower().startswith("https://") and text.lower().endswith(".zip"):
        return {"kind": "url", "url": text, "name": Path(urlparse(text).path).stem}
    key = text.lower()
    if key in _CATALOG_BY_NAME:
        entry = _CATALOG_BY_NAME[key]
        if entry.get("install_kind") != "github_release" or not entry.get("asset_pattern"):
            return {"kind": "manual", "entry": entry}
        return {"kind": "catalog", "entry": entry}
    if "/" in text and " " not in text:  # owner/repo shorthand
        return {"kind": "repo", "repo": text, "name": text.split("/")[-1]}
    entry = _CATALOG_BY_NAME.get(key)
    if entry:
        return {"kind": "manual", "entry": entry}
    return {"kind": "unknown"}


def install_extension(name_or_url: str, version: str | None = None) -> dict[str, Any]:
    """Download a release zip and unzip into the user Extensions dir. Never raises.

    Accepts a catalog name, ``owner/repo`` shorthand, or a direct https .zip URL.
    Manual-kind entries refuse honestly with the repo pointer (no guessed URLs).
    """
    from . import toolbox as _toolbox

    dest_root = primary_extensions_dir(create=True)
    if dest_root is None:
        return {
            "success": False,
            "error": "No Ghidra user dir found (start Ghidra once so %APPDATA%/ghidra/ghidra_*_PUBLIC exists).",
        }
    target = _resolve_target(name_or_url)
    if target["kind"] == "unknown":
        known = sorted(_CATALOG_BY_NAME)
        return {
            "success": False,
            "error": f"Unknown extension '{name_or_url}'. Known: {', '.join(known)} or owner/repo or https .zip URL.",
        }
    if target["kind"] == "manual":
        entry = target["entry"]
        return {
            "success": False,
            "needs_manual": True,
            "name": entry["name"],
            "repo": entry["repo"],
            "error": f"'{entry['name']}' has no prebuilt release asset tracked - install from https://github.com/{entry['repo']} per its docs.",
        }
    if target["kind"] == "catalog":
        entry = target["entry"]
        asset = _toolbox._github_asset(entry["repo"], entry["asset_pattern"], version)
        if "error" in asset:
            return {"success": False, "name": entry["name"], **asset}
        url, name = asset["url"], entry["name"]
    elif target["kind"] == "repo":
        asset = _toolbox._github_asset(target["repo"], r".*\.zip$", version)
        if "error" in asset:
            return {"success": False, "name": target["name"], **asset}
        url, name = asset["url"], target["name"]
    else:
        url, name = target["url"], target["name"]

    tmp = Path(os.environ.get("TEMP", r"C:\\Windows\\Temp")) / f"ghidra-ext-{name}.zip"
    dl = _toolbox._download(url, tmp)
    if "error" in dl:
        return {"success": False, "name": name, **dl}
    dest = dest_root / name
    try:
        if dest.is_dir():
            return {
                "success": False,
                "name": name,
                "error": f"Already installed at {dest} - remove first or update (delete + reinstall).",
            }
        with zipfile.ZipFile(tmp) as z:
            top = {p.split("/")[0].split("\\")[0] for p in z.namelist() if p.strip()}
            sole = next(iter(top))
            if len(top) == 1 and (sole.lower() not in ("", ".")):
                z.extractall(dest_root)
                extracted = dest_root / sole
                if extracted != dest:
                    shutil.move(str(extracted), str(dest))
            else:
                dest.mkdir(parents=True, exist_ok=True)
                z.extractall(dest)
        tmp.unlink(missing_ok=True)
    except Exception as e:
        logger.warning("extension install %s failed: %s", name, e)
        return {"success": False, "name": name, "error": f"extract failed: {e}"}
    row = _fingerprint(dest)
    return {
        "success": True,
        "name": name,
        "path": str(dest),
        "url": url,
        "manifest": row,
        "message": f"Installed '{name}'. Enable in Ghidra via File > Install Extensions, then restart.",
    }


def remove_extension(name: str, confirm: bool = False) -> dict[str, Any]:
    """Delete an installed extension dir. Destructive: needs confirm=True. Never raises."""
    if not confirm:
        return {"success": False, "needs_confirm": True, "error": f"Refusing to delete '{name}' without confirm=True."}
    base = (name or "").strip().removesuffix(".disabled")
    if not base or base in (".", "..") or "/" in base or "\\" in base:
        return {"success": False, "error": f"Refusing odd extension name: {name!r}."}
    for ext_root in user_extensions_dirs():
        for cand in (ext_root / base, ext_root / f"{base}.disabled"):
            if cand.is_dir():
                try:
                    shutil.rmtree(cand)
                    return {
                        "success": True,
                        "name": base,
                        "removed": str(cand),
                        "message": f"Removed '{cand.name}'. Restart Ghidra to pick it up.",
                    }
                except Exception as e:
                    return {"success": False, "name": base, "error": str(e)[:300]}
    return {
        "success": False,
        "error": f"Extension '{name}' not found in {len(user_extensions_dirs())} Extensions dir(s).",
    }


def set_enabled(name: str, enabled: bool = True) -> dict[str, Any]:
    """Enable/disable via rename (<name> <-> <name>.disabled). Reversible, never raises."""
    base = (name or "").strip().removesuffix(".disabled")
    if not base or "/" in base or "\\" in base:
        return {"success": False, "error": f"Refusing odd extension name: {name!r}."}
    for ext_root in user_extensions_dirs():
        on, off = ext_root / base, ext_root / f"{base}.disabled"
        src, dst = (off, on) if enabled else (on, off)
        if src.is_dir() and not dst.exists():
            try:
                src.rename(dst)
                state = "enabled" if enabled else "disabled"
                return {
                    "success": True,
                    "name": base,
                    "enabled": enabled,
                    "path": str(dst),
                    "message": f"'{base}' {state}. Restart Ghidra to pick it up.",
                }
            except Exception as e:
                return {"success": False, "name": base, "error": str(e)[:300]}
        if (on if enabled else off).is_dir():
            return {
                "success": True,
                "name": base,
                "enabled": enabled,
                "path": str(on if enabled else off),
                "message": f"'{base}' already {'enabled' if enabled else 'disabled'}.",
            }
    return {"success": False, "error": f"Extension '{name}' not found."}
