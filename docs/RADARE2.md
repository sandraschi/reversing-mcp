# radare2 Integration

[radare2](https://github.com/radareorg/radare2) (r2) is a free, scriptable disassembler and
analysis framework. reversing-mcp calls it as a subprocess; there is no `r2pipe` dependency.

**Status:** implemented but **unverified on the dev host** (r2 is not installed on Goliath).
The command lines below are what the code runs; the output parsing has not been checked
against a current r2 release.

---

## 1. What works

| Operation | MCP tool | Command run | Returns |
|-----------|----------|-------------|---------|
| Detection | `check_tools()` | `r2 -v` | first line of version output |
| Binary info | `analyze_binary(file, ['r2'])` | `r2 -A -q -c i <file>` | raw `i` output as `info` |
| Function list | `find_functions(file, 'r2')` (also the `auto` default) | `r2 -A -q -c afl <file>` | `{address, size, name, tool: "r2"}` per function |

All calls have a 30 s timeout (detection: 5 s). Code: `src/reversing_mcp/analyzers.py`
(`_check_r2`, `_analyze_with_r2`, `_find_functions_r2`).

## 2. Install (Windows)

1. Download the Windows release zip from the radare2 GitHub releases page.
2. Extract it and put its `bin` directory on `PATH`.
3. Check: `r2 -v` in a fresh shell, then `check_tools()` should show `r2` available.
4. Restart the backend (`start.ps1`) - detection runs per request, but the process inherits
   `PATH` at start.

## 3. Known doubts (check on first real run)

* **`afl` column layout.** `_find_functions_r2` reads column 1 as the address, column 2 as the
  size and the rest as the name. Recent r2 releases print more columns for `afl` (for example a
  basic-block count before the size). If sizes look like small integers, the parser is reading
  the wrong column; switch the command to `aflj` (JSON) and parse that instead.
* **`-A` on large binaries** runs full auto-analysis and can exceed the 30 s timeout. Use
  Ghidra for anything big.

## 4. Rizin / Cutter

[Rizin](https://rizin.re/) is a radare2 fork (and the engine under the Cutter GUI). Its CLI is
`rizin`, not `r2`, so it is **not** detected. Adding it would mean a second probe and the
`rizin -A -q -c` equivalents.

## 5. References

* radare2 book: https://book.rada.re/
* Engine overview: [ENGINES.md](ENGINES.md)
