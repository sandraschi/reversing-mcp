# reversing-mcp — latest changes

## 2026-11-02 — v0.5.0: Hercules DJ Console (MK1) Hardware Virtualizer, HID Decoder, MIDI Bridge & Replacement Shell

Reverse engineered and virtualized the 2003 Hercules DJ Console (MK1 / Guillemot Corporation VID: `0x06F8`, PID: `0xB100`).

### Hardware Virtualization & Protocols (`src/reversing_mcp/hardware/`)
- `HerculesMK1Decoder`: Decodes 16-byte raw USB interrupt IN reports on EP 1 IN (jog encoder velocity deltas, 45mm crossfader, pitch sliders, 3-band EQ pots, and 28 rubber tactile buttons).
- `HerculesMK1VirtualConsole`: In-memory state machine synthesizing realistic console telemetry, jogging deltas, fader sweeps, and 4-byte LED interrupt OUT reports.
- `HerculesMK1MidiBridge`: Bi-directional translation layer converting raw HID packets into standard MIDI CC (crossfader CC 8, pitch CC 9/10, jog CC 16/17, EQs CC 20-25) and Note On/Off (Notes 36-62) for DAWs (Mixxx, Traktor, Ableton Live, FL Studio).

### FastMCP Tools (`src/reversing_mcp/server.py`)
- `hercules_hw_info`: Returns physical geometry (235x200x65mm), USB VID/PID descriptors, I/O pinouts, and accessory notes.
- `hercules_virtual_spin`: Simulates relative jog wheel rotation on Deck A/B, emitting raw HID bytes and translated MIDI events.
- `hercules_virtual_fader`: Controls virtual crossfader, pitch sliders, or EQ knobs.
- `hercules_virtual_button`: Toggles tactile buttons (Play, Cue, Loop, FX 1-3, Sync).
- `hercules_decode_packet`: Decodes arbitrary 16-byte hex packets into structured telemetry.

### Mechanical Replacement CAD
- `hardware/hercules-mk1/shell_carrier.scad`: Parametric OpenSCAD design for a snap-on protective faceplate deck-saver and 25mm nylon strap loop frame to replace the lost original polycarbonate clamshell cover and shoulder strap.

### Tests & Documentation
- `tests/test_hercules_mk1.py`: 6/6 tests passing (defaults, roundtrip encoding/decoding, relative jog tick accumulation, LED bitmasks, MIDI diffing, virtual console execution).
- `docs/hardware/HERCULES_DJ_CONSOLE_MK1.md`: Full hardware architectural and protocol specification.
