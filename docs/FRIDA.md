# Frida

[Frida](https://frida.re/) is a free dynamic instrumentation toolkit: it injects a JavaScript
agent into a running process and lets you hook functions, read arguments and dump buffers.

**Status:** implemented and verified on the dev host (Frida 17.23.3, 2026-10-12). Feeds Gym
stage 2 (oracle capture): *what does the original read and write?*

## Why it matters here

Static analysis tells you what code *could* run. Frida shows what *does* run. For Digibib5 the
fastest route to the DKI text decoder is to hook the Win32 file API, filter on `.DKI` paths,
and dump the buffers after each read - the decoded text shows up there without having to
reverse the decompressor first.

## Use

| Operation | Call | Returns |
|-----------|------|---------|
| Trace exports | `engine(operation="frida_trace", target="D:/apps/prog.exe", functions=["kernel32.dll!CreateFileW", "kernel32.dll!ReadFile"], arg0_filter=".dki", duration_s=30, confirm=True)` | one event per call: `fn`, `arg0` (read as a string; UTF-16 for `...W` exports), `args[1..3]` as hex, `tid`, `t` |
| Custom agent | `engine(operation="frida_script", target=..., source="send(Process.enumerateModules().length)", confirm=True)` | the agent's `send()` payloads |
| Attach instead of spawn | pass `pid=<n>` instead of `target` | same |

Every result also carries `hooked`, `hook_errors`, `script_errors`, `event_count`, `dropped`,
`process_exited` and `elapsed_s`. Limits: `duration_s` 1-120, `max_events` 1-5000; the session
ends early when the process exits or the cap is hit. Spawned targets are killed at the end;
attached processes are detached and left running. Code: `src/reversing_mcp/engines.py`
(`frida_trace`, `frida_script`).

Hook specs are `module!export`. Frida 17 resolves them per module
(`Process.getModuleByName(m).getExportByName(e)`); the pre-17 static `Module.findExportByName`
API is gone.

## Safety

* `confirm=True` is required: spawning **executes** the target with your permissions, attaching
  instruments a live process. VM or a target you trust only - same rules as the CUA tour
  ([CUA_DISASSEMBLY_COMBO.md](CUA_DISASSEMBLY_COMBO.md) section 7, [GYM_SPEC.md](GYM_SPEC.md)
  section 7).
* `frida_script` runs arbitrary agent code inside the target. Treat the source like code you
  execute.

## Install

```powershell
uv sync --extra dynamic          # frida Python binding for the server (required for engine frida_*)
uv tool install frida-tools       # optional: frida / frida-trace CLIs for manual work
```

Without the binding, `engine(operation="frida_*")` returns "frida not installed" and
`check_tools()` lists Frida as unavailable.

## References

* Frida docs: https://frida.re/docs/home/
* Manual recipe: [DIGIBIB_REVERSING_GUIDE.md](DIGIBIB_REVERSING_GUIDE.md) section 4.3
* Engine overview: [ENGINES.md](ENGINES.md)
