# Hercules DJ Console (MK1 - 2003) Hardware & Protocol Specification

## 1. Device Overview

Released in autumn 2003 by Guillemot Corporation under the Hercules brand, the **DJ Console (MK1)** was the industry's first all-in-one USB DJ workcenter featuring twin jog wheels, multi-channel surround audio, integrated phono preamps, and hardware MIDI ports.

### Physical Geometry & Artifact Condition
- **Dimensions**: 235 mm (W) x 200 mm (D) x 65 mm (H)
- **Chassis**: Formed ABS lower tub with stamped brushed aluminum top faceplate
- **Weight**: 1,150 g
- **Physical Deficiencies in Vintage Units**:
  - The original console shipped with a smoked transparent polycarbonate clamshell protective lid featuring dual side latching pins and a 25 mm black nylon shoulder carry strap.
  - In the user's physical unit, **the protective shell and carry strap were lost**. The bare aluminum plate, potentiometers, and jog wheels are directly exposed.
  - A 3D-printable parametric replacement dust cover / deck-saver is specified in `hardware/hercules-mk1/shell_carrier.scad`.

---

## 2. Electrical & USB Architecture

### USB Identifiers
- **Vendor ID (VID)**: `0x06F8` (Guillemot Corporation)
- **Product ID (PID)**:
  - `0xB100`: Operational composite device (USB Audio Class 1.0 + Custom HID Interrupt)
  - `0xD000`: Bootloader / Firmware recovery bulk endpoint

### Endpoint Configuration
- **EP 0**: Control endpoint (Standard USB requests)
- **EP 1 IN**: Interrupt transfer (16-byte input reports at ~100 Hz / 10 ms polling rate)
- **EP 2 OUT**: Interrupt transfer (4-byte output reports for button illumination LEDs)
- **EP 3/4 OUT/IN**: Isochronous audio streams (6-channel DAC playback + 4-channel ADC recording, 48 kHz / 16-bit)

---

## 3. Interrupt IN Report Map (16 Bytes)

```
Offset | Width | Function
-------|-------|--------------------------------------------------------------------
Byte 0 | 1B    | Report ID (Constant 0x01)
Byte 1 | 1B    | Deck A Buttons:
       |       |   Bit 0: Play/Pause
       |       |   Bit 1: Cue
       |       |   Bit 2: Loop In
       |       |   Bit 3: Loop Out
       |       |   Bit 4: FX 1
       |       |   Bit 5: FX 2
       |       |   Bit 6: FX 3
       |       |   Bit 7: Headphone Cue Select A
Byte 2 | 1B    | Deck B Buttons:
       |       |   Bit 0: Play/Pause
       |       |   Bit 1: Cue
       |       |   Bit 2: Loop In
       |       |   Bit 3: Loop Out
       |       |   Bit 4: FX 1
       |       |   Bit 5: FX 2
       |       |   Bit 6: FX 3
       |       |   Bit 7: Headphone Cue Select B
Byte 3 | 1B    | Transport & Tempo:
       |       |   Bit 0: Deck A Pitch Bend (+)
       |       |   Bit 1: Deck A Pitch Bend (-)
       |       |   Bit 2: Deck B Pitch Bend (+)
       |       |   Bit 3: Deck B Pitch Bend (-)
       |       |   Bit 4: AutoBeat Sync
       |       |   Bit 5: Master Tempo Lock
       |       |   Bit 6: Microphone Talkover
       |       |   Bit 7: Reserved
Byte 4 | 1B    | Mouse Pointer Buttons:
       |       |   Bit 0: Mini-joystick Left Button
       |       |   Bit 1: Mini-joystick Right Button
       |       |   Bits 2-7: Reserved
Byte 5 | 1B    | Mini-joystick X Relative Velocity (int8: -128..127)
Byte 6 | 1B    | Mini-joystick Y Relative Velocity (int8: -128..127)
Byte 7 | 1B    | Jog Wheel Deck A Delta (int8: signed 2's complement ticks)
Byte 8 | 1B    | Jog Wheel Deck B Delta (int8: signed 2's complement ticks)
Byte 9 | 1B    | 45mm Crossfader Position (uint8: 0 = Deck A, 128 = Center, 255 = Deck B)
Byte 10| 1B    | Pitch Fader Deck A (uint8: 0..255, 128 = Center detent)
Byte 11| 1B    | Pitch Fader Deck B (uint8: 0..255, 128 = Center detent)
Byte 12| 1B    | Rotary Pot: Deck A Bass (uint8: 0..255)
Byte 13| 1B    | Rotary Pot: Deck A Mid (uint8: 0..255)
Byte 14| 1B    | Rotary Pot: Deck A Treble (uint8: 0..255)
Byte 15| 1B    | Rotary Pot: Deck B Bass (uint8: 0..255)
```

---

## 4. Interrupt OUT Report Map (4 Bytes - LED State)

```
Offset | Width | Function
-------|-------|--------------------------------------------------------------------
Byte 0 | 1B    | Report ID (Constant 0x02)
Byte 1 | 1B    | Deck A LEDs (1 = Illuminated, 0 = Off):
       |       |   Bit 0: Play A
       |       |   Bit 1: Cue A
       |       |   Bit 2: FX 1 A
       |       |   Bit 3: FX 2 A
       |       |   Bit 4: FX 3 A
       |       |   Bit 5: Headphone Cue A
Byte 2 | 1B    | Deck B LEDs (1 = Illuminated, 0 = Off):
       |       |   Bit 0: Play B
       |       |   Bit 1: Cue B
       |       |   Bit 2: FX 1 B
       |       |   Bit 3: FX 2 B
       |       |   Bit 4: FX 3 B
       |       |   Bit 5: Headphone Cue B
Byte 3 | 1B    | Auxiliary LEDs:
       |       |   Bit 0: AutoBeat Sync LED
```

---

## 5. Standard MIDI Translation Map

Modern DAWs (Mixxx, Traktor, Ableton, FL Studio) interface via `HerculesMK1MidiBridge`:

| Control Element | Type | MIDI Status | Number | Values / Notes |
|---|---|---|---|---|
| Crossfader | CC | `0xB0` (Ch 1) | CC 8 | `0..127` (64 = center) |
| Pitch A / B | CC | `0xB0` (Ch 1) | CC 9 / 10 | `0..127` (64 = 0% detent) |
| Jog Wheel A / B | Relative CC | `0xB0` (Ch 1) | CC 16 / 17 | `64 + delta` |
| EQ Bass A / B | CC | `0xB0` (Ch 1) | CC 20 / 23 | `0..127` |
| EQ Mid A / B | CC | `0xB0` (Ch 1) | CC 21 / 24 | `0..127` |
| EQ Treble A / B | CC | `0xB0` (Ch 1) | CC 22 / 25 | `0..127` |
| Deck A Play | Note | `0x90` / `0x80` | Note 36 | 127 on press, 0 on release |
| Deck A Cue | Note | `0x90` / `0x80` | Note 37 | 127 on press, 0 on release |
| Deck B Play | Note | `0x90` / `0x80` | Note 48 | 127 on press, 0 on release |
| Deck B Cue | Note | `0x90` / `0x80` | Note 49 | 127 on press, 0 on release |
| AutoBeat Sync | Note | `0x90` / `0x80` | Note 60 | 127 on press, 0 on release |
