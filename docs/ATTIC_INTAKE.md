# Attic Intake Form — frankendingus candidates (2026-10-31)

Copy this block once per find. Phone photos are fine. Send the filled blocks
back to chat (or drop in this folder as `intake-<name>.md`).

```markdown
## Find: <short name, e.g. "beige sewing machine">

- Where found / whose was it:
- Make + model (rear/bottom plate photo — THE most important item):
- MCU/CPU IDs visible without opening (or "unopened"):
- Condition (dust ok / battery crust / cracked / smells of fish = caps):
- Cables/manuals/floppies with it:
- Powered in last decade? (yes/no/unknown — NEVER test this now):
- Steve's verdict (keep/toss/funny):
```

## Trawl protocol (for Sandra AND Steve)

1. **Plates before power.** Rear/bottom label photo of everything with a chip
   in it. No model number = no triage = it waits.
2. **Power NOTHING.** Not "just to see". Forty-year-old caps and NiCds do not
   get curiosity voltage. Ever.
3. **Batteries out (if safe).** Loose AA/C/D packs: remove, bin separately.
   Internal NiCd soldered packs: LEAVE for the bench, note "internal pack".
4. **Bag the small stuff.** Floppies, ROM packs, cables, manuals, AC adapters
   go in a labeled bag WITH the machine. Orphans lose half their value.
5. **The sniff + shake test.** Fishy smell = dead caps (noted, not fatal).
   Rattle = loose screw or broken mount (noted). Sloshing = batteries (rule 3).

## What comes back to me

Filled blocks + plate photos. I return: rarity score, Tier placement,
and whether it jumps the queue (undumped ROMs always jump the queue).
```

```markdown
## Find: <example — delete me>

- Where found / whose was it: attic, north box, dad's
- Make + model: (photo attached)
- MCU/CPU IDs: unopened
- Condition: dusty, no crust visible
- Cables/manuals/floppies: power cable only
- Powered in last decade: unknown
- Steve's verdict: funny
```

## Bench photo protocol (phone is fine)

1. Whole board top + whole board bottom, flat, even light, no flash glare.
2. PSU section close-up, both sides.
3. Battery area close-up (even if it looks fine).
4. Macro of anything discolored, bulged, or crusty.
5. All labels, plates, and the 3 biggest ICs (for ID).
6. Caliper or ruler in frame on at least one shot (sizes parts later).

## Failure gallery (what you're looking at)

- **Electrolytic caps:** domed/scored top vent bulging, brown crust at the
  base, shrunken sleeve. Dead or dying — replace on sight in PSUs.
- **Tantalum beads** (yellow/blue drops): micro-cracks, scorch marks, blown
  open. They fail SHORT — rail-to-GND, the < 50 Ω test from the FrankenGRiD
  brief. Suspect #1 on dead 5 V rails.
- **Batteries:** white/green crust = alkaline leakage; NiCd packs leak too.
  Remove loose packs, leave soldered ones for the bench, photograph first.
- **Singed Leiterbahnen:** brown/black PCB, lifted solder mask, burnt smell.
  Trace is a symptom, not the disease — find the downstream short (often a
  tantalum) before re-power, then bridge with jumper wire.
- **Fishy smell:** cooked electrolytics or overheated plastic. Note it.

## Cap reading for replacement ordering

Copy one row per suspect cap. Markings carry everything:

```markdown
| RefDes | Type | µF | V | °C | Size (dxh / case) | Pitch | ESR class | Qty |
| C12 | electrolytic | 10 | 16 | 105 | 5x11 | 2.0 | low-ESR | 4 |
```

- **Electrolytics** print it all on the sleeve. **Tantalums** use codes
  (106 = 10 µF etc.) — photo the code, look it up, don't guess.
- Measure diameter × height and lead pitch with calipers — the replacement
  must fit the holes, not just match the numbers.
- Ordering rules: 105 °C near heat/PSU; **low-ESR** on switch-mode outputs;
  voltage equal or ONE step up; same capacitance (never "upgrade" µF blindly
  — timing and compensation circuits care); prefer 105 °C low-ESR
  Japanese-series stock for anything that runs warm.
- Head start: the M1 service manual parts list (`artifacts/korg-m1/`) already
  IS the cap BOM (16 V 10/100/470 µF rails etc.) — check there first for Korg.
