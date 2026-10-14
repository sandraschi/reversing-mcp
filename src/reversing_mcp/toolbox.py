"""Toolbox: autodiscovery, auto-install, autostart for the disassembly toolchain.

Sandra's rule: no hand-editing env, no manual installs. The backend discovers
every tool on boot (PATH, env, fleet dir, standard locations), exports what it
finds into its own environment, installs what is missing (winget / GitHub
releases / pip venv - never silently), and starts policy-enabled services.
License-gated tools (Hopper, IDA) get discovery + onboarding, not piracy.

Layout: everything third-party lives under ``D:\\Dev\\tools`` (outside any
``uv sync`` reach). Per-tool state: ready | missing | broken | license |
platform_blocked.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from .logging_config import get_logger

logger = get_logger("reversing_mcp.toolbox")

TOOLS_ROOT = Path(r"D:\Dev\tools")
WINGET = r"C:\Users\sandr\AppData\Local\Microsoft\WindowsApps\winget.exe"

_POLICY: dict[str, Any] = {"reva_headless": True}
_POLICY_LOCK = threading.RLock()


# ---------------------------------------------------------------------------
# detectors (fast, no spawn, never raise)


def _version_of(exe: str, args: list[str] | None = None, pattern: str | None = None) -> str | None:
    try:
        out = subprocess.run([exe, *(args or ["--version"])], capture_output=True, text=True, timeout=15)
        text = (out.stdout + out.stderr).strip().splitlines()
        line = text[0] if text else ""
        if pattern:
            m = re.search(pattern, line)
            return m.group(1) if m else (line[:60] or None)
        return line[:60] or None
    except (subprocess.SubprocessError, OSError, IndexError) as e:
        logger.debug("version probe %s failed: %s", exe, e)
        return None


def _ghidra_candidates() -> list[Path]:
    cands: list[Path] = []
    for key in ("GHIDRA_INSTALL_DIR", "GHIDRA_HOME"):
        if os.environ.get(key):
            cands.append(Path(os.environ[key]))
    cands += [
        TOOLS_ROOT / "ghidra_12.1.3_PUBLIC",
        Path(r"C:\Program Files\ghidra_12.1.3_PUBLIC"),
        Path(r"C:\Program Files\ghidra_12.0_PUBLIC"),
    ]
    cands += sorted(Path(r"C:\Program Files").glob("ghidra_*_PUBLIC"))
    cands += sorted(TOOLS_ROOT.glob("ghidra_*_PUBLIC"))
    return cands


def detect_ghidra() -> dict[str, Any]:
    for base in _ghidra_candidates():
        if not base.is_dir():
            continue
        run = base / "ghidraRun.bat"
        if not run.is_file():
            run = base / "support" / "ghidraRun.bat"
        headless = base / "support" / "analyzeHeadless.bat"
        if not headless.is_file():
            continue
        version = "?"
        props = base / "Ghidra" / "application.properties"
        try:
            for line in props.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("application.version="):
                    version = line.split("=", 1)[1].strip()
        except OSError:
            pass
        return {
            "status": "ready",
            "path": str(base),
            "version": version,
            "run_bat": str(run) if run.is_file() else None,
            "analyze_headless": str(headless),
        }
    return {"status": "missing", "path": None, "version": None, "install": "github:NationalSecurityAgency/ghidra"}


def detect_reva() -> dict[str, Any]:
    from .reva import find_mcp_reva

    exe = find_mcp_reva()
    if exe:
        return {
            "status": "ready",
            "path": exe,
            "version": _version_of(exe, ["--version"]),
            "install": None,
        }
    return {"status": "missing", "path": None, "version": None, "install": "pip:reverse-engineering-assistant"}


def detect_capa() -> dict[str, Any]:
    from .engines import find_capa

    exe = find_capa()
    if exe:
        return {
            "status": "ready",
            "path": exe,
            "version": _version_of(exe, ["--version"], r"(\d[\d.]*)"),
            "install": None,
        }
    cands = [TOOLS_ROOT / "capa" / "capa.exe"]
    for c in cands:
        if c.is_file():
            return {"status": "ready", "path": str(c), "version": None, "install": None}
    return {"status": "missing", "path": None, "version": None, "install": "github:mandiant/capa"}


def detect_die() -> dict[str, Any]:
    from .engines import find_diec

    exe = find_diec()
    if exe:
        return {"status": "ready", "path": exe, "version": _version_of(exe, ["--version"]), "install": None}
    return {"status": "missing", "path": None, "version": None, "install": "github:horsicq/DIE-engine"}


def detect_frida() -> dict[str, Any]:
    from .engines import check_frida

    info = check_frida()
    if info.get("available"):
        return {"status": "ready", "path": info.get("path"), "version": info.get("version"), "install": None}
    return {"status": "missing", "path": None, "version": None, "install": "pip:frida"}


def detect_r2() -> dict[str, Any]:
    for name in ("radare2", "r2", "rizin"):
        exe = shutil.which(name)
        if exe:
            return {"status": "ready", "path": exe, "version": _version_of(exe, ["-v"], r"(\d[\d.]*)"), "install": None}
    return {"status": "missing", "path": None, "version": None, "install": "winget:RizinOrg.Rizin"}


def detect_hopper() -> dict[str, Any]:
    import platform

    if platform.system() == "Windows":
        return {
            "status": "platform_blocked",
            "path": None,
            "version": None,
            "install": None,
            "note": "Hopper ships macOS/Linux builds only. See docs/HOPPER.md.",
        }
    live = _running_process(("hopper", "Hopper Disassembler v4"))
    if live:
        return {
            "status": "ready",
            "path": live.get("exe"),
            "version": None,
            "pid": live.get("pid"),
            "install": None,
            "note": "Running instance detected - glomming on.",
        }
    for p in ("/Applications/Hopper Disassembler v4.app", "/usr/local/bin/hopper"):
        if Path(p).exists():
            return {"status": "ready", "path": p, "version": None, "install": None}
    return {
        "status": "missing",
        "path": None,
        "version": None,
        "install": None,
        "note": "No running Hopper and none installed. See docs/HOPPER.md.",
    }


def _running_process(names: tuple[str, ...]) -> dict[str, Any] | None:
    """Glom check: is one of these executables alive right now? Never raises."""
    try:
        import psutil

        wanted = {n.lower() for n in names}
        for p in psutil.process_iter(["pid", "name", "exe"]):
            try:
                pname = (p.info.get("name") or "").lower()
                if pname in wanted:
                    return {"pid": p.info["pid"], "exe": p.info.get("exe")}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except ImportError as e:
        logger.debug("psutil unavailable for process scan: %s", e)
    except Exception as e:
        logger.debug("process scan failed: %s", e)
    return None


def detect_ida() -> dict[str, Any]:
    """IDA: a running instance wins (glom on), install path second, absence third.

    Licensing is the user's business, not the detector's.
    """
    live = _running_process(("ida64.exe", "ida.exe", "idag64.exe", "idaw.exe"))
    if live:
        return {
            "status": "ready",
            "path": live.get("exe"),
            "version": None,
            "pid": live.get("pid"),
            "install": None,
            "note": "Running instance detected - glomming on. See docs/IDA.md for attach.",
        }
    cands: list[Path] = []
    if os.environ.get("IDA_DIR"):
        cands.append(Path(os.environ["IDA_DIR"]))
    cands += [
        Path(r"C:\Program Files\IDA Pro 9.0\ida64.exe"),
        Path(r"C:\Program Files\IDA Free\ida.exe"),
    ]
    for c in cands:
        if c.is_file():
            return {"status": "ready", "path": str(c), "version": None, "install": None}
        if c.is_dir() and (c / "ida64.exe").is_file():
            return {"status": "ready", "path": str(c / "ida64.exe"), "version": None, "install": None}
    return {
        "status": "missing",
        "path": None,
        "version": None,
        "install": None,
        "note": "No running IDA and no install found. Start IDA or set IDA_DIR. See docs/IDA.md.",
    }


def detect_java() -> dict[str, Any]:
    exe = shutil.which("java")
    if not exe:
        return {"status": "missing", "path": None, "version": None, "install": "winget:EclipseAdoptium.Temurin.21.JDK"}
    ver = _version_of(exe, ["-version"], r'"(\d+)[.\"]')
    try:
        major = int((ver or "0").split(".")[0])
    except ValueError:
        major = 0
    if major and major < 17:
        return {"status": "broken", "path": exe, "version": ver, "install": None, "note": "Ghidra needs Java 17+."}
    return {"status": "ready", "path": exe, "version": ver, "install": None}


def detect_tesseract() -> dict[str, Any]:
    from .clickerlab import _TESSERACT_EXE

    if Path(_TESSERACT_EXE).is_file():
        return {"status": "ready", "path": _TESSERACT_EXE, "version": None, "install": None}
    return {"status": "missing", "path": None, "version": None, "install": "winget:UB-Mannheim.TesseractOCR"}


def detect_node() -> dict[str, Any]:
    exe = shutil.which("node")
    if exe:
        return {"status": "ready", "path": exe, "version": _version_of(exe, ["--version"]), "install": None}
    return {"status": "missing", "path": None, "version": None, "install": "winget:OpenJS.NodeJS.LTS"}


def detect_ollama() -> dict[str, Any]:
    """Ollama in three states: serving (:11434) > installed (exe/process) > missing.

    The dashboard used to report installed-but-idle as 'no Ollama' - wrong
    prescription (install what's already there). States drive Start vs Install.
    """
    import httpx

    try:
        r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=3)
        if r.status_code == 200:
            n = len(r.json().get("models", []))
            return {
                "status": "ready",
                "path": None,
                "version": None,
                "install": None,
                "note": f"serving with {n} model(s)",
            }
    except Exception as e:
        logger.debug("ollama probe failed: %s", e)
    cands = [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"]
    which = shutil.which("ollama")
    if which:
        cands.insert(0, Path(which))
    for c in cands:
        if c.is_file():
            return {
                "status": "installed",
                "path": str(c),
                "version": _version_of(str(c), ["--version"]),
                "install": None,
                "note": "installed but not serving - start it, don't reinstall",
            }
    if _running_process(("ollama app", "ollama app.exe", "ollama.exe")):
        return {
            "status": "installed",
            "path": None,
            "version": None,
            "install": None,
            "note": "process seen but exe not located - start via the app",
        }
    return {"status": "missing", "path": None, "version": None, "install": "winget:Ollama.Ollama"}


def start_ollama() -> dict[str, Any]:
    """Launch `ollama serve` detached. Idempotent-ish: serving already → ok."""
    state = detect_ollama()
    if state["status"] == "ready":
        return {"success": True, "message": f"Ollama already serving ({state.get('note')})."}
    exe = state.get("path") or shutil.which("ollama")
    if not exe:
        return {"success": False, "error": "Ollama not installed - install it first (toolbox install ollama)."}
    try:
        subprocess.Popen(
            [exe, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
        )
        logger.info("ollama serve launched")
        return {"success": True, "message": "Ollama starting - the dashboard cue clears when :11434 answers."}
    except (subprocess.SubprocessError, OSError) as e:
        return {"success": False, "error": str(e)[:300]}


def pull_ollama_model(model: str) -> dict[str, Any]:
    """`ollama pull` in a background thread (GBs take minutes). Never raises."""
    state = detect_ollama()
    exe = state.get("path") or shutil.which("ollama")
    if not exe:
        return {"success": False, "error": "Ollama not installed."}
    if state["status"] != "ready":
        return {"success": False, "error": "Ollama not serving - start it first."}
    if not model or not re.fullmatch(r"[A-Za-z0-9][\w\-.:/]*", model):
        return {"success": False, "error": f"Refusing odd model name: {model!r}."}

    def _pull() -> None:
        try:
            proc = subprocess.run([exe, "pull", model], capture_output=True, text=True, timeout=3600)
            logger.info("ollama pull %s exited %s", model, proc.returncode)
        except (subprocess.SubprocessError, OSError) as e:
            logger.warning("ollama pull %s failed: %s", model, e)

    threading.Thread(target=_pull, name=f"ollama-pull-{model}", daemon=True).start()
    return {"success": True, "message": f"Pulling {model} in the background - watch /api/llm/discover."}


DETECTORS = {
    "ghidra": detect_ghidra,
    "reva": detect_reva,
    "capa": detect_capa,
    "die": detect_die,
    "frida": detect_frida,
    "r2": detect_r2,
    "hopper": detect_hopper,
    "ida": detect_ida,
    "java": detect_java,
    "tesseract": detect_tesseract,
    "node": detect_node,
    "ollama": detect_ollama,
}


def probe() -> dict[str, Any]:
    """Full toolbox inventory. Fast, no spawns except --version probes. Never raises."""
    tools = {}
    for name, fn in DETECTORS.items():
        try:
            tools[name] = {"name": name, **fn()}
        except Exception as e:
            tools[name] = {"name": name, "status": "broken", "error": str(e)[:200]}
    ready = sum(1 for t in tools.values() if t["status"] == "ready")
    return {
        "success": True,
        "tools": tools,
        "ready": ready,
        "total": len(tools),
        "message": f"Toolbox: {ready}/{len(tools)} ready.",
    }


# ---------------------------------------------------------------------------
# installers (may download/build; run off the event loop; never raise)


def _https_open(url: str, timeout_s: int):
    """urlopen restricted to https (S310: no file/custom schemes)."""
    from urllib.parse import urlparse

    if urlparse(url).scheme != "https":
        raise ValueError(f"refusing non-https URL: {url[:80]}")
    # Scheme allowlisted to https above (S310 justified on both calls).
    req = urllib.request.Request(  # noqa: S310
        url, headers={"User-Agent": "reversing-mcp-toolbox", "Accept": "application/vnd.github+json"}
    )
    return urllib.request.urlopen(req, timeout=timeout_s)  # noqa: S310


def _github_asset(repo: str, name_pattern: str, version: str | None = None) -> dict[str, Any]:
    """Find a release asset URL. version=None means latest."""
    api = f"https://api.github.com/repos/{repo}/releases/{'tags/' + version if version else 'latest'}"
    try:
        with _https_open(api, 30) as r:
            rel = json.loads(r.read().decode("utf-8", errors="replace"))
        for a in rel.get("assets", []):
            if re.search(name_pattern, a.get("name", ""), re.IGNORECASE):
                return {"url": a["browser_download_url"], "name": a["name"], "tag": rel.get("tag_name")}
        return {"error": f"no asset matching {name_pattern} in {repo} {version or 'latest'}"}
    except Exception as e:
        return {"error": f"GitHub API failed for {repo}: {e}"}


def _download(url: str, dest: Path, timeout_s: int = 900) -> dict[str, Any]:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with _https_open(url, timeout_s) as r, dest.open("wb") as f:
            shutil.copyfileobj(r, f, length=1024 * 256)
        return {"path": str(dest), "bytes": dest.stat().st_size}
    except Exception as e:
        return {"error": f"download failed: {e}"}


def _winget_install(package_id: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [
                WINGET,
                "install",
                "--id",
                package_id,
                "-e",
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if proc.returncode == 0:
            return {"success": True, "message": f"winget installed {package_id}"}
        return {"success": False, "error": (proc.stderr or proc.stdout)[-500:]}
    except (subprocess.SubprocessError, OSError) as e:
        return {"success": False, "error": str(e)[:300]}


def install_ghidra(version: str = "12.1.3") -> dict[str, Any]:
    """Download + extract Ghidra to the fleet tools dir (no admin needed)."""
    dest_dir = TOOLS_ROOT / f"ghidra_{version}_PUBLIC"
    if (dest_dir / "support" / "analyzeHeadless.bat").is_file():
        return {"success": True, "path": str(dest_dir), "message": f"Ghidra {version} already installed."}
    asset = _github_asset("NationalSecurityAgency/ghidra", rf"ghidra_{re.escape(version)}_PUBLIC.*\.zip")
    if "error" in asset:
        return {"success": False, **asset}
    tmp = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / f"ghidra-{version}.zip"
    dl = _download(asset["url"], tmp)
    if "error" in dl:
        return {"success": False, **dl}
    try:
        with zipfile.ZipFile(tmp) as z:
            z.extractall(dest_dir)
        inner = dest_dir / f"ghidra_{version}_PUBLIC"
        if inner.is_dir():
            for child in inner.iterdir():
                shutil.move(str(child), dest_dir)
            inner.rmdir()
        tmp.unlink(missing_ok=True)
    except Exception as e:
        return {"success": False, "error": f"extract failed: {e}"}
    ok = (dest_dir / "support" / "analyzeHeadless.bat").is_file()
    return {
        "success": ok,
        "path": str(dest_dir),
        "message": f"Ghidra {version} installed." if ok else "Extract layout unexpected.",
    }


def install_reva() -> dict[str, Any]:
    """Codified fleet install: own venv + pip + compat shim (see D:/Dev/tools/reva/README.md)."""
    from .reva import REVA_HOME

    venv_py = REVA_HOME / ".venv" / "Scripts" / "python.exe"
    uv = shutil.which("uv") or r"C:\Users\sandr\.local\bin\uv.exe"
    try:
        if not venv_py.is_file():
            proc = subprocess.run(
                [uv, "venv", "--python", "3.12", str(REVA_HOME / ".venv")],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if proc.returncode != 0:
                return {"success": False, "error": f"venv failed: {(proc.stderr or proc.stdout)[-400:]}"}
        proc = subprocess.run(
            [uv, "pip", "install", "--python", str(venv_py), "reverse-engineering-assistant==7.3.1"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if proc.returncode != 0:
            return {"success": False, "error": f"pip failed: {(proc.stderr or proc.stdout)[-400:]}"}
    except (subprocess.SubprocessError, OSError) as e:
        return {"success": False, "error": str(e)[:300]}
    site = REVA_HOME / ".venv" / "Lib" / "site-packages"
    compat = site / "reva_mcp_compat.py"
    if not compat.is_file():
        return {
            "success": False,
            "error": "pip done but the MCP-SDK compat shim is missing - rerun the documented patch (D:/Dev/tools/reva/README.md).",
        }
    return {
        "success": True,
        "path": str(REVA_HOME / ".venv" / "Scripts" / "mcp-reva.exe"),
        "message": "ReVa venv ready (compat shim present). Extension install is separate - see probe.",
    }


def install_capa() -> dict[str, Any]:
    """Standalone capa.exe from mandiant/capa releases into the fleet tools dir."""
    dest = TOOLS_ROOT / "capa" / "capa.exe"
    if dest.is_file():
        return {"success": True, "path": str(dest), "message": "capa already installed."}
    asset = _github_asset("mandiant/capa", r"capa-.*windows-64\.exe$")
    if "error" in asset:
        return {"success": False, **asset}
    dl = _download(asset["url"], dest)
    if "error" in dl:
        return {"success": False, **dl}
    return {"success": True, "path": str(dest), "message": f"capa installed ({asset['name']})."}


def install_die() -> dict[str, Any]:
    """Detect-It-Easy portable zip from horsicq/DIE-engine releases."""
    dest_dir = TOOLS_ROOT / "die"
    if (dest_dir / "diec.exe").is_file() or (dest_dir / "die" / "diec.exe").is_file():
        return {"success": True, "path": str(dest_dir), "message": "DiE already installed."}
    asset = _github_asset("horsicq/DIE-engine", r"die_win64_portable.*\.zip$")
    if "error" in asset:
        return {"success": False, **asset}
    tmp = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / "die-portable.zip"
    dl = _download(asset["url"], tmp)
    if "error" in dl:
        return {"success": False, **dl}
    try:
        with zipfile.ZipFile(tmp) as z:
            z.extractall(dest_dir)
        tmp.unlink(missing_ok=True)
    except Exception as e:
        return {"success": False, "error": f"extract failed: {e}"}
    return {"success": True, "path": str(dest_dir), "message": "DiE installed."}


INSTALLERS = {
    "ghidra": install_ghidra,
    "reva": install_reva,
    "capa": install_capa,
    "die": install_die,
}


def install(name: str) -> dict[str, Any]:
    """Install one toolbox entry. Winget/pip kinds handled generically; the rest refuse honestly."""
    name = (name or "").lower()
    if name in INSTALLERS:
        try:
            out = INSTALLERS[name]()
            out["tool"] = name
            if "success" not in out:
                out["success"] = True
            return out
        except Exception as e:
            logger.exception("toolbox install %s failed", name)
            return {"success": False, "tool": name, "error": str(e)[:300]}
    inv = probe()["tools"].get(name)
    if inv is None:
        return {"success": False, "error": f"Unknown toolbox entry '{name}'."}
    kind = inv.get("install") or ""
    if kind.startswith("winget:"):
        out = _winget_install(kind.split(":", 1)[1])
        out["tool"] = name
        return out
    if kind.startswith("pip:"):
        pkg = kind.split(":", 1)[1]
        uv = shutil.which("uv") or r"C:\Users\sandr\.local\bin\uv.exe"
        try:
            proc = subprocess.run([uv, "pip", "install", "--system", pkg], capture_output=True, text=True, timeout=600)
            ok = proc.returncode == 0
            return {
                "success": ok,
                "tool": name,
                "message": f"pip installed {pkg}" if ok else f"pip failed: {(proc.stderr or proc.stdout)[-400:]}",
            }
        except (subprocess.SubprocessError, OSError) as e:
            return {"success": False, "tool": name, "error": str(e)[:300]}
    if name in ("hopper", "ida"):
        return {
            "success": False,
            "tool": name,
            "error": f"{name} has no silent installer. {inv.get('note', 'Start it or set its DIR env; the toolbox gloms onto running instances.')} See docs/ONBOARDING.md.",
        }
    if name == "java":
        return _winget_install("EclipseAdoptium.Temurin.21.JDK") | {"tool": name}
    return {"success": False, "tool": name, "error": f"No installer for '{name}' (status={inv.get('status')})."}


# ---------------------------------------------------------------------------
# policy + ensure (boot path: discover, export env, start policy services)


def get_policy() -> dict[str, Any]:
    with _POLICY_LOCK:
        return {"success": True, "policy": dict(_POLICY)}


def set_policy(updates: dict[str, Any]) -> dict[str, Any]:
    with _POLICY_LOCK:
        for k, v in (updates or {}).items():
            if k in _POLICY:
                _POLICY[k] = bool(v)
        return {"success": True, "policy": dict(_POLICY)}


def ensure(autostart: bool = True) -> dict[str, Any]:
    """Boot path: probe, export discovered locations into this process env,
    start policy services. Idempotent; never raises."""
    inv = probe()
    tools = inv["tools"]
    exported = []
    ghidra = tools.get("ghidra", {})
    if ghidra.get("status") == "ready" and ghidra.get("path"):
        if not os.environ.get("GHIDRA_INSTALL_DIR"):
            os.environ["GHIDRA_INSTALL_DIR"] = ghidra["path"]
            exported.append("GHIDRA_INSTALL_DIR")
    die = tools.get("die", {})
    if die.get("status") == "ready" and die.get("path"):
        d = str(Path(die["path"]).parent)
        if d not in os.environ.get("PATH", "") and not os.environ.get("DIE_DIR"):
            os.environ["DIE_DIR"] = d
            exported.append("DIE_DIR")
    started: dict[str, Any] = {}
    if autostart:
        with _POLICY_LOCK:
            want_reva = bool(_POLICY.get("reva_headless"))
        if want_reva:
            from . import reva as _reva

            st = _reva._managed()
            if not st.get("running"):
                # Declared boot policy (logged), not surprise execution: the desktop
                # already runs the backend; headless mcp-reva touches no mouse/keys.
                res = _reva.start(
                    mode="headless",
                    confirm=True,
                    bridge_url=os.environ.get("GHIDRA_BRIDGE_URL", "http://127.0.0.1:8089"),
                )
                started["reva_headless"] = {
                    "ok": bool(res.get("success")),
                    "pid": res.get("pid"),
                    "note": res.get("message") or res.get("error"),
                }
                logger.info("toolbox autostart reva_headless: %s", started["reva_headless"])
            else:
                started["reva_headless"] = {"ok": True, "pid": st.get("pid"), "note": "already running"}
    return {
        "success": True,
        "ready": inv["ready"],
        "total": inv["total"],
        "exported_env": exported,
        "started": started,
        "message": f"Toolbox ensure: {inv['ready']}/{inv['total']} ready, env={exported}, started={list(started)}.",
    }
