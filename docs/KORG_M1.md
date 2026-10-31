# Korg M1 - Reversing Dossier (1988 Music Workstation)

Source trawl 2026-10-31. Local copies in `artifacts/korg-m1/`.

## Why your unit is likely fine

MIDI works = PSU + main CPU alive. Classic failure = internal battery dead
-> 64KB SRAM NVRAM (`0x00000-0x0FFFF`) loses programs/combis -> boots to
piano/INIT only. Fix: replace battery, factory reset, reload preload SysEx.

* Korg UK reload guide: https://support.korg.co.uk/en-US/reloading-the-m1-factory-preload-data-406887
* Factory preload SysEx (official): https://www.korg.com/us/support/download/software/1/139/3374
* Reset how-to: Sweetwater "How to Initialize (reset), and preload on the Korg M1/M1R"
* Videos: `TdU7IdaI-b0` (battery + reset), `Jwafj-yrGTs` (full SysEx restore)

## Manuals (local)

* `artifacts/korg-m1/M1_Owners_Manual.pdf` (7.9 MB, cdn.korg.com)
* `artifacts/korg-m1/M1_Owners_Manual_mirror.pdf` (6.0 MB, pulustudio)
* `artifacts/korg-m1/M1_Service_Manual.pdf` (2.3 MB, pulustudio)
* Full scan + OCR: https://archive.org/details/korg_M1_SERVICE_MANUAL (30.4 MB)
  Direct PDF: https://archive.org/download/korg_M1_SERVICE_MANUAL/M1_SERVICE_MANUAL_text.pdf
  Contents: Specs, Structural Diagram, Block Diagram, Circuit Diagram,
  P.C. Board layouts (KLM-1261/1263/1264/1266), Power supply, Jack plate,
  Parts list.

## Hardware map (from MAME `src/mame/korg/korgm1.cpp`, Angelo Salese / AJR)

* Main CPU: NEC V50 (`cpu/nec/v5x.h`), IPL ROM 128KB at `0xE0000-0xFFFFF`
* NVRAM 64KB at `0x00000-0x0FFFF` (battery backed)
* BeeCard slot 32KB window at `0x50000-0x5FFFF`
  Cards: MCR-02 128kB, MCR-03 256kB, MCR-04 1MB x4 banks.
  Ext pair: MPC-** program BeeCard + MSC-** PCM 19x2-pin expander.
* TG MB87402 x2 @ `0x1000-0x11FF` (PCM tone generators)
* VDF MB87404 @ `0x0100` / `0x0200` (filters)
* MDE MB87405 @ `0x0500` (multi effects)
* OPZ ports @ `0x0600/0x0700`, keyboard SCAN @ `0x0800`
* ADC0808 @ `0x0900` (aftertouch/velocity/joystick)
* CXD1095 PIO @ `0x0A00` (panel switch matrix select)
* HD44780 LCD 2x40 chars
* Panel matrix Y0-Y7: INT/COMBI/PROG/SEQ/GLOBAL/CARD/EDIT, cursor A-D,
  Bank Hold, keypad 0-9

## ROM / firmware sources

* MAME sets: `korgm1` Rev 19, `korgm1ex` v1.29 (planetemu.net, mdk.cab)
* Bulk dumps: https://dbwbp.com/index.php/9-misc/37-synth-eprom-dumps
* https://archive.org/download/vintage-synth-firmware-collection
* https://www.alexanderpeppe.com/eprom-bins
* Forum version note: firmware reports as #29 on INT+power; official line went to 1.19

## Already reversed?

Yes - no need to start from zero:

* MAME driver boots, panel + LCD emulated, sound partial (TG/VDF/MDE not cycle accurate)
* Vintage Emulator Studio (2026, KVR thread 633133): wraps MAME synths as AU/VST3
* Korg Collection M1 (official VST): bit-accurate, loads real SysEx - use as oracle
* Web editors: https://hsiboy.github.io/Korg-Librarian, https://knob.monster,
  https://bipluk.com, https://midi.toys, https://github.com/HelgeSverre/sysex-utility
* RE Lite (https://github.com/shahmir2002004/re-lite): "originally developed
  for analyzing Korg keyboard firmware and PCG/STY files"
* MAME Lua scripting: https://docs.mamedev.org/luascript/index.html (memory R/W,
  state hooks, `mame -autoboot_script`)

## Reversing path with this repo

1. Take MAME `korgm1.zip` IPL ROM -> `analyze_binary` / Ghidra headless,
   language = NEC V50 (8086-derived). See `docs/GHIDRA.md`.
2. `mame_read_memory_block` / `mame_get_registers` style live probes map to
   our `engine` + `rea_investigate` tools once a MAME bridge is added (see below).
3. three.js panel: `web_sota/src/pages/hardware-m1.tsx` - dimensions from
   Structural Diagram (~1047 x 340 x 110 mm), 61 keys, clickable Y-matrix
   buttons, LCD driven by HD44780 state or Web MIDI SysEx.

## Agentic MAME (2026 state)

* `ffxx68/mame_mcp_server` (Python + `mame_mcp_bridge.lua`, FastMCP, file IPC
  `mame_cmd.json`/`mame_rsp.json`): launch/stop/status/pause/reset/screenshot/
  read/write memory/registers/list inputs/send input/list roms/cheat/exec_lua.
  Closest to what we want - Lua bridge pattern is right.
* `dbowlin/CoCo3_MCP_Server` (TS, 5 stars): same idea scoped to TRS-80 CoCo3 -
  BASIC typing, disk mount, screenshots, memory R/W.
* `PlagueHO/arcade-janitor` (Rust, today): CleanMAME CLI + MCP for ROM folder
  hygiene via `mame.xml` + `catver.ini` - management, not live control.
* `M-J-Murray/MAMEToolkit` (Python, PyPI): RL wrapper - step gameplay, frames
  + memory, send actions. Pre-LLM but agent-compatible.
* None is fleet-grade (ports, Prefab cards, sampling, NSSM). Recommendation:
  build `mame-mcp` (or `mamecraft`) reusing ffxx68's Lua file-IPC bridge,
  replacing `mss` screenshots with MAME `-aviwrite`/`-snap`, adding fleet
  Start script + port claim + three.js frame view. Reversing use case
  (korgm1, not arcade) needs memory-map-aware tools, not just cheats.
