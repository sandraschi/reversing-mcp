# GRiD Attic Revive — GRiDCase 1520 to Chatbot (2026-10-31)

**Correction 12:40 UTC: the attic unit is a GRiDCase 1520, not a Compass.**
The 1520 is an IBM-PC/AT-compatible 286 machine — different architecture,
different OS, different plan. Machine facts: `rust-mame-mcp`
`mame_gridcase1520_profile`. The Compass `grid1101` profile stays in the repo
as a second machine, clearly labeled — it does NOT describe this unit.

Companion doc (Gemini, today): Drive `FrankenGRiD Project Brief & Hardware
Engineering Guide` — Branch A/B plan, HV + tantalum safety, KMK keyboard
firmware, power/thermal/RF. This runbook adopts its safety section by
reference and corrects its hardware identity below (§1).

## 0. Rule zero: do NOT power it on yet

A 40-year-old NiCd pack does not sleep — it leaks alkaline electrolyte onto the
motherboard. Step one is always mechanical, never electrical:

1. Photograph every angle + the rear model plate first (needed for §1 anyway).
2. Open the case, find the battery pack, remove it. Look for green/white crust
   on terminals, traces, and the keyboard MCU area (Intel 8741).
3. If crust: neutralize (mild acid + isopropanol routine), soft brush, inspect
   for eaten traces under magnification. Power comes *after* the board is clean.
4. Check the EL inverter area for bulging caps. The display drive is
   high-voltage — never probe it live and never in front of an audience.

## 1. Identify the unit (2 minutes, decides everything)

- Attic unit: **GRiDCase 1520** — Intel **80286** @ 10 MHz (+80287 socket),
  1 MB (up to 8 MB), **gas-plasma** version (an LCD version also shipped),
  1.44 MB floppy + 40 MB HDD, serial + parallel, **MS-DOS IBM-compatible**,
  Micro Switch ST keyboard. Successor of the Compass line, first Case 1985.
- Note: the FrankenGRiD brief says "GRiDCase 3 / 8086 / 640x200" — that does
  NOT match the 1520 (286 AT-class). Trust the rear plate, not the brief:
  if the plate says 1520, the 286 facts above rule. Branch aperture dims
  (210x85 mm) and "680x200" figures in the brief need re-measuring anyway.
- Preservation check: archive.org already hosts 1520 LCD + plasma ROM dumps
  (300778-21/300777-21, 300778-22/...) and a 720 KB system disk — your job is
  to dump YOUR unit's ROMs (same part numbers expected) before modding.
  Dumping your own hardware is the legal path everywhere.
- Compass line (1101 etc.) is covered separately by `mame_grid1101_profile`
  and MAME `gridcomp.cpp` — different OS (GRiD-OS), different plan.

## 2. Prove the software before touching the hardware

No MAME driver exists for the 1500 series (checked 2026-10-31) — so the
oracle path is different from the Compass:

1. **Generic-286 probe (unverified, next bench task):** 86Box/PCem-class
   emulator + YOUR dumped 1520 ROMs + the archive.org 720 KB system disk
   (MS-DOS + GRiD utils) as reference. If DOS boots, you have your oracle.
2. **Branch A needs no emulator at all:** MS-DOS + Kermit on the real 1520,
   serial to the Pi (`serial-getty`, 19200 8-N-1 VT100 per the FrankenGRiD
   brief §4). Period-correct, non-destructive, and it IS the chatbot demo
   transport — the glass becomes the bot's face on day one.

## 3. Implant plan (reversible, like the M1 carrier)

- Keep: magnesium clamshell, EL glass + bezel, keyboard assembly, GRiDROM slots.
- If the tube strikes: drive it. If the inverter is dead: modern transflective
  LCD behind the original bezel, dead tube retained with the papers.
- Compute: Pi Zero 2 W minimum, Pi 5 8 GB for the chatbot leg. Keyboard: keep
  the 8741 matrix, scan it from GPIO (or USB-convert and keep the MCU powered
  as a curiosity — it draws nothing).
- Bubble RAM is non-volatile and likely *still holds data* — image it before
  first write. Someone's 1985 files may be in there; that reveal is half the demo.

## 4. The chatbot demo (4 beats, ~6 minutes)

1. **The relic**: clamshell opens on stage. "1982. 8086. It went to space on
   the Shuttle." Boot real GRiD-OS — on the implant, on the original glass.
2. **It remembers**: show the bubble-RAM contents (or the MAME oracle of them).
   Forty-year-old files, live.
3. **It talks**: open the terminal. The prompt answers — a local small model
   (3B Q4 runs on a Pi 5 8 GB; smaller Pis thin-client over WiFi through the
   modem port, which is a joke worth making out loud). It introduces itself
   *as the 1985 machine* and roasts modern laptops.
4. **The receipt**: `mame_grid1101_profile` on screen — every chip it just
   impersonated, named. Dumbfounded audience, Q&A, done.

## 5. BOM sketch (< €120 if the glass lights)

Pi Zero 2 W / Pi 5 + SD + level shifters + LCD fallback + connectors + printed
bezel shims. The expensive part is patience, not parts.

Preservation order stands: **dump > clean > emulate > implant > perform.**
