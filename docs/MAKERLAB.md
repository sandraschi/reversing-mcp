# Home makerlab plan — SOTA but cheap, small flat (2026-10-31)

Constraints (Sandra): no printer, no bench iron yet. Small flat, one big
window — bench goes next to it with exhaust/hood. Instruments: cheap and
cheerful, **USB-controlled, no screens/knobs** (headless by doctrine, not just
budget — the fleet MCPs already speak exactly this class).

## The punchline first

`oscilloscope-mcp` already drives the **Hantek 6022BE** and `logic-analyzer-mcp`
already drives **sigrok fx2la clones** — both have simulator modes for dry-runs.
The software side is bought and paid for. Buy the iron it already speaks.

## Buy order (doctrine: dump → prove → make)

**Wave 1 — Tier 0/Rule-zero kit (~€150):** EPROM programmer TL866II-class
(~€50, reads every ROM before power mods), digital calipers (~€20 — also
unblocks carrier rev B), Aneng AN8008-class DMM (~€25), ESD mat + tweezers
(~€20), silicone soldering mat. Pinecil V2 USB-C iron (~€30, open firmware).
*Rationale: dump-first and measure-first cost almost nothing.*

**Wave 2 — bench proof (~€150):** Hantek 6022BE USB scope (~€60–70, 20 MHz —
rails, clocks, reset nets, ripple), fx2la 8ch/24 MHz LA clone (~€12–15 —
UART/SPI/I2C, keyboard matrices, HD44780), Korad KA3005P-class bench PSU
(~€60, current limiting is NON-NEGOTIABLE per the FrankenGRiD soft-start
protocol). DSLogic-class upgrade only if 24 MHz ever runs out (it won't on
8086/Z80/6502-era buses).
*Rationale: every Tier 1 revive needs scope trace + LA capture. Rehearse in
simulator mode, run once on iron.*

**Wave 3 — make (~€250–400):** enclosed-core printer with dry box (Bambu-class
A1 mini or Prusa MK4S-kit depending on budget month), Robbie spool/inspect
missions after. Diode laser LAST — it shares the window exhaust, and the hood
must exist before it arrives.

## Bench + exhaust (awaiting floor plan)

One bench, window-adjacent: fume path is short rigid duct to the window
(DIY acrylic hood + inline fan; KOTTO-class absorber as interim). Laser and
soldering SHARE the hood — schedule, don't duplicate. 4-40 and M3 hardware in
one organizer; NiCd/corrosion quarantine tray separate from food-adjacent
anything. Noise/dust curfew rule for the flat to be agreed, not discovered.

## What NOT to buy

64-channel GHz logic analysis (a whole lab's budget for signals our oldest
CPU can't make), a screened scope with knobs (the laptop is the screen, the
agent turns the knobs), any instrument without Linux/sigrok support, a laser
before the hood exists.
