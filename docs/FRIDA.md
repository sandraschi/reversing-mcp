# Frida (planned)

[Frida](https://frida.re/) is a free dynamic instrumentation toolkit: it injects a JavaScript
agent into a running process and lets you hook functions, read arguments and dump buffers.

**Status:** **not wired yet.** This page describes the planned integration (roadmap phase 3).
Until then, the manual recipe in [DIGIBIB_REVERSING_GUIDE.md](DIGIBIB_REVERSING_GUIDE.md)
section 4.3 is the way to use it.

## Why it matters here

Static analysis tells you what code *could* run. Frida shows what *does* run. For Digibib5 the
fastest route to the DKI text decoder is to hook the Win32 file API, filter on `.DKI` paths,
and dump the buffers after each read - the decoded text shows up there without having to
reverse the decompressor first.

## Planned MCP surface

| Tool | Purpose |
|------|---------|
| `frida_trace` | Spawn or attach to a target, hook a list of exports (for example `kernel32!CreateFileW`, `kernel32!ReadFile`), filter by argument, return a bounded event log |
| `frida_script` | Run a user-supplied Frida JS agent against a target with a time limit, return its `send()` messages |

Design constraints:

* **Local targets only**, launched or attached by explicit path or PID - same consent rules as
  the CUA tour (see [CUA_DISASSEMBLY_COMBO.md](CUA_DISASSEMBLY_COMBO.md) section 7).
* Hard time and event-count limits; results returned as JSON, large dumps written to a file
  and returned by path.
* `frida` is an optional dependency: `check_tools()` reports it missing instead of failing.

## Install (for the manual recipe today)

```powershell
uv tool install frida-tools
frida --version
```

## References

* Frida docs: https://frida.re/docs/home/
* Engine overview: [ENGINES.md](ENGINES.md)
