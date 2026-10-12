# Detect It Easy (DiE)

[Detect It Easy](https://github.com/horsicq/DIE-engine) identifies the compiler, linker,
packer, protector and libraries of a binary from signatures. Free, fast (well under a second),
and the right first question before any disassembly: *what built this, and is it packed?*

**Status:** implemented and verified on the dev host (DiE 3.21, 2026-10-12).

## Use

| Where | Call |
|-------|------|
| MCP | `engine(operation="die", file_path="D:/apps/prog.exe")` |
| Gym | stage 1 (triage) runs it automatically |
| Inventory | `check_tools()` / Help -> Engines shows install state |

Returns `detections` (one row per signature: `type` compiler/linker/packer/protector/library,
`name`, `version`, `string`), `filetypes`, and `packed` (true when any detection is a packer,
protector or cryptor). Code: `src/reversing_mcp/engines.py` (`run_die`, `check_die`).

Example (Digibib5.exe): `Linker: Turbo Linker(2.25), Compiler: Borland Delphi(7)[Professional],
Library: Video for Windows (VFW)`, not packed.

## Install (Windows)

1. Download `die_win64_portable_<ver>_x64.zip` from the DIE-engine GitHub releases.
2. Extract to `D:\Dev\tools\die` (fleet convention), or anywhere and set `DIE_DIR`.
3. Lookup order: `DIE_DIR` -> `diec` on `PATH` -> `D:\Dev\tools\die\die\diec.exe`.
4. Check: `diec --version` prints `die <ver>`.

## References

* Engine overview: [ENGINES.md](ENGINES.md)
