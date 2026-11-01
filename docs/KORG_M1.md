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

## Sound Architecture: Why Subtractive Minisynths Fail

The Korg M1 is **fundamentally an AI PCM Rompler**, not a subtractive analog synth:
* **4 MB PCM Mask ROMs**: Two 2MB mask ROMs (`m1_pcm1.bin`, `m1_pcm2.bin`) holding 100 16-bit 32 kHz raw acoustic multi-samples and 44 drum samples.
* **Tone Generator ASICs**: Dual Fujitsu MB87402 chips stream PCM samples with polynomial interpolation, feeding into MB87404 Variable Digital Filters (VDF) and MB87405 24-bit Multi-Digital Effects (MDE).
* **The "Distorted Piano" Trap**: Iconic patches like `03: Ooh / Ahh`, `00: Universe`, and `01: Piano 16'` are based on multi-sample recordings of human vocalists and acoustic grand pianos. Attempting to synthesize them with simple subtractive sine/saw oscillators and standard biquad filters on a minisynth produces synthetic buzzy pings and distorted piano-like impulses rather than human vocal formants or authentic hammer strikes.

## The Factory Preload Soundbank (MPC-00P / 64 KB NVRAM)

Full bank data is mapped in `web_sota/src/data/korg-m1-bank.ts`:
* **100 Factory Programs (Prog 00–99)**:
  - `00 Universe`: Choir breath chiff (`PCM #08`) + sparkling bell wave (`PCM #14`) + hall reverb.
  - `01 Piano 16'`: Compressed acoustic hammer multi-sample (`PCM #00`), the 90s house staple.
  - `02 Brass 1`: Acoustic-synthetic brass section (`PCM #02`).
  - `03 Ooh / Ahh`: True vocal choir multi-samples (`PCM #08 Choir Ooh` + `PCM #09 Choir Aah`) sweeping vocal formants.
  - `06 Fretless`: Singing electric fretless bass (`PCM #15`).
  - `16 Pick Bass` & `46 Slap Bass`: Electric bass thumb slap and plectrum transients.
  - `17 Organ 2`: 90s UK garage tonewheel organ (`PCM #06`) with percussive key click (`PCM #07`).
  - Through `99 Please~~~~`: Hidden easter egg patch with reverse reverb.
* **100 Factory Combinations (Combi 00–99)**:
  - Multi-timbral 8-part splits and layers (`00 Film Score`, `01 Harvest`, `02 Metropolis`, `04 The Strings`, `10 Voices`, etc.).

## Already reversed? The VST3 & Emulation Landscape

Yes - no need to start from zero:

* **Korg Collection M1 (Official VST3 / AU / AAX / Standalone)**:
  - The commercial reference oracle.
  - Korg's software team reverse-engineered their own V50 assembly firmware into 64-bit native C++.
  - Uses the raw uncompressed 4MB PCM sample data dumps, bit-accurate MB87404 VDF filter math, and MB87405 MDE 24-bit multi-effects.
  - Contains all 100 Programs, 100 Combinations, PLUS all 19 ROM expansion card sets (>3,300 patches).
  - Native bit-accurate SysEx import/export (`.syx`).
* **Vintage Emulator Studio (VES) by Autodafe (Open Source JUCE VST3)**:
  - GitHub: `antoniograzioli/VintageEmulatorStudio` (AGPL-3.0).
  - Wraps MAME's `src/mame/korg/korgm1.cpp` NEC V50 core inside a JUCE VST3 plugin container for DAW hosting.
  - Does not bundle ROMs due to copyright; user supplies MAME `korgm1.zip`.
  - Emulates CPU, panel matrix, and LCD at 100%; Fujitsu ASIC audio rendering is in active community development.
* **MAME Driver (`src/mame/korg/korgm1.cpp`)**:
  - Boots NEC V50 CPU, maps 64KB NVRAM, emulates HD44780 LCD, panel matrix Y0–Y7.
* **Web MIDI DAW Bridge**:
  - In `web_sota/src/pages/hardware-m1.tsx`, Web MIDI Output connects to virtual MIDI cables (`loopMIDI`) to drive external VST3 instances or hardware M1s with Note On/Off and instant Program Change `0xC0 [prog_num]`.
* **SysEx Preload Data Restoration (`M1_PRELOAD.SYX`)**:
  - Format: `F0 42 30 19 4C [Data Blocks] F7` (64 KB NVRAM `0x00000–0x0FFFF`).
  - Restores all 100 Programs and 100 Combinations after CR2032 battery replacement.
* **Web editors & Librarians**: https://hsiboy.github.io/Korg-Librarian, https://knob.monster,
  https://bipluk.com, https://midi.toys, https://github.com/HelgeSverre/sysex-utility
* **RE Lite (https://github.com/shahmir2002004/re-lite)**: "originally developed
  for analyzing Korg keyboard firmware and PCG/STY files"
* **MAME Lua scripting**: https://docs.mamedev.org/luascript/index.html (memory R/W,
  state hooks, `mame -autoboot_script`)

## Reversing path with this repo

1. Take MAME `korgm1.zip` IPL ROM -> `analyze_binary` / Ghidra headless,
   language = NEC V50 (8086-derived). See `docs/GHIDRA.md`.
2. `mame_read_memory_block` / `mame_get_registers` style live probes map to
   our `engine` + `rea_investigate` tools once a MAME bridge is added (see below).
3. three.js panel: `web_sota/src/pages/hardware-m1.tsx` - dimensions from
   Structural Diagram (~1047 x 340 x 110 mm), 61 keys, clickable Y-matrix
   buttons, LCD driven by HD44780 state or Web MIDI SysEx, complete 100 Program / 100 Combi browser,
   and live Web MIDI Output routing to external VST3 / DAW.

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
