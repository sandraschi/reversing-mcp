# Megasynth 20-machine shortlist (2026-10-31)

All ROM-dumped. "MAME status" is the driver's audio state; "Playable" is how
you hear it today. Both columns matter — never confuse them.

## Keys / workstations

| # | Machine | MAME status | Playable today |
|---|---|---|---|
| 1 | Korg M1 / M1EX | korgm1 boots, panel mapped, sound partial | Korg Collection (oracle) |
| 2 | Ensoniq ESQ-1 | Semi ("doesn't sound so bad actually") | VES |
| 3 | Ensoniq SD-1 | driver exists | VES + dedicated MAME-based VST |
| 4 | Casio CZ-101 | driver exists, sound No | VES |
| 5 | Casio CZ-1 | — | VES |
| 6 | Sequential Prophet-5 | driver exists, sound No | VES |
| 7 | Sequential Six-Trak | — | VES |
| 8 | Yamaha DX100 | — | VES |
| 9 | Yamaha TX81Z | — | VES |
| 10 | Yamaha FB-01 | **Yes** | MAME direct |
| 11 | Casio HT-6000 | Skeleton | oracle gap (watchlist) |
| 12 | Akai AX80 | driver exists (needs display-controller ROM) | oracle gap |
| 13 | Roland MT-32 | driver exists (needs LA32 — stretch goal) | Roland Cloud |

## Drums

| # | Machine | MAME status | Playable today |
|---|---|---|---|
| 14 | LinnDrum | No | VES |
| 15 | Oberheim DMX | No | VES |
| 16 | Roland TR-707 | No | VES |
| 17 | TR-727 | No | VES |
| 18 | Casio RZ-1 | **Yes** | MAME direct |

## Samplers

| # | Machine | MAME status | Playable today |
|---|---|---|---|
| 19 | Akai MPC60 | No | VES |
| 20 | Akai S3000XL | No | VES |
| — | Ensoniq Mirage (backup) | driver exists, floppies emulated | oracle gap |

Gap-fillers where MAME audio isn't there yet: Dexed (DX7 family), Roland
Cloud (D-50/LA), Arturia (Fairlight). Same SysEx workflow, different engine.
On ARM implants the natively-running stack is MAME-direct + open DSP
(Dexed, OB-Xd, Vital, Surge XT) — ~15 of 20 with zero license fog.
