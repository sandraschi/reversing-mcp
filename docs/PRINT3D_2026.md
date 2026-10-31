# 3D printing late-2026: open vs closed, changers, metal, laser (2026-10-31)

No fleet doc covered this — now one does. Sourced from Oct 2026 press unless
marked stable knowledge. Home-lab lens throughout: small flat, one window.

## 1. The open/closed brouhaha (it went nuclear in 2026)

- **Bambu locked the doors.** Firmware updates compel Bambu-cloud account
  validation for init/config/local control; encrypted protocols block custom
  firmware and third-party slicer paths. Community verdict: bait-and-switch
  into a walled garden (Jan 2025 update started it, 2026 hardened it).
- **May 2026 escalation:** Bambu sent a DMCA cease-and-desist to the dev of
  `OrcaSlicer-bambulab`, a fork restoring the local print path. Dev deleted
  the repo (lawsuit costs vs corporation); Rossmann offered legal funds; the
  **Software Freedom Conservancy opened AGPL-violation proceedings**
  (Bambu Studio is AGPL, forked from PrusaSlicer ← Slic3r).
- **Prusa plays the counter.** Josef Prusa publicly called out the licensing
  violations; Prusa = open firmware, open slicer, local-first.
  Caveat, honestly: the Core One (late 2024) is no longer 100% open-licensed
  (clone protection) — firmware stays user-modifiable, hardware files don't.
- **Fleet rule from this:** never buy a printer whose local path depends on
  someone's cloud. LAN mode + OrcaSlicer/PrusaSlicer compatibility is a
  purchase gate, same rank as build volume. Our future OctoPrint/Moonraker
  bridge must assume hostile-vendor firmware and speak plain local protocols.

## 2. PRC vs US/EU (buying map, late 2026)

- **PRC volume makers** (Bambu, Creality, Elegoo, Anycubic): best price/speed,
  worst openness trajectory (see §1). Elegoo Centauri Carbon gets genuine
  community love as the post-Ender upgrade — but check its local-mode story
  before money moves.
- **Prusa (EU/CZ):** the open counterweight, Core One caveat noted. MMU3 and
  now the INDX path (below) keep multicolor inside the open tent.
- **US premium** exists but prices out of home-lab Wave 3; skip unless a
  specific machine (used LulzBot Tank-class) falls off a truck.
- Doctrine: openness is a spec, not a vibe. If the vendor can brick your
  workflow with a firmware push, you rent the printer.

## 3. Changers: AMS-style purge vs toolchanger (the 2026 debate)

- **Filament changers** (Bambu AMS & co, CoPrint upgrades, Prusa MMU3): one
  nozzle, purge old color on every swap = poop chute economics. Verdict
  crystallizing in Oct 2026 guides: under ~10 multicolor prints/month the AMS
  stays cheaper; past ~20, waste + time flip the math.
- **Toolchangers** (Bondtech INDX for CORE One: 8 materials, each its own
  nozzle + wireless induction heating, passive tools — zero purge): the
  waste-free endgame, at toolchanger money and complexity.
- **Robbie angle:** AMS automates spools inside the machine; a toolchanger
  needs nothing; but OUR lab already plans robot spool missions — an open
  single-material workhorse + Robbie as the changer is the cheap-and-cheerful
  third path. Dry box discipline matters more than changer brand.

## 4. Load-bearing: fiber at home, metal outside

- **Home ceiling: fiber-filled nylon.** PA-CF / PA-GF (and PET-CF) print
  genuinely structural brackets, gears, carrier plates on a €300–600 machine
  — requirements: hardened-steel nozzle, dry box (nylon drinks water), and
  ventilation. Carrier rev B in PA-CF is realistic on our own bench.
- **Metal stays a service job.** No home SLM in a small flat, full stop.
  Route: JLC3DP (SLA/MJF/SLM/FDM/SLS/BJ, "from $0.3"), PCBWay, RapidDirect,
  Unionfab — March/July 2026 comparisons exist, get 3 quotes per part.
  Debind-and-sinter filaments (316L-class) only make sense with a kiln
  partner; otherwise order SLM direct.
- **Rule of thumb:** prototype at home in PA-CF, prove the geometry, then
  either keep the plastic part (most brackets never need more) or send the
  STEP file out for one metal copy. Never iterate in metal.

## 5. Laser sideline (cheap, cheerful, ventilated or not at all)

- Diode lasers (xTool/Creality-Falcon class, EU stores exist) cut thin ply and
  engrave everything including our front panels and chassis labels. CO2/fiber
  stay outside services for now.
- **Ventilation is the purchase, the laser is the accessory:** no hood, no
  laser — same window duct as soldering (MAKERLAB.md). Acrylic/ABS/pusted
  plastics need real extraction, not a desk fan.
- Fleet gap, named: **no GRBL bridge MCP yet.** Vector path exists
  (`inkscape-mcp` laser template). The OctoPrint/Moonraker + GRBL bridges are
  the two missing MCPs in the makerlab queue.

## 6. Fleet cross-connects (today)

PrusaSlicer vendored in `externals/` (slice pipeline), FreeCAD + solidcraft
(design), `kicad-mcp` (carrier boards), Robbie PTZ/gripper (spool + inspect
missions), inkscape-mcp (laser vectors). Missing: printer-farm bridge,
laser bridge. Wave 3 buys the iron; the agents are already waiting.
