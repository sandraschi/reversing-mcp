#!/usr/bin/env python3
"""
Decompile a PE via PyGhidra (Ghidra 12+ headless JVM from Python).

Why this exists: analyzeHeadless -postScript with *.py expects Ghidra started in PyGhidra mode.
Running this script with `uv run` uses the bundled pyghidra launcher instead.

Example:
  uv sync --extra ghidra
  $env:GHIDRA_INSTALL_DIR = "C:\\Program Files\\ghidra_12.0_PUBLIC"
  uv run python scripts\\decompile_pe_pyghidra.py --exe "C:\\Program Files (x86)\\Digitale Bibliothek 5\\Digibib5.exe"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_entry_function(prog):  # Program from Ghidra — avoid importing at module level
    fm = prog.getFunctionManager()
    st = prog.getSymbolTable()
    want = {"entry", "EntryPoint", "ENTRY"}
    it = st.getAllSymbols(True)
    while it.hasNext():
        sym = it.next()
        if sym.getName() in want:
            fn = fm.getFunctionAt(sym.getAddress())
            if fn is not None:
                return fn
    cur = fm.getFunctionAfter(prog.getMinAddress())
    return cur


def main() -> int:
    parser = argparse.ArgumentParser(description="Decompile entry (or first) function with PyGhidra")
    parser.add_argument(
        "--exe",
        default=None,
        help="Path to PE (default: Digibib5 install or fixture)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output .c path (default: artifacts/digibib5_entry_decompile.c under repo root)",
    )
    parser.add_argument(
        "--install-dir",
        default=os.environ.get("GHIDRA_INSTALL_DIR", r"C:\Program Files\ghidra_12.0_PUBLIC"),
        help="Ghidra installation directory",
    )
    args = parser.parse_args()

    try:
        import pyghidra
    except ImportError:
        print(
            "Missing pyghidra. Install with: uv sync --extra ghidra",
            file=sys.stderr,
        )
        return 2

    exe_path: Path
    if args.exe:
        exe_path = Path(args.exe)
    else:
        sys.path.insert(0, str(_repo_root() / "src"))
        from reversing_mcp.digibib_research import resolve_digibib_exe

        resolved, tried = resolve_digibib_exe(None)
        if resolved is None:
            print("Digibib5.exe not found. Tried:", file=sys.stderr)
            for p in tried:
                print(f"  {p}", file=sys.stderr)
            return 1
        exe_path = resolved

    if not exe_path.is_file():
        print(f"Not a file: {exe_path}", file=sys.stderr)
        return 1

    out_path = Path(args.out) if args.out else _repo_root() / "artifacts" / "digibib5_entry_decompile.c"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    proj_root = _repo_root() / "artifacts" / "ghidra_py_projects"
    proj_root.mkdir(parents=True, exist_ok=True)

    install = Path(args.install_dir)
    pyghidra.start(install_dir=install)

    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import TaskMonitor
    from pyghidra import open_program

    with open_program(
        exe_path,
        project_location=proj_root,
        project_name="Digibib5_pyghidra",
        analyze=True,
        nested_project_location=True,
    ) as flat:
        prog = flat.getCurrentProgram()
        fn = _resolve_entry_function(prog)
        if fn is None:
            print("No function found to decompile.", file=sys.stderr)
            return 3

        decomp = DecompInterface()
        if not decomp.openProgram(prog):
            print("DecompInterface.openProgram failed", file=sys.stderr)
            return 5
        decomp.toggleSyntaxTree(True)
        decomp.toggleCCode(True)
        res = decomp.decompileFunction(fn, 120, TaskMonitor.DUMMY)
        if not res.decompileCompleted():
            print(res.getErrorMessage(), file=sys.stderr)
            return 6
        c = res.getDecompiledFunction().getC()
        hdr = f"// {fn.getName()} @ {fn.getEntryPoint()}\n"
        out_path.write_text(hdr + str(c), encoding="utf-8")

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
