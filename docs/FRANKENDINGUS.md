# FRANKENDINGUS Doctrine — every clunker with a CPU is a candidate (2026-10-31)

Coinage: Sandra. Reading: バカを見る (the XT taught us). Rule: no more
attic losses without triage first.

## 1. The XT reframing

Regret budget should track *irreplaceability*, not nostalgia:

```
rarity = (no MAME/86Box driver) x (no public ROM dump) x (custom silicon)
```

- IBM XT: rarity ~ 0. Fully emulated, BIOS everywhere, parts ubiquitous.
  Losing one stings emotionally, costs ~€200 to reconstitute. Forgive yourself.
- GRiDCase 1520 plasma ROMs: dumped, but barely. Compass 1100/1107/1121/1131:
  NO dumps — losing one of those would be the real バカ.
- An early automated sewing machine or Zojirushi kettle with a mask-ROM MCU
  nobody ever read out: rarity HIGH. These outrank another XT every time.

## 2. The ladder (never skip down without a written reason)

- **Tier 0 — Document.** Photos, plates, manuals hunt, ROM dumps FIRST
  (programmer/clip before any power mods). Cost: an afternoon. Skipping this
  is how dumps stay missing forever.
- **Tier 1 — Revive.** Clean, recap, stock boot. The machine runs as itself.
- **Tier 2 — Augment.** Pi co-processor over non-destructive taps (serial,
  parallel, sensor sniffing). Original silicon still in charge.
- **Tier 3 — Eviscerate.** Carrier + implant, full port/sensor/actuator
  breakout. Requires a dead-rail justification (Branch B rule) AND bagged,
  tagged originals AND a working oracle to diff against.

No implant without an oracle: MAME driver, 86Box config, or a stock-boot video
with known inputs. If you can't tell correct from broken, you're not modifying,
you're destroying.

## 3. Why sewing machines and kettles are excellent targets

- **Early automated sewing machine:** needle-bar position sensors, feed-dog
  steppers, pattern ROMs, button matrix, motor drivers. The full
  sense-compute-actuate loop in one chassis — the actuator story our synth
  and laptop jobs don't have. Pattern ROM dump = new "firmware" nobody has.
- **Zojirushi kettle:** thermistors, keep-warm PID-ish logic, water-level
  sensing, a tiny MCU with mask ROM. The sensor story: thermal profiling with
  modern logging against the stock controller's behavior. Safest high-voltage
  practice in the fleet (mains + water + heat — treat with full respect).

## 4. Fleet mapping (already built, reuse it)

| Ladder step | Fleet tool |
|---|---|
| ROM dump analysis | `reversing-mcp` (`analyze_binary`, Ghidra headless, `engine`) |
| Live control / oracle | `rust-mame-mcp` `Command` bus + per-machine profile module |
| Carrier / breakout PCB | `kicad-mcp` stable lane (DRC/exports) + pcbnew generators |
| Panel / chassis view | three.js Hardware views in `web_sota` |
| Brain (Branch A chatbot) | Pi + local small LLM over the period-correct serial line |
| Tier 1 rail/clock proof | `oscilloscope-mcp` (PicoScope 2/3/5/6000, Hantek 6022; simulator for dry-runs) — rails, oscillators, reset nets, ripple |
| Tier 1 bus sniffing | `logic-analyzer-mcp` (sigrok + simulator, ports 10985/10989) — `la_capture` + `la_decode` on keyboard matrices, UARTs, card buses |

Bench rule: every Tier 1 revive gets a scope trace (rails + clocks) and, for
digital boards, an LA capture before any chip is declared dead. Both servers
default to simulator mode — rehearse the capture sequence headless, then run
it once on iron. Their READMEs already cross-link `kicad-mcp` for net names:
probe the net the schematic names, not the pin that looks guilty.

Profiles so far: `korgm1`, `grid1101`, `gridcase1520`. Next profiles get cut
when a candidate clears Tier 0 with a model number — no invented entries.

## 6. The trajectory (the pipeline view of the same doctrine)

**Trawl attic → find interesting dead hw → analyze → repair → improve →
clone → raspi → LLM.** Each arrow has an owner:

| Stage | Means | Fleet home |
|---|---|---|
| Trawl | plates, photos, no power | `ATTIC_INTAKE.md` |
| Find | rarity score, tier placement | `FRANKENDINGUS.md` §1–2 |
| Analyze | ROM dumps, Ghidra, scope/LA proof | `reversing-mcp`, bench MCPs |
| Repair | stock boot first (Hoover: `HOOVER_REPAIR.md`) | Tier 1, bench rule |
| Improve | non-destructive taps, better caps, quiet fans | Tier 2 |
| Clone | emulation oracle (MAME/86Box/stock video) | `rust-mame-mcp` profiles |
| Raspi | carrier + implant, reversible default | `kicad-mcp`, carrier dirs |
| LLM | chatbot face over the period-correct line | Branch A pattern |

Nothing advances a stage without the previous stage's receipt: no repair
without analysis, no implant without an oracle, no LLM without a transport.

## 5. Intake (awaiting model numbers, no work starts without them)

1. Early automated sewing machine — need make/model, MCU IDs on sight.
2. Zojirushi kettle — need model, controller board photos.
3. Next attic sweep: photograph plates FIRST, power NOTHING, triage here.

Standing order: **all microcontrollers and their ROMs are fair game.**
Read them before they rot; emulation before implantation; reversibility by
default; evisceration only with a dead rail and a bagged original.
