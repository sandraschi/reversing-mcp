# M1 carrier rev A — outline + placement draft (PROVISIONAL)

KLM-1266 replacement carrier for the megasynth retrofit (see
`docs/MEGASYNTH_RETROFIT.md` §2). **All geometry provisional — verify outline
and standoff positions against the real KLM-1266 with calipers before fab.**
No cuts to the M1 steel; original boards stay bagged and tagged.

## Files

| File | Role |
|---|---|
| `gen_m1_carrier.py` | Source of truth: generates the board via KiCad 10 pcbnew |
| `m1-carrier-revA.kicad_pcb` | Generated board (KiCad 10.0.3, DRC 0 violations) |
| `m1-carrier-revA.png` | 3D render proof |

## Regenerate + verify (KiCad 10.0.x bundled python + kicad-cli)

```powershell
& "C:\Program Files\KiCad\10.0\bin\python.exe" gen_m1_carrier.py
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb drc --format json --severity-error --output revA-drc.json m1-carrier-revA.kicad_pcb
& "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe" pcb render --output m1-carrier-revA.png --width 1200 m1-carrier-revA.kicad_pcb
```

Fleet note: `kicad-mcp` owns the MCP surface for this (stable `kicad-cli`
lane for DRC/exports, IPC lane for CRUD). This draft was built with the same
pcbnew calls its headless lane uses; graduate it to `kicad-mcp` CRUD ops
(footprint placement, copper, netlist) at rev B when dims are measured.

## Zones (all F.SilkS placeholders, no copper yet)

250x180 outline on Edge.Cuts, 4x M3 NPTH holes, CM5 55x40, GPIO+MCP23017,
HD44780 header, I2S DAC, MIDI UART+opto+USB, PSU note.
