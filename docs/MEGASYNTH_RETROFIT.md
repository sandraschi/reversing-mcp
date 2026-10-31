# MEGASYNTH Retrofit Dossier — Korg M1 + GRiD (2026-10-31)

Sources: `artifacts/korg-m1/M1_Service_Manual.pdf` (OCR read 2026-10-31),
MAMEDEV wiki + `gridcomp.cpp`/`korgm1.cpp`, BPB/VES, raspberrypi.com, CLAP project.

## 1. M1 measured baseline (from the manual, not memory)

- Chassis: **1058 W x 356 D x 110 H mm, 13.5 kg, 11 W**. Keybed FS-61 (61 keys).
- Logic boards: **KLM-1266** (CPU/core), KLM-1261 (DAC PCM54HP + BeeCard),
  KLM-1262 (front panel), KLM-1263 (jacks), KLM-1264 (card slots).
- Silicon on KLM-1266: **uPD70216 (NEC V50)**, TG MB87402 + MB87403,
  VDF MB87404 x2, MDE MB87405, PIO CXD1095Q, mask ROM **MB83512** (IPL),
  SRAM + **CR2032** (the killer), clock KXO-01 32 MHz.
- PSU KLM-1267/68/69 rails: **+5 V 1.2 A, +12 V 0.3 A, -12 V 0.13 A**.
- Human I/O to preserve: 2x40 backlit LCD module (313001300), joystick ass'y,
  34 panel tact switches (SKHHAN), 2 slide VRs, MCR BeeCard + 19x2 PCM slots.
- Fasteners are all catalogued (CT-B-ZMC 3x8/4x10 etc.) — disassembly is safe.

## 2. Carrier-plate strategy (reversible — bag, tag, keep every KLM)

1. Remove KLM-1266 + PSU secondary, keep FS-61, panel, LCD, jacks, chassis grounds.
2. New carrier PCB on the KLM-1266 standoffs with:
   - CM5 socket (55x40 mm) or Pi 5 mounting holes (85x56 mm) + NVMe (CM5Lite + HAT)
   - Keybed scan: replicate SCAN-port matrix on GPIO + MCP23017 expanders
   - LCD: HD44780 driven **directly from GPIO** (4-bit mode, 5 V-tolerant level shift)
   - Panel switches: same expander bus (Y0..Y7 select lines map 1:1 to `korgm1::PANEL_MATRIX`)
   - Audio: I2S DAC HAT footprint (PCM54HP stays with the stored KLM-1261)
   - MIDI: DIN jacks rewired to UART + USB class-compliant gadget port
   - Power: reuse the transformer, new regulation for 5 V/3 A (Pi) + LCD bias
3. Draw it in KiCad against the KLM-1266 outline + standoff positions from the
   P.C. BOARD pages (sec. 5). No cuts to the steel.

## 3. Board verdict: newest Raspi or not?

**Short: CM5 for the implant, and know what it can't do.**

- State of正面: Pi 5 (BCM2712 4x Cortex-A76 2.4 GHz, up to 16 GB) and
  **Compute Module 5 (55x40 mm, 2–16 GB RAM, 16–64 GB eMMC or Lite for NVMe,
  from $45)**. CM5 + custom carrier = the professional implant; Pi 5 = the prototype.
- The catch for a *megasynth*: commercial VST3 oracles (Korg Collection, Roland
  Cloud) ship **x86-64 Windows/macOS** builds. VES ships macOS/Windows/**Linux x86_64**
  — no ARM Linux build advertised. On ARM the stack that runs natively is:
  MAME-direct (builds clean on ARM) + open DSP (Dexed, OB-Xd, Vital, Surge XT —
  all ARM-native CLAP/VST3) + anything you compile. That covers ~15 of the 20
  with zero license fog.
- If the brief is "all 20 verbatim incl. commercial VSTs", the implant is an
  **x86 mini-ITX/mini-PC board** (used thin-client boards are cheap and 12 V).
  11 W M1 PSU won't feed it — budget a new internal brick either way on x86.
- Recommendation: **CM5 8 GB Lite + NVMe carrier for the M1** (silent, cool,
  boots MAME + open stack in seconds), Pi 5 8 GB on the bench for development.
  x86 only if a specific commercial VST is non-negotiable.

## 4. VST3 / CLAP reversing state (for the DAW repos)

- **CLAP is the home turf**: MIT-licensed open ABI (`free-audio/clap`),
  `clap-validator` + info tools in CI, hosts incl. Bitwig/Reaper/FL/Studio One,
  `free-audio/clap-wrapper` converts CLAP <-> VST3/AU, 2026 deep-dives rate
  JUCE 8 / iPlug2 / DPF / Cmajor as the build paths. Build CLAP-first, wrap to
  VST3 — no legal fog, validator-provable.
- **VST3 hosting is solved openly**: JUCE hosts VST3, `yabridge` runs Windows
  VSTs on Linux (the pattern for an x86 megasynth running commercial ROM-oracles
  under Linux). Steinberg's SDK license bites on *distribution*, not on hosting.
- **Reversing commercial VST DSP**: standard PE/ELF pipeline — exactly what
  `reversing-mcp` (`analyze_binary`, Ghidra headless, `engine` DiE/capa) does.
  Rule: learn the wire format (params/state/chunks), never lift code — clean
  room, oracle-tested (A/B the original like VES does with MAME drivers).
- Proposed DAW-repo work: `clap-validator` in CI for anything we ship,
  SysEx/state-chunk maps per synth in the dossier, VES as the listening oracle.

## 5. GRiD attic unit — identification + demo plan

- Likely **Compass 1101 (1982)** or, if the plate says 1985, **Compass II 1109**
  or **GRiDCase 1530**. Check the rear plate before ordering anything.
  Compass 1101: Intel 8086, **320x240 amber electroluminescent** (reads as red
  plasma in memory), 384 KB bubble RAM, GRiD-OS, 1200 bps modem, IEEE-488.
- **Already emulated**: MAME `grid1101` in `src/mame/gridcomp/gridcomp.cpp`,
  in-tree since 0.187, current at 0.289 — and `rust-mame-mcp` can launch it
  today (`launch --rom grid1101`, ROMs not distributed, dump your own).
- Implant: Pi Zero 2 W (or CM5 if sharing the carrier design) + HDMI-to-LVDS
  or composite overlay **behind the EL glass if the tube still strikes**.
  EL needs ~100+ V drive — if the inverter is dead, do NOT hand-wire mains-era
  HV in front of an audience; fit a modern transflective LCD behind the bezel
  and keep the dead tube with the unit's papers.
- The funny demo, staged: 1) open the clamshell on stage, 2) boot real GRiD-OS
  (MAME on the implant, on the original glass), 3) `mame_exec_lua` hands off
  to a local chatbot (Pi 5-class runs a 3B Q4 model; smaller Pi = thin client
  to the laptop over the modem-port-turned-WiFi joke), 4) it introduces itself
  *as the 1985 machine*. Dumbfounded audience guaranteed; total BOM < €120
  if the glass still lights.
