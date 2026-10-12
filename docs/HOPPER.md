# Hopper

[Hopper](https://www.hopperapp.com/) is a commercial disassembler/decompiler (roughly the
USD 100 range) for **macOS and Linux**. There is no Windows build.

**Status in reversing-mcp:** not wrapped directly. It is only reachable as a **provider of the
REA sidecar** (`rea_investigate(..., provider="hopper")`).

## On Windows: not available

REA reports `Hopper integration is not supported on win32` (verified 2026-10-11 on Goliath).
On Windows, REA's native provider ranking skips Hopper and goes to Ghidra, then IDA.
Do not buy Hopper for a Windows-only setup.

## On macOS / Linux

* REA setup can install Hopper with your approval (`just setup-rea`); it is REA's
  first-ranked native provider there.
* Select it explicitly with `provider="hopper"`, or omit `provider` for auto-select.
* Setup details: [REA.md](REA.md) section on native providers, and REA's upstream
  installation guide.

## References

* Engine overview: [ENGINES.md](ENGINES.md)
