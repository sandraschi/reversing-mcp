# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for reversing-mcp backend sidecar (fleet standard)."""

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

pkg_name = "reversing_mcp"

datas = [(f"src/{pkg_name}", pkg_name)]
for pkg in (
    "fastmcp",
    "mcp",
    "fastapi",
    "uvicorn",
    "pydantic",
    "starlette",
    "httpx",
    "prefab_ui",
    "opentelemetry-api",
):
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "_strptime",
    "_datetime",
    "joserfc",
    "joserfc.jwk",
    "joserfc.jwt",
    "cachetools",
    "mcp.types",
    "jaraco.text",
    "jaraco.context",
    "jaraco.functools",
]
try:
    hiddenimports += collect_submodules("reversing_mcp")
except Exception:
    pass
try:
    hiddenimports += collect_submodules("key_value")
except Exception:
    pass

a = Analysis(
    ["run_server.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pandas", "scipy", "torch", "tensorflow"],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="reversing-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
