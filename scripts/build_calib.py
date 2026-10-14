"""Build the hermetic calibration targets (tests/fixtures/calib/*.c -> *.exe).

Finds MSVC cl.exe under VS2022/2019 Community/Pro/Enterprise/BuildTools;
skips honestly (exit 3) when no compiler exists so CI on other platforms
stays green. Binaries are checked in (like test_pe.exe) once built.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CALIB = REPO_ROOT / "tests" / "fixtures" / "calib"
TARGETS = ["calib_win32", "calib_canvas"]


def find_msvc() -> tuple[Path, Path] | None:
    """(cl.exe, msvc-version-dir). Self-configures INCLUDE/LIB (VsDevCmd does
    not survive non-cmd shells, so we wire the env ourselves)."""
    import os

    roots = [
        Path(r"C:\Program Files\Microsoft Visual Studio"),
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio"),
    ]
    for root in roots:
        for edition in ("2022", "2019"):
            for sub in ("Community", "Professional", "Enterprise", "BuildTools"):
                tool = root / edition / sub / "VC" / "Tools" / "MSVC"
                if not tool.is_dir():
                    continue
                versions = sorted((p for p in tool.iterdir() if p.is_dir()), reverse=True)
                for ver in versions:
                    cl = ver / "bin" / "Hostx64" / "x64" / "cl.exe"
                    if cl.is_file():
                        kits = Path(r"C:\Program Files (x86)\Windows Kits\10")
                        sdks = (
                            sorted((kits / "Include").glob("10.*"), reverse=True) if (kits / "Include").is_dir() else []
                        )
                        if not sdks:
                            continue
                        sdk, sdk_ver = sdks[0].parent.parent, sdks[0].name
                        inc = [str(ver / "include")]
                        lib = [str(ver / "lib" / "x64")]
                        for area in ("ucrt", "um", "shared"):
                            inc.append(str(sdk / "Include" / sdk_ver / area))
                        for area in ("ucrt", "um"):
                            lib.append(str(sdk / "Lib" / sdk_ver / area / "x64"))
                        sep = os.pathsep
                        os.environ["INCLUDE"] = sep.join(inc) + sep + os.environ.get("INCLUDE", "")
                        os.environ["LIB"] = sep.join(lib) + sep + os.environ.get("LIB", "")
                        os.environ["PATH"] = str(cl.parent) + sep + os.environ.get("PATH", "")
                        return cl, ver
    return None


def main() -> int:
    found = find_msvc()
    if found is None:
        print("build_calib SKIP: no MSVC + Windows SDK found (binaries must be committed by a Windows dev).")
        return 3
    cl, _ver = found
    print(f"build_calib: using {cl}")
    for name in TARGETS:
        src = CALIB / f"{name}.c"
        out = CALIB / f"{name}.exe"
        proc = subprocess.run(
            [str(cl), "/nologo", "/O1", f"/Fe{out}", str(src), "user32.lib", "gdi32.lib"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if proc.returncode != 0 or not out.is_file():
            print(f"build_calib FAILED for {name}:\n{proc.stderr[-2000:]}")
            return 2
        print(f"build_calib: {name}.exe ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
