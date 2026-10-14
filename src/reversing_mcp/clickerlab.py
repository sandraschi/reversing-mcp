"""ClickerLab: Gym stage 1b (elicitation) + stage 3 (clicker tour).

Spec: docs/GYM_SPEC.md sections 2b/2c. Playbook: docs/ELICITATION_AND_CLICKER.md.
Build order: G1b (no VM, static only) then G3 (executes the target).

Stage 1b is pure static analysis over triage artifacts - safe to run any time.
It writes ``elicitation/`` into the run directory: ``formats/*.md`` stubs,
``features.json``, ``tour-draft.yaml`` and ``prior-art.md``.

Stage 3 executes the target binary. Safety contract (spec section 1 + 7):

- Sessions require ``confirm=True`` (like ``engine`` frida_* ops).
- The clicker belongs in an isolated VM (virtualization-mcp, snapshot before,
  no network, no credentials). Running on this desktop needs an explicit,
  per-session ``accept_local=True`` which is recorded in the session log.
- Step cap (default 200) + wall-clock cap (default 600 s); stop kills the
  whole target process tree via :func:`engines.kill_tree`.
- UIA driving needs ``pywinauto`` (``uv sync --extra clicker``); screenshots
  need ``Pillow``. Both are lazy imports - without them the session refuses
  honestly instead of pretending.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from . import engines
from .logging_config import get_logger

logger = get_logger("reversing_mcp.clickerlab")

# ---------------------------------------------------------------------------
# Shared helpers


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


#: Fleet-standard Tesseract location (mirrors scripts/cua-smoke.py).
_TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#: Tour intents that need credentials, payment or identity - never improvised.
#: A step matching one of these is recorded as a named skip, never executed.
FORBIDDEN_INTENT_RES = (
    r"passw",
    r"log.?in|sign.?in|logon",
    r"sign.?up|register|create.?account",
    r"\bpay\b|payment|purchase|buy\b|checkout|credit.?card|billing",
    r"license.?key|activation.?key|serial.?key|product.?key",
    r"\bunlock\b.*\b(paid|license|key)\b",
)


def _tesseract_version() -> str:
    try:
        out = subprocess.run([_TESSERACT_EXE, "--version"], capture_output=True, text=True, timeout=10)
        return (out.stdout.strip().splitlines() or ["?"])[0].split(" ", 1)[-1][:24]
    except (subprocess.SubprocessError, OSError) as e:
        logger.debug("tesseract probe failed: %s", e)
        return "?"


def warn_operator(sdir: Path, mode: str, target: str) -> None:
    """Warn-first banner (fleet CUA rule): the session is about to drive the desktop."""
    banner = (
        "CUA AUTOMATION WARNING: ClickerLab takes control of the mouse and keyboard "
        f"to drive {target} (mode={mode}). Do not touch mouse/keyboard until the session ends."
    )
    logger.warning(banner)
    _slog(sdir, "operator_warning", banner)


def release_mouse() -> None:
    """Release all mouse buttons + dismiss stray context menus (fleet CUA rule).

    UIA click_input() on some controls fires through Invoke rather than a true
    synthetic click, which can surface as a context menu - Escape clears it.
    """
    try:
        import ctypes

        for flag in (0x0004, 0x0010, 0x0040):  # LEFTUP, RIGHTUP, MIDDLEUP
            ctypes.windll.user32.mouse_event(flag, 0, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x1B, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x1B, 0, 0x0002, 0)
    except Exception as e:
        logger.debug("release_mouse failed: %s", e)


def ocr_image(path: Path) -> str:
    """OCR one screenshot file. Empty string when OCR is unavailable."""
    try:
        import pytesseract
        from PIL import Image

        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_EXE
        return pytesseract.image_to_string(Image.open(path))
    except Exception as e:
        logger.debug("OCR failed for %s: %s", path.name, e)
        return ""


def ocr_regions(path: Path, min_conf: int = 40) -> list[dict[str, Any]]:
    """B3 target proposals: text blobs with coordinates (for canvas-rendered UI)."""
    try:
        import pytesseract
        from PIL import Image

        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_EXE
        data = pytesseract.image_to_data(Image.open(path), output_type=pytesseract.Output.DICT)
    except Exception as e:
        logger.debug("OCR regions failed for %s: %s", path.name, e)
        return []
    out = []
    n = len(data.get("text", []))
    for i in range(n):
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            continue
        text = (data["text"][i] or "").strip()
        if conf < min_conf or len(text) < 2:
            continue
        out.append(
            {
                "text": text[:80],
                "conf": round(conf, 1),
                "x": int(data["left"][i]) + int(data["width"][i]) // 2,
                "y": int(data["top"][i]) + int(data["height"][i]) // 2,
                "w": int(data["width"][i]),
                "h": int(data["height"][i]),
            }
        )
    return out


def screenshot_diff_regions(before: Path, after: Path, cell: int = 32) -> list[dict[str, int]]:
    """Changed screen regions between two screenshots (B3 click verification).

    Coarse-cell diff: cells whose mean pixel delta exceeds threshold merge into
    bounding boxes. Deterministic, dependency-light (Pillow only).
    """
    try:
        from PIL import Image, ImageChops, ImageStat
    except ImportError as e:
        logger.debug("Pillow missing for diff: %s", e)
        return []
    try:
        a = Image.open(before).convert("L")
        b = Image.open(after).convert("L")
        size = (min(a.width, b.width), min(a.height, b.height))
        a, b = a.resize(size), b.resize(size)
        diff = ImageChops.difference(a, b)
        w, h = size
        hot: list[tuple[int, int]] = []
        for cy in range(0, h, cell):
            for cx in range(0, w, cell):
                box = (cx, cy, min(cx + cell, w), min(cy + cell, h))
                if ImageStat.Stat(diff.crop(box)).mean[0] > 12:
                    hot.append((cx, cy))
        if not hot:
            return []
        # Merge adjacent hot cells into boxes (single-pass union on the grid).
        boxes: list[list[int]] = []
        for cx, cy in hot:
            placed = False
            for box in boxes:
                if (
                    cx <= box[2] + cell
                    and cy <= box[3] + cell
                    and cx + cell >= box[0] - cell
                    and cy + cell >= box[1] - cell
                ):
                    box[0] = min(box[0], cx)
                    box[1] = min(box[1], cy)
                    box[2] = max(box[2], cx + cell)
                    box[3] = max(box[3], cy + cell)
                    placed = True
                    break
            if not placed:
                boxes.append([cx, cy, cx + cell, cy + cell])
        return [{"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0} for x0, y0, x1, y1 in boxes]
    except Exception as e:
        logger.debug("screenshot diff failed: %s", e)
        return []


def read_clipboard_text() -> str:
    """Capture text clipboard (per-step capture bundle). Empty when unavailable."""
    try:
        import win32clipboard

        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                return (win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT) or "")[:4000]
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        logger.debug("clipboard read failed: %s", e)
    return ""


def snapshot_files(dirs: list[Path], max_files: int = 20000) -> tuple[dict[str, dict[str, int]], bool]:
    """File inventory (path -> {size, mtime_ns}) for watch dirs + truncated flag.

    Budgeted: stops after max_files entries so a bloated %TEMP% cannot stall a
    pass (live-fire lesson 2026-10-14: unbounded rglob took ~55 s per rip pass).
    The flag is carried into every diff record so a capped snapshot never
    silently poses as complete.
    """
    snap: dict[str, dict[str, int]] = {}
    truncated = False
    for d in dirs:
        try:
            for p in d.rglob("*"):
                if len(snap) >= max_files:
                    truncated = True
                    break
                try:
                    if p.is_file() and not p.is_symlink():
                        st = p.stat()
                        snap[str(p)] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns}
                except OSError:
                    continue
        except OSError as e:
            logger.debug("watch dir %s unreadable: %s", d, e)
    return snap, truncated


def diff_files(before: dict[str, dict[str, int]], after: dict[str, dict[str, int]]) -> dict[str, list[str]]:
    """Added / modified / removed files between two snapshots."""
    added = sorted(p for p in after if p not in before)
    removed = sorted(p for p in before if p not in after)
    modified = sorted(p for p in after if p in before and after[p] != before[p])
    return {"added": added[:100], "modified": modified[:100], "removed": removed[:100]}


def snapshot_registry(hive_path: str = r"HKCU\Software") -> Path | None:
    """Export a registry subtree to a temp .reg file (session-level diffing)."""
    try:
        out = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / f"clickerlab-reg-{uuid.uuid4().hex[:8]}.reg"
        proc = subprocess.run(["reg", "export", hive_path, str(out), "/y"], capture_output=True, text=True, timeout=120)
        if proc.returncode == 0 and out.is_file():
            return out
        logger.debug("reg export failed: %s", proc.stderr[:200])
    except (subprocess.SubprocessError, OSError) as e:
        logger.debug("reg export failed: %s", e)
    return None


def classify_step(step: dict[str, Any]) -> dict[str, Any]:
    """Tour allowlist gate: forbidden steps become named skips, never execution."""
    blob = json.dumps(step.get("action", ""), default=str)
    for pat in FORBIDDEN_INTENT_RES:
        if re.search(pat, blob, re.IGNORECASE):
            return {
                "allowed": False,
                "skip_name": f"forbidden:{pat}",
                "reason": "Step needs credentials/payment/identity - improvising is forbidden (Tier 3 section 3).",
            }
    return {"allowed": True, "skip_name": None, "reason": None}


def jlog(sdir: Path, record: dict[str, Any]) -> None:
    """Append one JSONL capture record (Tier 3 bundle: one record per step)."""
    with (sdir / "tour.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now(), **record}, default=str) + "\n")


def clicker_engines() -> dict[str, Any]:
    """Probe the optional G3 driver stack. Never raises."""
    out: dict[str, Any] = {}
    try:
        import pywinauto

        out["pywinauto"] = {"available": True, "version": getattr(pywinauto, "__version__", "unknown")}
    except ImportError:
        out["pywinauto"] = {"available": False, "install_hint": "uv sync --extra clicker  (pywinauto>=0.6.8)"}
    try:
        import PIL

        out["pillow"] = {"available": True, "version": getattr(PIL, "__version__", "unknown")}
    except ImportError:
        out["pillow"] = {"available": False, "install_hint": "uv sync --extra clicker  (Pillow>=10)"}
    try:
        import yaml  # noqa: F401

        out["yaml"] = {"available": True}
    except ImportError:  # pragma: no cover - pyyaml ships with most stacks
        out["yaml"] = {"available": False, "install_hint": "pip install pyyaml"}
    try:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_EXE
        out["ocr"] = {
            "available": Path(_TESSERACT_EXE).is_file(),
            "backend": f"pytesseract + Tesseract {_tesseract_version()}",
        }
    except ImportError:
        out["ocr"] = {"available": False, "install_hint": "uv sync --extra clicker  (pytesseract>=0.3.10)"}
    drive_ready = bool(out["pywinauto"]["available"])
    ocr_ready = bool(out["ocr"]["available"])
    layers = ["B1 rip" if drive_ready else "B1 rip (needs pywinauto)"]
    layers.append("B3 OCR" if ocr_ready else "B3 OCR (needs Tesseract binary + pytesseract)")
    return {
        "engines": out,
        "drive_ready": drive_ready,
        "ocr_ready": ocr_ready,
        "elicitation_ready": True,
        "layers": layers,
        "message": (
            "Clicker drive ready (pywinauto present)."
            if drive_ready
            else "Elicitation ready; live driving needs uv sync --extra clicker (pywinauto)."
        ),
    }


# ---------------------------------------------------------------------------
# Stage 1b: elicitation (static, no execution)


_EXT_RE = re.compile(r"\.([a-zA-Z0-9]{2,4})\b")
_MAGIC_HITS = (
    "MZ",
    "PK",
    "RIFF",
    "ITSF",
    "%PDF",
    "\x89PNG",
    "SQLite format 3",
    "ID3",
    "OggS",
    "BM",
    "GIF8",
    "II*\x00",
    "MM\x00*",
)
_FORMAT_VERBS = ("format", "codec", "compress", "encrypt", "parser", "import", "export", "filter")
_HELP_WORDS = ("help", "about", "tip", "tutorial", "contents", "index", "search", "manual", "guide", "chm", "pdf")
_FILE_IO_VERBS = ("open", "save", "export", "import", "print", "write", "read", "load", "convert")
_DIALOG_WORDS = ("dialog", "window", "view", "options", "settings", "preferences", "wizard", "panel", "tab")
_DECO_WORDS = ("skin", "theme", "toolbar", "splash", "about", "tip of the day", "tip-of-the-day")

#: Candidate public specs for formats apps commonly touch. Leads, not truth.
KNOWN_SPECS: dict[str, dict[str, str]] = {
    "psd": {
        "name": "Adobe Photoshop file format",
        "url": "https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/",
    },
    "tif": {"name": "TIFF 6.0", "url": "https://www.itu.int/itudoc/itu-t/com16/tiff-fx/docs/tiff6.pdf"},
    "tiff": {"name": "TIFF 6.0", "url": "https://www.itu.int/itudoc/itu-t/com16/tiff-fx/docs/tiff6.pdf"},
    "jpg": {"name": "JPEG (ITU-T T.81)", "url": "https://www.w3.org/Graphics/JPEG/itu-t81.pdf"},
    "jpeg": {"name": "JPEG (ITU-T T.81)", "url": "https://www.w3.org/Graphics/JPEG/itu-t81.pdf"},
    "png": {"name": "PNG (RFC 2083)", "url": "https://www.rfc-editor.org/rfc/rfc2083.txt"},
    "pdf": {"name": "PDF 32000-1:2008", "url": "https://www.iso.org/standard/51502.html"},
    "zip": {"name": "APPNOTE.TXT (PKWARE)", "url": "https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT"},
    "chm": {
        "name": "MS ITSF/CHM (MSDN + 7-Zip/chmlib sources)",
        "url": "https://learn.microsoft.com/en-us/previous-versions/windows/desktop/htmlhelp/",
    },
    "xml": {"name": "XML 1.0 (W3C REC)", "url": "https://www.w3.org/TR/xml/"},
    "xlsx": {
        "name": "ECMA-376 OOXML",
        "url": "https://www.ecma-international.org/publications-and-standards/standards/ecma-376/",
    },
    "docx": {
        "name": "ECMA-376 OOXML",
        "url": "https://www.ecma-international.org/publications-and-standards/standards/ecma-376/",
    },
    "db": {"name": "SQLite file format", "url": "https://www.sqlite.org/fileformat.html"},
    "exe": {
        "name": "PE (MS-DOS header + COFF, MS-X)",
        "url": "https://learn.microsoft.com/en-us/windows/win32/debug/pe-format",
    },
    "dll": {
        "name": "PE (MS-DOS header + COFF, MS-X)",
        "url": "https://learn.microsoft.com/en-us/windows/win32/debug/pe-format",
    },
}


def mine_format_candidates(strings: list[str]) -> list[dict[str, Any]]:
    """Playbook A1: extensions, magic bytes and format names from strings.

    Returns candidates sorted by hit count, each with up to 3 context samples
    (80 chars around the hit, per the playbook).
    """
    ext_hits: dict[str, list[str]] = {}
    for s in strings:
        for m in _EXT_RE.finditer(s):
            ext = m.group(1).lower()
            if ext in ("exe", "dll", "00", "040", "000") or ext.isdigit():
                continue  # version noise (.323, .161) per playbook A1
            start = max(0, m.start() - 80)
            ctx = s[start : m.end() + 80 - (m.end() - m.start())][:160].strip()
            ext_hits.setdefault(ext, []).append(ctx)
            if len(ext_hits[ext]) > 50:
                ext_hits[ext] = ext_hits[ext][:50]

    magic: dict[str, int] = {}
    for s in strings:
        for mark in _MAGIC_HITS:
            if mark in s:
                magic[mark] = magic.get(mark, 0) + 1

    names: dict[str, list[str]] = {}
    for s in strings:
        low = s.lower()
        for verb in _FORMAT_VERBS:
            i = low.find(verb)
            if i >= 0:
                names.setdefault(verb, []).append(s[max(0, i - 80) : i + 80].strip())
                if len(names[verb]) > 20:
                    names[verb] = names[verb][:20]
                break

    candidates = [
        {
            "ext": ext,
            "hits": len(ctxs),
            "samples": ctxs[:3],
            "known_spec": KNOWN_SPECS.get(ext),
            "magic_seen": [m for m in magic if m],
        }
        for ext, ctxs in sorted(ext_hits.items(), key=lambda kv: -len(kv[1]))
    ]
    return candidates[:25]


def _word_hit(title_low: str, words: tuple[str, ...]) -> bool:
    """Word-boundary match: substring hits on short verbs ("read" in "thread")
    mis-prioritise everything into file I/O."""
    return re.search(r"\b(" + "|".join(words) + r")\b", title_low) is not None


def _priority(title_low: str) -> tuple[int, str]:
    if _word_hit(title_low, _FILE_IO_VERBS):
        return 1, "file I/O (oracle + tour first)"
    if _word_hit(title_low, _DIALOG_WORDS):
        return 2, "dialogs and views"
    if _word_hit(title_low, _DECO_WORDS):
        return 3, "decoration"
    return 2, "dialogs and views"


def mine_features(strings: list[str]) -> list[dict[str, Any]]:
    """Playbook A3: every help/menu string becomes one feature row."""
    seen: dict[str, dict[str, Any]] = {}
    for s in strings:
        low = s.lower()
        if len(s) < 4 or len(s) > 120:
            continue
        src = None
        if any(w in low for w in _HELP_WORDS):
            src = "help"
        elif re.search(r"[A-Z][a-z]+(\s+[A-Za-z][a-z]+){0,3}(\.\.\.)?$", s) and any(
            v in low for v in (*_FILE_IO_VERBS, "edit", "view", "tools", "window")
        ):
            src = "menu"
        if src is None:
            continue
        key = re.sub(r"\s+", " ", s).strip(" .&")
        if not key or key.lower() in seen:
            continue
        prio, why = _priority(low)
        seen[key.lower()] = {
            "id": f"f{len(seen) + 1:03d}",
            "title": key[:100],
            "source": src,
            "file_io": prio == 1,
            "priority": prio,
            "why": why,
        }
    feats = sorted(seen.values(), key=lambda f: (f["priority"], f["title"]))
    return feats[:200]


def inventory_help(target: Path) -> dict[str, Any]:
    """Playbook A3 inventory: .chm/.hlp/.pdf beside the EXE."""
    found: list[str] = []
    try:
        for pat in ("*.chm", "*.hlp", "*.pdf", "*manual*", "*help*"):
            for p in target.parent.glob(pat):
                if p.is_file() and p != target:
                    found.append(str(p))
    except OSError:
        pass
    return {
        "beside_exe": sorted(set(found))[:20],
        "note": "CHM is a parseable container (7-Zip extracts; chmlib reads #SYSTEM/#TOPICS) - topic tree becomes features at G1b build time.",
    }


def build_tour_draft(target: str, features: list[dict[str, Any]]) -> str:
    """Playbook A3 tour-YAML draft: priority-1 features become intent steps.

    Intent steps record *what* to reach; the G3 driver resolves live UIA paths
    (docs-seeded ordering, B2). Same schema as scripts/tour/tour.example.yaml.
    """
    lines = [
        f"# Tour draft (elicited {_now()}, status: draft - driver resolves paths live)",
        f"# Target: {target}",
        "target:",
        f"  exe: {json.dumps(target)}",
        "isolation:",
        "  network: off",
        "  credentials: none",
        "  snapshot_before: true",
        "steps:",
        "  - id: launch",
        "    action: launch",
        "    expect: null",
        "    capture: [screenshot, process_list]",
    ]
    for f in features:
        if f["priority"] != 1:
            continue
        title = f["title"].replace('"', "'")
        lines += [
            f"  - id: {f['id']}",
            f"    action: [intent: {json.dumps(title)}]",
            "    expect: null",
            "    capture: [screenshot, uia_tree]",
        ]
        if len([ln for ln in lines if ln.strip().startswith("- id:")]) > 30:
            break
    lines += [
        "  - id: quit",
        '    action: [hotkey: "alt+F4"]',
        "    expect: null",
        "    capture: [process_list]",
        "correlate_after:",
        "  seeds_from: [ocr_text, uia_labels, file_paths_written]",
        '  map_out: "maps/<target>-tour-v1.md"',
    ]
    return "\n".join(lines) + "\n"


def build_elicitation(run_path: Path, triage: dict[str, Any], target: str) -> dict[str, Any]:
    """Run stage 1b over a triaged run. Writes elicitation/ artifacts.

    Re-extracts strings from the target (min_length 5, playbook A1/A3 need the
    raw text, triage only keeps counts). Offline and deterministic.
    """
    from .analyzers import BinaryAnalyzer

    elic_dir = run_path / "elicitation"
    (elic_dir / "formats").mkdir(parents=True, exist_ok=True)

    analyzer = BinaryAnalyzer()
    raw = analyzer.extract_strings(target, min_length=5)
    texts = [s.string for s in raw if hasattr(s, "string")]

    candidates = mine_format_candidates(texts)
    for c in candidates:
        spec = c["known_spec"] or {"name": "none found yet", "url": "prior-art search (operator step)"}
        stub = (
            f"# {c['ext']} - candidate spec (elicited {_now()}, status: lead)\n"
            f"- Claimed by: {c['hits']} string hit(s) near extensions/magic\n"
            f"- Public spec: {spec['name']} <{spec['url']}>\n"
            "- Record boundaries per spec: (fill during prior-art lookup)\n"
            "- App dialect notes: (filled during oracle capture, never before)\n"
            "- Verdict: pending oracle\n"
            f"- Samples: {json.dumps(c['samples'][:2])}\n"
        )
        _atomic_write(elic_dir / "formats" / f"{c['ext']}.md", stub)

    features = mine_features(texts)
    _atomic_write(elic_dir / "features.json", json.dumps(features, indent=2))
    tour = build_tour_draft(target, features)
    _atomic_write(elic_dir / "tour-draft.yaml", tour)
    help_inv = inventory_help(Path(target))
    triage_formats = triage.get("formats_referenced", [])
    prior_art = (
        f"# Prior art ({_now()}, status: leads - operator runs REA web kinds)\n\n"
        f"Triage format refs: {', '.join(triage_formats) or '(none)'}\n"
        f"Mined candidates: {', '.join(c['ext'] for c in candidates[:10]) or '(none)'}\n\n"
        "Search leads (one pass per target, time-boxed to an hour):\n"
        "- Existing specs, SDKs, plugins, converters for the app's formats.\n"
        "- Teardown write-ups, CTF solutions, forum threads about the file format.\n"
        "- Compatible apps (anything that already reads the format is an oracle *and* a reference).\n"
        "Log dead ends here - the next target benefits from knowing what does not exist.\n"
    )
    _atomic_write(elic_dir / "prior-art.md", prior_art)
    summary = {
        "strings_scanned": len(texts),
        "format_candidates": len(candidates),
        "features": len(features),
        "priority1": sum(1 for f in features if f["priority"] == 1),
        "help_inventory": help_inv,
        "triage_formats": triage_formats,
    }
    _atomic_write(elic_dir / "elicitation.json", json.dumps(summary, indent=2))
    summary.update(
        {
            "success": True,
            "message": (
                f"Elicitation: {len(candidates)} format candidate(s), {len(features)} feature(s) "
                f"({summary['priority1']} file-I/O), tour draft + prior-art leads in elicitation/."
            ),
        }
    )
    return summary


# ---------------------------------------------------------------------------
# Stage 3: clicker sessions (execute the target - confirm + isolation gates)


_SESSIONS: dict[str, dict[str, Any]] = {}
_WORKERS: dict[str, threading.Thread] = {}
_CANCELS: dict[str, threading.Event] = {}
_LOCK = threading.RLock()

DEFAULT_STEP_CAP = 200
DEFAULT_TIME_CAP_S = 600


def _session_dir(run_path: Path, session_id: str) -> Path:
    d = run_path / "clicker" / "sessions" / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_session(sdir: Path, state: dict[str, Any]) -> None:
    tmp = sdir / "session.json.tmp"
    tmp.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, sdir / "session.json")


def _slog(sdir: Path, event: str, detail: str = "") -> None:
    with (sdir / "log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _now(), "event": event, "detail": detail}) + "\n")


def start_session(
    run_path: Path,
    run_id: str,
    target: str,
    mode: str = "rip",
    tour_rel: str | None = None,
    step_cap: int = DEFAULT_STEP_CAP,
    time_cap_s: int = DEFAULT_TIME_CAP_S,
    confirm: bool = False,
    accept_local: bool = False,
) -> dict[str, Any]:
    """Start a clicker session (background worker). Never raises.

    Gates, in order: known run/target, confirm, isolation opt-out, mode sanity,
    driver presence. The worker records everything under
    ``clicker/sessions/<sid>/``.
    """
    mode = (mode or "rip").lower()
    if not Path(target).is_file():
        return {"success": False, "error": f"Target must be a local file: {target}"}
    if not confirm:
        return {
            "success": False,
            "error": "Clicker sessions execute the target. Re-run with confirm=True (VM preferred - see accept_local).",
        }
    if not accept_local:
        return {
            "success": False,
            "error": (
                "Spec section 1: the clicker runs isolated (Hyper-V VM via virtualization-mcp, snapshot "
                "before, no network, no credentials). Pass accept_local=True for an explicit, logged "
                "opt-out to drive on this desktop."
            ),
        }
    if mode not in ("rip", "tour"):
        return {"success": False, "error": f"Unknown clicker mode '{mode}'. Valid: rip, tour."}
    tour_path: Path | None = None
    if mode == "tour":
        if not tour_rel:
            return {"success": False, "error": "Tour mode needs tour_rel (e.g. elicitation/tour-draft.yaml)."}
        tour_path = (run_path / tour_rel).resolve()
        try:
            tour_path.relative_to(run_path.resolve())
        except ValueError:
            return {"success": False, "error": "Tour path escapes the run directory."}
        if not tour_path.is_file():
            return {"success": False, "error": f"No such tour: {tour_rel}"}
    probe = clicker_engines()
    if not probe["drive_ready"]:
        return {
            "success": False,
            "error": "pywinauto not installed - live driving unavailable.",
            "install_hint": probe["engines"]["pywinauto"].get("install_hint"),
            "note": "Elicitation (formats/features/tour draft) works without it.",
        }

    session_id = uuid.uuid4().hex[:12]
    with _LOCK:
        for sid, st in _SESSIONS.items():
            if st.get("run_id") == run_id and st.get("status") == "running":
                return {"success": False, "busy": True, "session_id": sid, "error": "A session is already running."}
        sdir = _session_dir(run_path, session_id)
        state: dict[str, Any] = {
            "session_id": session_id,
            "run_id": run_id,
            "target": target,
            "mode": mode,
            "tour_rel": tour_rel,
            "step_cap": max(1, min(int(step_cap), 2000)),
            "time_cap_s": max(30, min(int(time_cap_s), 3600)),
            "confirm": True,
            "accept_local": True,
            "status": "running",
            "started": _now(),
            "ended": None,
            "error": None,
            "coverage": {},
            "message": "",
        }
        _save_session(sdir, state)
        _slog(sdir, "session_started", f"mode={mode} target={target} LOCAL-RUN-OPTOUT (no VM)")
        token = uuid.uuid4().hex
        cancel = threading.Event()
        _CANCELS[token] = cancel
        worker = threading.Thread(
            target=_session_worker,
            args=(sdir, state, token, cancel),
            name=f"clicker-{session_id}",
            daemon=True,
        )
        _SESSIONS[session_id] = {**state, "_token": token, "_dir": str(sdir)}
        _WORKERS[token] = worker
        worker.start()
    return {
        "success": True,
        "session_id": session_id,
        "run_id": run_id,
        "mode": mode,
        "status": "running",
        "message": f"Clicker session {session_id} started ({mode}). Poll status; stop kills the target tree.",
    }


def get_session(run_path: Path, session_id: str) -> dict[str, Any]:
    """Session status; a running session with no live worker becomes interrupted."""
    with _LOCK:
        live = _SESSIONS.get(session_id)
    sfile = run_path / "clicker" / "sessions" / session_id / "session.json"
    if not sfile.exists():
        return {"success": False, "error": f"Unknown session: {session_id}"}
    state = json.loads(sfile.read_text(encoding="utf-8"))
    if state.get("status") == "running":
        token = (live or {}).get("_token", "")
        worker = _WORKERS.get(token)
        if worker is None or not worker.is_alive():
            state["status"] = "interrupted"
            state["ended"] = _now()
            state["error"] = "Worker gone (backend restarted?) while the session ran."
            _save_session(run_path / "clicker" / "sessions" / session_id, state)
    state["success"] = True
    return state


def stop_session(run_path: Path, session_id: str) -> dict[str, Any]:
    """Stop a session: cancel event + kill the target process tree."""
    with _LOCK:
        live = _SESSIONS.get(session_id)
        sdir = run_path / "clicker" / "sessions" / session_id
        sfile = sdir / "session.json"
        if not sfile.exists():
            return {"success": False, "error": f"Unknown session: {session_id}"}
        state = json.loads(sfile.read_text(encoding="utf-8"))
        if state.get("status") != "running":
            return {"success": True, "session_id": session_id, "message": f"Session already {state.get('status')}."}
        if live and live.get("_token"):
            cancel = _CANCELS.get(live["_token"])
            if cancel is not None:
                cancel.set()
        pid = state.get("target_pid")
        if pid:
            try:
                engines.kill_tree(int(pid))
            except (ValueError, TypeError):
                pass
        state.update({"status": "stopped", "ended": _now(), "error": "Stopped by user."})
        _save_session(sdir, state)
        _slog(sdir, "stopped", "user stop; target tree killed")
        if live:
            live["status"] = "stopped"
    return {"success": True, "session_id": session_id, "message": f"Session {session_id} stopped; target tree killed."}


def correlate_session(run_id: str, session_id: str, with_rea: bool = True, max_seeds: int = 12) -> dict[str, Any]:
    """Tier 3 section 5 MVP: runtime strings -> static seeds -> code refs -> map rows.

    Reads the session capture bundle (tour.jsonl, uia_tree, OCR text), dedupes
    against the binary's own strings, and emits per-seed verdicts
    (mapped / ambiguous / no static trace) into ``map.md``. REA native_search
    is best-effort per seed; failures stay honest rows, never exceptions.
    Blocking - call via to_thread.
    """
    from . import gym as _gym
    from .analyzers import BinaryAnalyzer

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    sdir = run_path / "clicker" / "sessions" / session_id
    if not (sdir / "session.json").exists():
        return {"success": False, "error": f"Unknown session: {session_id}"}
    target = state["target"]

    # 1. Harvest runtime strings from the bundle. Control names and window
    #    titles outrank framework plumbing: generic UIA ControlType values
    #    (Pane, Button) correlate to everything, i.e. to nothing.
    runtime: dict[str, int] = {}

    def _feed(text: str, weight: int = 1) -> None:
        for w in re.findall(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9_.\\-]{3,40}", text or ""):
            runtime[w] = runtime.get(w, 0) + weight

    jsonl = sdir / "tour.jsonl"
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            _feed(str(rec.get("outcome", "")))
            _feed(str(rec.get("ocr_text", "")), 3)
            _feed(str(rec.get("clipboard", "")), 3)
            _feed(str(rec.get("text", "")), 3)
    uia = sdir / "uia_tree.json"
    if uia.exists():
        try:
            tree = json.loads(uia.read_text(encoding="utf-8", errors="replace"))
        except ValueError:
            tree = []
        for win in tree if isinstance(tree, list) else []:
            _feed(str(win.get("window", "")), 3)
            for node in win.get("nodes", []) or []:
                _feed(str(node.get("name", "")), 3)
                # control_type / automation_id deliberately unfed: framework vocabulary.
    stop_words = {"the", "and", "with", "from", "that", "this", "windows", "microsoft"}
    ranked = sorted(
        ((w, c) for w, c in runtime.items() if w.lower() not in stop_words and not w[0].isdigit()),
        key=lambda kv: -kv[1],
    )[: max(1, max_seeds * 3)]

    # 2. Baseline: the binary's own strings. Seeds must occur in the binary
    #    to be statically correlatable; runtime-only strings get honest rows.
    analyzer = BinaryAnalyzer()
    raw = analyzer.extract_strings(target, min_length=4)
    static_texts = [s.string for s in raw if hasattr(s, "string")]
    static_blob = "\n".join(static_texts)
    static_low = static_blob.lower()
    seeds = [w for w, _ in ranked if w.lower() in static_low][:max_seeds]
    runtime_only = [w for w, _ in ranked[:max_seeds] if w.lower() not in static_low]

    # 3. Static refs per seed: offsets + Ghidra inventory (functions + string
    #    xrefs) + REA native_search. A seed referenced FROM named functions is
    #    mapped; bare offsets are ambiguous; absence is absence.
    try:
        from .analyzers import ghidra_inventory

        inv = ghidra_inventory(target)
        funcs_ok = bool(inv.get("success"))
        func_names = " ".join(str(f.get("name", "")) for f in inv.get("functions", [])).lower()
        xref_funcs: dict[str, list[str]] = {}
        for addr, callers in (inv.get("xrefs") or {}).items():
            xref_funcs[addr] = callers
        inv_strings = {s.get("value", ""): s.get("address", "") for s in inv.get("strings", [])}
    except Exception as e:
        logger.debug("ghidra inventory failed: %s", e)
        funcs_ok, func_names, xref_funcs, inv_strings = False, "", {}, {}

    rows = []
    rea_used = 0
    for seed in seeds:
        offsets = [m.start() for m in re.finditer(re.escape(seed), static_blob)][:10]
        in_funcs = seed.lower() in func_names
        xref_to = sorted(
            {
                fn
                for addr, fns in xref_funcs.items()
                for fn in fns
                if seed.lower() in (inv_strings.get(addr, "") or "").lower()
            }
            | {fn for v, a in inv_strings.items() if seed.lower() in v.lower() for fn in xref_funcs.get(a, [])}
        )
        rea_note = "REA skipped (with_rea=False or budget spent)."
        if with_rea and rea_used < 6:
            from . import rea_bridge

            rea_used += 1
            res = rea_bridge.run_rea("native_search", target=target, query=seed, timeout_s=90)
            if res.get("success"):
                out = json.dumps(res.get("result") or res)[:600]
                rea_note = f"REA answered: {out}"
            else:
                rea_note = f"REA unavailable: {(res.get('error') or '')[:160]}"
        verdict = (
            "mapped"
            if (offsets and (xref_to or in_funcs or "REA answered" in rea_note))
            else ("ambiguous" if offsets else "no static trace")
        )
        rows.append(
            {
                "seed": seed,
                "offsets": offsets,
                "offset_count": len(offsets),
                "in_function_names": in_funcs,
                "xref_functions": xref_to[:10],
                "rea": rea_note,
                "verdict": verdict,
            }
        )
    for w in runtime_only:
        rows.append(
            {
                "seed": w,
                "offsets": [],
                "offset_count": 0,
                "in_function_names": False,
                "rea": "Not attempted (absent from binary).",
                "verdict": "no static trace",
            }
        )

    mapped = sum(1 for r in rows if r["verdict"] == "mapped")
    lines = [
        f"# Feature-to-code map ({_now()})",
        f"Target: {target} | run {run_id} | session {session_id}",
        f"Seeds: {len(rows)} ({mapped} mapped, {sum(1 for r in rows if r['verdict'] == 'ambiguous')} ambiguous, "
        f"{sum(1 for r in rows if r['verdict'] == 'no static trace')} no static trace). "
        "Functions inventory: " + ("available" if funcs_ok else "unavailable") + ".",
        "",
        "Stated limits: string match is correlation, not proof - identical text can serve",
        "unrelated features. REA rows carry its evidence verbatim; human reviews every map.",
        "",
    ]
    for r in rows:
        lines += [
            f"## {r['seed']} - {r['verdict']}",
            f"- Static offsets: {r['offsets'][:5]}{'...' if r['offset_count'] > 5 else ''} ({r['offset_count']} hits)",
            f"- In function names: {r['in_function_names']}",
            f"- Xref'd from: {', '.join(r.get('xref_functions', [])[:10]) or '(none)'}",
            f"- {r['rea']}",
            "",
        ]
    _atomic_write(sdir / "map.md", "\n".join(lines))
    _atomic_write(sdir / "map.json", json.dumps({"seeds": rows, "mapped": mapped, "total": len(rows)}, indent=2))
    msg = f"Correlate: {len(rows)} seed(s), {mapped} mapped. Map in clicker/sessions/{session_id}/map.md."
    _slog(sdir, "correlated", msg)
    return {
        "success": True,
        "run_id": run_id,
        "session_id": session_id,
        "seeds": len(rows),
        "mapped": mapped,
        "message": msg,
    }


def _session_steps(sdir: Path) -> list[dict[str, Any]]:
    """Step records for comparison: tour-results.json preferred, tour.jsonl fallback."""
    res_file = sdir / "tour-results.json"
    if res_file.exists():
        try:
            data = json.loads(res_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except ValueError:
            pass
    out = []
    jsonl = sdir / "tour.jsonl"
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("kind") in ("tour_step", "canvas_click"):
                out.append(rec)
    return out


def compare_sessions(run_id: str, session_a: str, session_b: str) -> dict[str, Any]:
    """Determinism check (spec: two runs of the same build must agree).

    Compares per-step (id, action, outcome, expect_ok) between two sessions of
    one run. Timestamps, pids, screenshots and OCR text are excluded by design
    (environment, not behavior). Returns score + diverged list; never raises.
    """
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    base = run_path / "clicker" / "sessions"
    dirs = {}
    for sid in (session_a, session_b):
        sdir = base / sid
        if not (sdir / "session.json").exists():
            return {"success": False, "error": f"Unknown session: {sid}"}
        dirs[sid] = sdir
    steps_a = _session_steps(dirs[session_a])
    steps_b = _session_steps(dirs[session_b])

    def _sig(s: dict[str, Any]) -> str:
        action = json.dumps(s.get("action"), sort_keys=True, default=str)
        return f"{s.get('id')}|{action}|{s.get('outcome')}|{s.get('expect_ok')}"

    sigs_a = [_sig(s) for s in steps_a]
    sigs_b = [_sig(s) for s in steps_b]
    pairs = min(len(sigs_a), len(sigs_b))
    same = sum(1 for i in range(pairs) if sigs_a[i] == sigs_b[i])
    diverged = [
        {"index": i, "a": sigs_a[i][:200], "b": sigs_b[i][:200]} for i in range(pairs) if sigs_a[i] != sigs_b[i]
    ][:20]
    length_note = None
    if len(sigs_a) != len(sigs_b):
        length_note = f"step counts differ: {session_a}={len(sigs_a)}, {session_b}={len(sigs_b)}"
    score = (same / pairs) if pairs else 0.0
    out = {
        "success": True,
        "run_id": run_id,
        "sessions": [session_a, session_b],
        "steps_compared": pairs,
        "identical": same,
        "score": round(score, 3),
        "deterministic": score == 1.0 and length_note is None,
        "length_note": length_note,
        "diverged": diverged,
        "message": f"Determinism {same}/{pairs} identical steps (score {score:.2f})."
        + ("" if score == 1.0 and length_note is None else " Divergences are bugs - file them."),
    }
    _atomic_write(base / f"determinism-{session_a[:8]}-vs-{session_b[:8]}.json", json.dumps(out, indent=2))
    return out


def file_offset_to_va(target: str, file_offset: int, image_base: int | None = None) -> int | None:
    """Map a raw file offset to a virtual address via the PE section table.

    Correlate seeds carry FILE offsets (string extraction); Ghidra/IDA want
    VAs. Returns None when the offset falls in headers or gaps (honest skip,
    not a zero address). No dependency: struct-only PE parse.
    """
    import struct

    try:
        with open(target, "rb") as f:
            data = f.read(0x1000)
        if data[:2] != b"MZ":
            return None
        (e_lfanew,) = struct.unpack_from("<I", data, 0x3C)
        with open(target, "rb") as f:
            f.seek(e_lfanew)
            hdr = f.read(8)
            if hdr[:4] != b"PE\0\0":
                return None
            (n_sec,) = struct.unpack_from("<H", hdr, 6)
            # COFF header is 20 bytes; optional-header size lives at its +16.
            f.seek(e_lfanew + 4 + 16)
            (opt_size,) = struct.unpack("<H", f.read(2))
            if image_base is None:
                f.seek(e_lfanew + 4 + 20)
                (magic,) = struct.unpack("<H", f.read(2))
                # PE32 (0x10b): ImageBase at +28; PE32+ (0x20b): ImageBase at +24.
                f.seek(e_lfanew + 4 + 20 + (28 if magic == 0x10B else 24))
                (image_base,) = struct.unpack("<I", f.read(4))
            f.seek(e_lfanew + 4 + 20 + opt_size)
            for _ in range(n_sec):
                sec = f.read(40)
                if len(sec) < 40:
                    break
                _name, _vsize, vaddr, raw_size, raw_ptr = struct.unpack_from("<8sIIII", sec)
                if raw_ptr <= file_offset < raw_ptr + raw_size:
                    return image_base + vaddr + (file_offset - raw_ptr)
    except (OSError, struct.error) as e:
        logger.debug("offset->VA failed for %s: %s", target, e)
    return None


def export_map(run_id: str, session_id: str, rename: bool = False) -> dict[str, Any]:
    """Item 6: put the map where analysts look.

    Ghidra: plate comments on every seed string address + (only with
    rename=True, only on default FUN_* names, only identifier-safe seeds)
    function renames, in the analyst's project via PyGhidra.
    IDA: generates ``map_import_ida.py`` (idc.set_cmt + idc.set_name with
    SN_CHECK) for the analyst to run inside IDA - no seat needed here.
    Blocking - call via to_thread. Never raises.
    """
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    sdir = run_path / "clicker" / "sessions" / session_id
    map_file = sdir / "map.json"
    if not map_file.exists():
        return {"success": False, "error": f"No map yet - correlate session {session_id} first."}
    try:
        seeds = json.loads(map_file.read_text(encoding="utf-8")).get("seeds", [])
    except ValueError as e:
        return {"success": False, "error": f"map.json unreadable: {e}"}

    commented, renamed = 0, []
    ghidra_error = None
    # Two address sources: file-offset math feeds the IDA script (whose rebase
    # guard verifies bytes before commenting); Ghidra comments use defined-
    # string addresses from the live program (loader may rebase - file math
    # silently misses there, live-fire lesson).
    va_rows: list[dict[str, Any]] = []
    for row in seeds:
        if row.get("verdict") != "mapped":
            continue
        vas = []
        for off in (row.get("offsets") or [])[:5]:
            try:
                va = file_offset_to_va(state["target"], int(off))
            except (ValueError, TypeError):
                va = None
            if va is not None:
                vas.append(va)
        va_rows.append({**row, "vas": vas})
    try:
        from .analyzers import _ensure_jvm

        _ensure_jvm()
        import tempfile

        import pyghidra
        from ghidra.program.model.listing import CodeUnit
        from ghidra.program.model.symbol import SourceType

        with tempfile.TemporaryDirectory(prefix="ghidra-export-") as proj_dir:
            # analyze=True: comments need defined strings/code, which only
            # exist after analysis (minutes on big binaries - on-demand).
            with pyghidra.open_program(state["target"], project_location=proj_dir, analyze=True) as flat_api:
                program = flat_api.getCurrentProgram()
                listing, fm = program.getListing(), program.getFunctionManager()
                defined: list[tuple[Any, str]] = []
                for data in listing.getDefinedData(True):
                    try:
                        dtype = str(data.getDataType().getName()).lower()
                    except Exception as e:
                        logger.debug("export dtype probe failed: %s", e)
                        continue
                    if dtype not in ("string", "unicode", "utf8", "utf16"):
                        continue
                    try:
                        defined.append((data.getAddress(), str(data.getValue())))
                    except Exception as e:
                        logger.debug("export string read failed: %s", e)
                        continue
                addr_of: dict[str, list[Any]] = {}
                for row in va_rows:
                    hits = [a for a, v in defined if row["seed"].lower() in v.lower()][:5]
                    row["vas"] = [int(a.getOffset()) for a in hits]
                    addr_of[row["seed"]] = hits
                for row in va_rows:
                    for addr in addr_of.get(row["seed"], []):
                        try:
                            cu = listing.getCodeUnitAt(addr)
                            if cu is None:
                                continue
                            cu.setComment(
                                CodeUnit.PLATE_COMMENT,
                                f"[ClickerLab] seed {row['seed']!r} "
                                f"xref: {', '.join((row.get('xref_functions') or [])[:5]) or 'static-only'}",
                            )
                            commented += 1
                        except Exception as e:
                            logger.debug("comment failed at %s: %s", addr, e)
                if rename:
                    for row in seeds:
                        seed = row.get("seed", "")
                        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{2,60}", seed):
                            continue
                        for fn_name in row.get("xref_functions", [])[:5]:
                            try:
                                for fn in fm.getFunctions(True):
                                    if str(fn.getName()) == fn_name and fn_name.startswith("FUN_"):
                                        fn.setName("CL_" + seed, SourceType.USER_DEFINED)
                                        renamed.append(f"{fn_name} -> CL_{seed}")
                                        break
                            except Exception as e:
                                logger.debug("rename failed for %s: %s", fn_name, e)
    except Exception as e:
        ghidra_error = str(e)[:300]
        logger.debug("ghidra export failed: %s", e)

    ida_lines = [
        "# ClickerLab map import - run inside IDA (File > Script file).",
        "# VAs verified before commenting: a row whose bytes do not contain the",
        "# seed is SKIPPED (image may be rebased - silence beats wrong comments).",
        "import ida_bytes",
        f"ROWS = {json.dumps([[r.get('seed'), r.get('vas', [])[:3], (r.get('xref_functions') or [])[:5]] for r in va_rows])}",
        "n = skipped = 0",
        "for seed, vas, fns in ROWS:",
        "    for va in vas:",
        "        try:",
        "            blob = ida_bytes.get_strlit_contents(va, -1, 0) or b''",
        "        except Exception:",
        "            blob = b''",
        "        if seed.lower().encode() not in blob.lower():",
        "            skipped += 1",
        "            continue",
        "        ida_bytes.set_cmt(va, f'[ClickerLab] {seed} <- {chr(44).join(fns)}', 0)",
        "        n += 1",
        "print(f'map_import: {len(ROWS)} seeds, {n} comments, {skipped} skipped (rebase guard)')",
    ]
    ida_script = sdir / "map_import_ida.py"
    _atomic_write(ida_script, "\n".join(ida_lines) + "\n")
    msg = (
        f"Export: {commented} Ghidra plate comments, {len(renamed)} renames, "
        f"IDA script at clicker/sessions/{session_id}/map_import_ida.py."
    )
    if ghidra_error:
        msg += f" Ghidra live export failed (IDA script still written): {ghidra_error}"
    _slog(sdir, "exported", msg)
    return {
        "success": True,
        "run_id": run_id,
        "session_id": session_id,
        "ghidra_comments": commented,
        "ghidra_renames": renamed,
        "ghidra_error": ghidra_error,
        "ida_script": f"clicker/sessions/{session_id}/map_import_ida.py",
        "message": msg,
    }


def _snapshot_process_list() -> list[dict[str, Any]]:
    import psutil

    rows = []
    for p in psutil.process_iter(["pid", "name"]):
        try:
            rows.append({"pid": p.info["pid"], "name": p.info["name"] or "?"})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rows


def _dump_uia_tree(windows: list[Any]) -> list[dict[str, Any]]:
    """B1 node records: AutomationId, Name, ControlType + pattern names."""
    tree = []
    for w in windows:
        try:
            children = []
            for d in w.descendants():
                try:
                    info = d.element_info
                    patterns = []
                    try:
                        patterns = [i.interface for i in d.iface_registry] if hasattr(d, "iface_registry") else []
                    except Exception as e:
                        logger.debug("pattern probe failed: %s", e)
                        patterns = []
                    children.append(
                        {
                            "automation_id": str(getattr(info, "automation_id", "") or ""),
                            "name": str(getattr(info, "name", "") or "")[:160],
                            "control_type": str(getattr(info, "control_type", "") or ""),
                            "patterns": patterns,
                        }
                    )
                except Exception as e:
                    logger.debug("node dump skipped: %s", e)
                    continue
            tree.append({"window": str(getattr(w.element_info, "name", "") or "")[:160], "nodes": children})
        except Exception as e:
            tree.append({"window": "?", "error": str(e)[:200]})
    return tree


def _session_worker(sdir: Path, state: dict[str, Any], token: str, cancel: threading.Event) -> None:
    """Drive the target (B1 rip or B2 tour). Runs off the event loop."""
    from pywinauto import Application

    sid = state["session_id"]
    deadline = time.monotonic() + state["time_cap_s"]
    target_pid: int | None = None
    coverage: dict[str, Any] = {
        "nodes_seen": 0,
        "nodes_visited": 0,
        "menus_seen": 0,
        "menus_opened": 0,
        "dialogs_reached": 0,
        "steps": 0,
        "ocr_regions": 0,
        "coord_clicks": 0,
        "named_skips": 0,
    }
    reg_before: Path | None = None
    try:
        warn_operator(sdir, state["mode"], state["target"])
        watch = [Path(os.environ.get("TEMP", r"C:\Windows\Temp"))]
        watch += [Path(p) for p in state.get("watch_dirs", []) if Path(p).is_dir()]
        state["watch_dirs"] = [str(p) for p in watch]
        _save_session(sdir, state)
        reg_before = snapshot_registry()
        _slog(sdir, "baselines", f"watch={[str(p) for p in watch]} reg={'ok' if reg_before else 'unavailable'}")
        _slog(sdir, "launch", state["target"])
        proc = subprocess.Popen([state["target"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        target_pid = proc.pid
        state["target_pid"] = target_pid
        _save_session(sdir, state)
        with _LOCK:
            if sid in _SESSIONS:
                _SESSIONS[sid]["target_pid"] = target_pid

        app = Application(backend="uia")
        try:
            app.connect(process=target_pid, timeout=20)
        except Exception:
            time.sleep(3)
            app.connect(process=target_pid, timeout=20)

        if state["mode"] == "rip":
            _run_rip(sdir, state, app, coverage, cancel, deadline)
        else:
            _run_tour(sdir, state, app, coverage, cancel, deadline)

        ok, msg = (
            True,
            (
                f"{state['mode']} complete: {coverage['nodes_visited']}/{coverage['nodes_seen']} nodes, "
                f"{coverage['menus_opened']}/{coverage['menus_seen']} menus, "
                f"{coverage['dialogs_reached']} dialogs, {coverage['steps']} steps."
            ),
        )
    except engines.Cancelled:
        ok, msg = False, "Cancelled by stop; target tree killed."
    except Exception as e:
        logger.exception("Clicker session %s failed", sid)
        ok, msg = False, str(e)[:500]
    finally:
        release_mouse()
        if target_pid:
            try:
                engines.kill_tree(target_pid)
            except Exception as e:
                logger.debug("target tree kill failed: %s", e)
        try:
            reg_after = snapshot_registry()
            if reg_before and reg_after:
                before = reg_before.read_text(encoding="utf-8", errors="replace").splitlines()
                after = reg_after.read_text(encoding="utf-8", errors="replace").splitlines()
                import difflib

                reg_diff = [ln for ln in difflib.unified_diff(before, after, n=0) if ln[:1] in "+-"][2:200]
                _atomic_write(sdir / "reg-diff.txt", "\n".join(reg_diff) + "\n")
                reg_after.unlink(missing_ok=True)
                reg_before.unlink(missing_ok=True)
        except Exception as e:
            logger.debug("registry diff failed: %s", e)
        with _LOCK:
            _WORKERS.pop(token, None)
            _CANCELS.pop(token, None)
            live = _SESSIONS.get(sid, {})
            record = live.get("status") != "stopped"  # else stop_session already recorded the outcome
            cur: dict[str, Any] | None = None
            if record:
                try:
                    cur = json.loads((sdir / "session.json").read_text(encoding="utf-8"))
                except (OSError, ValueError) as e:
                    logger.debug("session state unreadable: %s", e)
                    record = False
            if record and cur is not None:
                cur.update(
                    {
                        "status": "done" if ok else "failed",
                        "ended": _now(),
                        "error": None if ok else msg,
                        "message": msg,
                        "coverage": coverage,
                        "target_pid": target_pid,
                    }
                )
                _save_session(sdir, cur)
                _slog(sdir, "session_done" if ok else "session_failed", msg)
                if sid in _SESSIONS:
                    _SESSIONS[sid].update(cur)


def _cancelled(cancel: threading.Event, deadline: float) -> bool:
    if cancel.is_set():
        raise engines.Cancelled("clicker")
    if time.monotonic() > deadline:
        raise TimeoutError("time cap reached")
    return False


def _target_alive(state: dict[str, Any]) -> bool:
    """True while the launched target process still runs (psutil, zombie-aware).

    Checked every pass so the driver never pokes dead COM handles - a UIA call
    against an exited process can block indefinitely (live-fire 2026-10-14).
    """
    import psutil

    try:
        proc = psutil.Process(int(state["target_pid"]))
        return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError, ValueError, TypeError) as e:
        logger.debug("target liveness check failed: %s", e)
        return False


def _shoot(app: Any, sdir: Path, name: str) -> Path | None:
    """Screenshot the top window into the session dir. None when unavailable."""
    try:
        shot = app.top_window().capture_as_image()
        if shot is None:
            return None
        path = sdir / f"{name}.png"
        shot.save(str(path))
        return path
    except Exception as e:
        logger.debug("screenshot %s failed: %s", name, e)
        return None


def _click_coords(x: int, y: int) -> bool:
    """Coordinate click (B3/custom UI). Verifies nothing - caller diffs screenshots."""
    try:
        import pywinauto.mouse

        pywinauto.mouse.click(button="left", coords=(x, y))
        time.sleep(0.5)
        release_mouse()
        return True
    except Exception as e:
        logger.debug("coord click (%s,%s) failed: %s", x, y, e)
        return False


def _drive_canvas(
    sdir: Path,
    app: Any,
    window: Any,
    coverage: dict[str, Any],
    visited: set[str],
    step: int,
    state: dict[str, Any],
    cancel: threading.Event,
    deadline: float,
) -> int:
    """B3: OCR one canvas window, click each unvisited text region once, verify by pixels."""
    try:
        title = str(window.element_info.name or "")[:80]
    except Exception:
        title = "?"
    shot = _shoot(app, sdir, f"canvas-{step}")
    if shot is None:
        return step
    regions = ocr_regions(shot)
    coverage["ocr_regions"] = coverage.get("ocr_regions", 0) + len(regions)
    for reg in regions:
        _cancelled(cancel, deadline)
        if step >= state["step_cap"]:
            break
        key = f"ocr:{reg['text'].lower()}"
        if key in visited:
            continue
        visited.add(key)
        before = _shoot(app, sdir, f"canvas-{step}-before")
        clicked = _click_coords(reg["x"], reg["y"])
        after = _shoot(app, sdir, f"canvas-{step}-after")
        changed: list[dict[str, int]] = []
        if before and after:
            changed = screenshot_diff_regions(before, after)
            if not changed:
                before.unlink(missing_ok=True)
        coverage["coord_clicks"] = coverage.get("coord_clicks", 0) + (1 if clicked else 0)
        step += 1
        jlog(
            sdir,
            {
                "kind": "canvas_click",
                "window": title,
                "text": reg["text"],
                "x": reg["x"],
                "y": reg["y"],
                "clicked": clicked,
                "changed_regions": len(changed),
                "shot": shot.name,
            },
        )
        _slog(sdir, "canvas_click", f"{title!r} '{reg['text']}' clicked={clicked} changed={len(changed)}")
    return step


def _run_rip(
    sdir: Path,
    state: dict[str, Any],
    app: Any,
    coverage: dict[str, Any],
    cancel: threading.Event,
    deadline: float,
) -> None:
    """B1: BFS over the live UIA tree (GUITAR-style rip-then-walk)."""
    time.sleep(2)  # let the main window appear
    visited: set[str] = set()
    step = 0
    watch = [Path(p) for p in state.get("watch_dirs", [])]
    pass_baseline, _ = snapshot_files(watch)
    while step < state["step_cap"]:
        _cancelled(cancel, deadline)
        if not _target_alive(state):
            _slog(sdir, "target_exited", "Target process is gone - ending the walk (no dead-COM poking).")
            break
        try:
            windows = app.windows()
        except Exception:
            break
        tree = _dump_uia_tree(windows)
        _atomic_write(sdir / "uia_tree.json", json.dumps(tree, indent=2))
        coverage["nodes_seen"] = sum(len(w.get("nodes", [])) for w in tree) + len(tree)
        coverage["dialogs_reached"] = len(tree)

        menus_seen = menus_opened = 0
        progressed = False
        for w in windows:
            _cancelled(cancel, deadline)
            if not _target_alive(state):
                _slog(sdir, "target_exited", "Target died mid menu walk - ending the pass.")
                break
            try:
                menu = w.menu()
                items = menu.items() if menu else []
                menus_seen += len(items)
                for item in items[:20]:
                    _cancelled(cancel, deadline)
                    key = f"menu:{item.text()}"
                    if key in visited:
                        continue
                    visited.add(key)
                    try:
                        item.click_input()
                        menus_opened += 1
                        progressed = True
                    except Exception as e:
                        logger.debug("menu click failed: %s", e)
                        continue
                    step += 1
                    if step >= state["step_cap"]:
                        break
            except engines.Cancelled:
                raise
            except TimeoutError:
                _slog(sdir, "time_cap", "menu walk hit the wall-clock cap.")
                break
            except Exception as e:
                logger.debug("menu walk failed: %s", e)
                continue
            if step >= state["step_cap"]:
                break
        coverage["menus_seen"] += menus_seen
        coverage["menus_opened"] += menus_opened

        # Walk invokable / expandable / selectable controls, cheapest first.
        try:
            for w in windows:
                _cancelled(cancel, deadline)
                if not _target_alive(state):
                    _slog(sdir, "target_exited", "Target died mid control walk - ending the pass.")
                    break
                for d in w.descendants():
                    _cancelled(cancel, deadline)
                    if step >= state["step_cap"]:
                        break
                    try:
                        info = d.element_info
                        key = f"{info.control_type}:{info.automation_id}:{info.name}"
                    except Exception as e:
                        logger.debug("element info failed: %s", e)
                        continue
                    if key in visited:
                        continue
                    acted = False
                    for pattern in ("invoke", "expand", "select"):
                        if not hasattr(d, pattern):
                            continue
                        try:
                            getattr(d, pattern)()
                        except Exception as e:
                            logger.debug("%s failed on %s: %s", pattern, key[:60], e)
                            continue
                        acted = True
                        break
                    if acted:
                        visited.add(key)
                        step += 1
                        progressed = True
                        time.sleep(0.3)
                if step >= state["step_cap"]:
                    break
        except engines.Cancelled:
            raise
        except TimeoutError:
            raise
        except Exception as e:
            logger.debug("control walk pass failed: %s", e)

        # B3 escalation: windows with an empty UIA subtree are custom-rendered
        # (Delphi/Directmedia canvas) - drive them by OCR regions, not blind clicks.
        try:
            for w in windows:
                _cancelled(cancel, deadline)
                if not _target_alive(state):
                    _slog(sdir, "target_exited", "Target died mid canvas walk - ending the pass.")
                    break
                if step >= state["step_cap"]:
                    break
                try:
                    nodes = w.descendants()
                except Exception as e:
                    logger.debug("canvas probe failed: %s", e)
                    continue
                if len(nodes) > 1:
                    continue
                progressed = True
                step = _drive_canvas(sdir, app, w, coverage, visited, step, state, cancel, deadline)
        except engines.Cancelled:
            raise
        except TimeoutError:
            raise
        except Exception as e:
            logger.debug("canvas pass failed: %s", e)

        coverage["steps"] = step
        coverage["nodes_visited"] = len(visited)
        state["coverage"] = dict(coverage)
        _save_session(sdir, state)
        pass_now, pass_trunc = snapshot_files(watch)
        pass_files = diff_files(pass_baseline, pass_now)
        pass_files["truncated"] = pass_trunc
        pass_baseline = pass_now
        jlog(sdir, {"kind": "rip_pass", "step": step, "visited": len(visited), "file_diff": pass_files})
        _slog(sdir, "rip_pass", f"step={step} visited={len(visited)} menus={menus_opened}")
        if not progressed:
            break
    _atomic_write(
        sdir / "rip.json",
        json.dumps(
            {
                "coverage": coverage,
                "deterministic_note": "re-running the same build must produce the same walk (flakes are bugs, file them).",
            },
            indent=2,
        ),
    )
    _atomic_write(sdir / "process_list.json", json.dumps(_snapshot_process_list(), indent=2))


def _run_tour(
    sdir: Path,
    state: dict[str, Any],
    app: Any,
    coverage: dict[str, Any],
    cancel: threading.Event,
    deadline: float,
) -> None:
    """B2: execute a tour-YAML draft; intent steps resolve against the live tree."""
    import yaml

    run_root = sdir.parents[2]  # sessions/<sid> -> sessions -> clicker -> run
    tour_file = (run_root / (state["tour_rel"] or "")).resolve()
    tour = yaml.safe_load(tour_file.read_text(encoding="utf-8")) or {}
    steps = tour.get("steps", [])
    results = []
    step = 0
    watch = [Path(p) for p in state.get("watch_dirs", [])]
    file_before, _ = snapshot_files(watch)
    for tstep in steps:
        _cancelled(cancel, deadline)
        if step >= state["step_cap"]:
            break
        if not _target_alive(state):
            _slog(sdir, "target_exited", "Target process is gone - ending the tour.")
            break
        sid_step = str(tstep.get("id", f"s{step}"))
        action = tstep.get("action")
        expect = tstep.get("expect")
        capture = tstep.get("capture", [])
        gate = classify_step(tstep)
        shot: Path | None = None
        ocr_text = ""
        clip = ""
        file_diff: dict[str, list[str]] = {"added": [], "modified": [], "removed": []}
        ok_expect = True
        if not gate["allowed"]:
            outcome = f"named skip {gate['skip_name']}: {gate['reason']}"
            coverage["named_skips"] = coverage.get("named_skips", 0) + 1
        else:
            outcome = _exec_action(app, action, sdir, sid_step, capture)
            # Fleet receipt rule: every behavioral claim needs a captured artifact.
            shot = _shoot(app, sdir, sid_step)
            if shot is not None:
                ocr_text = ocr_image(shot)
            clip = read_clipboard_text()
            file_now, file_trunc = snapshot_files(watch)
            file_diff = diff_files(file_before, file_now)
            file_diff["truncated"] = file_trunc
            file_before = file_now
            if expect:
                try:
                    titles = " ".join(w.window_text() for w in app.windows())
                except Exception as e:
                    logger.debug("title read failed: %s", e)
                    titles = ""
                ok_expect = str(expect).lower() in titles.lower() or str(expect).lower() in ocr_text.lower()
        record = {
            "id": sid_step,
            "action": action,
            "outcome": outcome,
            "expect": expect,
            "expect_ok": ok_expect,
            "shot": shot.name if shot else None,
            "ocr_text": ocr_text[:2000],
            "clipboard": clip[:500],
            "file_diff": {k: (v[:20] if isinstance(v, list) else v) for k, v in file_diff.items()},
        }
        results.append(record)
        jlog(sdir, {"kind": "tour_step", **record})
        _slog(sdir, "tour_step", f"{sid_step}: {outcome} expect_ok={ok_expect}")
        step += 1
        coverage["steps"] = step
        coverage["nodes_visited"] = step
        state["coverage"] = dict(coverage)
        _save_session(sdir, state)
    _atomic_write(sdir / "tour-results.json", json.dumps(results, indent=2, default=str))
    _atomic_write(sdir / "uia_tree.json", json.dumps(_dump_uia_tree(app.windows()), indent=2, default=str))
    _atomic_write(sdir / "process_list.json", json.dumps(_snapshot_process_list(), indent=2))


def _exec_action(app: Any, action: Any, sdir: Path, sid_step: str, capture: list[str]) -> str:
    """Execute one tour action. Returns a short outcome string; never raises."""
    try:
        acts = action if isinstance(action, list) else [action]
        notes = []
        for a in acts:
            if a == "launch":
                notes.append("launched (session start)")
            elif isinstance(a, dict) and "intent" in a:
                notes.append(_resolve_intent(app, str(a["intent"]), sdir))
            elif isinstance(a, dict) and "click_menu" in a:
                notes.append(_resolve_intent(app, f"{a.get('click_menu', '')} {a.get('click_item', '')}", sdir))
            elif isinstance(a, dict) and "hotkey" in a:
                app.top_window().type_keys(str(a["hotkey"]))
                release_mouse()
                notes.append(f"hotkey {a['hotkey']}")
            elif isinstance(a, dict) and "key" in a:
                app.top_window().type_keys(f"{{{a['key']}}}")
                release_mouse()
                notes.append(f"key {a['key']}")
            elif isinstance(a, dict) and "type" in a:
                app.top_window().type_keys(str(a["type"]), with_spaces=True)
                release_mouse()
                notes.append(f"typed {len(str(a['type']))} chars")
            else:
                notes.append(f"skipped unhandled action {json.dumps(a)[:80]}")
        if "screenshot" in capture:
            _capture_shot(app, sdir / f"{sid_step}.png")
        return "; ".join(notes)[:300]
    except Exception as e:
        return f"action failed: {e!s}"[:200]


def _resolve_intent(app: Any, intent: str, sdir: Path | None = None) -> str:
    """B2 resolution, cheapest first: live UIA name match, then B3 OCR coordinates."""
    words = [w.lower() for w in re.findall(r"[A-Za-zÄÖÜäöüß]{3,}", intent)]
    try:
        for w in app.windows():
            for d in w.descendants():
                try:
                    name = str(d.element_info.name or "").lower()
                except Exception as e:
                    logger.debug("intent name probe failed: %s", e)
                    continue
                if name and any(kw in name for kw in words):
                    for meth in ("invoke", "click_input", "select"):
                        if hasattr(d, meth):
                            try:
                                getattr(d, meth)()
                                time.sleep(0.5)
                                release_mouse()
                                return f"intent '{intent[:40]}' -> '{name[:40]}' via {meth}"
                            except Exception as e:
                                logger.debug("intent %s via %s failed: %s", intent[:40], meth, e)
                                continue
    except Exception as e:
        return f"intent resolve failed: {e!s}"[:120]
    # B3 coordinate fallback: OCR the top window, click the first matching blob.
    if sdir is not None:
        shot = _shoot(app, sdir, "intent-fallback")
        if shot is not None:
            for reg in ocr_regions(shot):
                if any(kw in reg["text"].lower() for kw in words):
                    before = _shoot(app, sdir, "intent-fallback-before")
                    clicked = _click_coords(reg["x"], reg["y"])
                    after = _shoot(app, sdir, "intent-fallback-after")
                    changed = len(screenshot_diff_regions(before, after)) if before and after else 0
                    if clicked:
                        return (
                            f"intent '{intent[:40]}' -> OCR '{reg['text'][:40]}' "
                            f"at ({reg['x']},{reg['y']}) changed={changed}"
                        )
    return f"intent '{intent[:40]}' unresolved (no live or OCR match)"


def elicit_run(run_id: str) -> dict[str, Any]:
    """Stage 1b for a run: needs triage first. Blocking - call via to_thread."""
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    triage_file = run_path / "triage" / "triage.json"
    if not triage_file.exists():
        return {"success": False, "error": "Elicitation needs triage first (advance the run to triage)."}
    triage = json.loads(triage_file.read_text(encoding="utf-8"))
    return build_elicitation(run_path, triage, state["target"])


def clicker_start(
    run_id: str,
    mode: str = "rip",
    tour_rel: str | None = None,
    step_cap: int = DEFAULT_STEP_CAP,
    time_cap_s: int = DEFAULT_TIME_CAP_S,
    confirm: bool = False,
    accept_local: bool = False,
) -> dict[str, Any]:
    """Validate the run, then hand to start_session."""
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    return start_session(run_path, run_id, state["target"], mode, tour_rel, step_cap, time_cap_s, confirm, accept_local)


def clicker_status(run_id: str, session_id: str) -> dict[str, Any]:
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    return get_session(run_path, session_id)


def clicker_stop(run_id: str, session_id: str) -> dict[str, Any]:
    from . import gym as _gym

    run_path, state = _gym._load(run_id)
    if run_path is None:
        return {"success": False, "error": state.get("error", f"Unknown run: {run_id}")}
    return stop_session(run_path, session_id)


def _capture_shot(app: Any, path: Path) -> None:
    try:
        from PIL import ImageGrab

        _ = ImageGrab  # re-export guard: Pillow present means capture_as_image can save
    except ImportError:
        return
    try:
        shot = app.top_window().capture_as_image()
        if shot is not None:
            shot.save(str(path))
    except Exception as e:
        logger.debug("screenshot capture failed: %s", e)
