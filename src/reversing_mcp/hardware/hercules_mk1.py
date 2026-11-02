"""
Hercules DJ Console (MK1 - 2003) Hardware Virtualizer, HID Protocol Decoder & MIDI Bridge.

Hardware Profile:
- Guillemot Corporation (Hercules) DJ Console MK1
- USB VID: 0x06F8, PID: 0xB100 (Operational Console) / 0xD000 (Bulk mode)
- Transport: USB 1.1 Audio + Custom HID Interrupt (EP 1 IN / EP 2 OUT)
- Controls: 2x Jog Wheels (Optical Quad Encoders), 1x Crossfader, 2x Pitch Faders,
            6x 3-Band EQ Pots, 28x Rubber Buttons, 1x Mini-Joystick Mouse Pointer.
- Physical Form: 235 x 200 x 65 mm aluminum-topped console with originally included
                 protective smoked acrylic clamshell cover and nylon shoulder strap
                 (frequently lost in vintage specimens).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Any


@dataclass
class HerculesMK1State:
    """Represents the complete live state of the physical or virtual MK1 console."""

    # Jog Wheels (accumulated position and current relative tick velocity)
    jog_a_pos: int = 0
    jog_b_pos: int = 0
    jog_a_delta: int = 0
    jog_b_delta: int = 0

    # Faders (0-255)
    crossfader: int = 128  # Center
    pitch_a: int = 128  # Center (0% pitch offset)
    pitch_b: int = 128  # Center (0% pitch offset)

    # 3-Band EQ Pots (0-255)
    bass_a: int = 128
    mid_a: int = 128
    treble_a: int = 128
    bass_b: int = 128
    mid_b: int = 128
    treble_b: int = 128

    # Volume & Gain Pots (0-255)
    vol_a: int = 200
    vol_b: int = 200
    master_vol: int = 220

    # Mini-joystick mouse pointer
    mouse_x: int = 0
    mouse_y: int = 0
    mouse_left_btn: bool = False
    mouse_right_btn: bool = False

    # Deck A Buttons
    btn_play_a: bool = False
    btn_cue_a: bool = False
    btn_loop_in_a: bool = False
    btn_loop_out_a: bool = False
    btn_fx1_a: bool = False
    btn_fx2_a: bool = False
    btn_fx3_a: bool = False
    btn_pitch_bend_pos_a: bool = False
    btn_pitch_bend_neg_a: bool = False
    btn_cue_select_a: bool = False

    # Deck B Buttons
    btn_play_b: bool = False
    btn_cue_b: bool = False
    btn_loop_in_b: bool = False
    btn_loop_out_b: bool = False
    btn_fx1_b: bool = False
    btn_fx2_b: bool = False
    btn_fx3_b: bool = False
    btn_pitch_bend_pos_b: bool = False
    btn_pitch_bend_neg_b: bool = False
    btn_cue_select_b: bool = False

    # Global / Auxiliary Buttons
    btn_autobeat: bool = False
    btn_master_tempo: bool = False
    btn_talkover: bool = False

    # Output LEDs (Backlights)
    led_play_a: bool = False
    led_cue_a: bool = False
    led_fx1_a: bool = False
    led_fx2_a: bool = False
    led_fx3_a: bool = False
    led_cue_sel_a: bool = False

    led_play_b: bool = False
    led_cue_b: bool = False
    led_fx1_b: bool = False
    led_fx2_b: bool = False
    led_fx3_b: bool = False
    led_cue_sel_b: bool = False

    led_autobeat: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class MidiMessage:
    """Standard 3-byte MIDI message representation."""

    status: int  # e.g., 0x90 Note On, 0x80 Note Off, 0xB0 CC
    data1: int  # Note number or CC number
    data2: int  # Velocity or CC value
    channel: int = 0  # 0-15 (Channel 1-16)

    def to_bytes(self) -> bytes:
        return bytes([(self.status & 0xF0) | (self.channel & 0x0F), self.data1 & 0x7F, self.data2 & 0x7F])

    def to_hex(self) -> str:
        return self.to_bytes().hex().upper()


class HerculesMK1Decoder:
    """
    Decodes raw 16-byte USB interrupt IN reports from the Hercules DJ Console MK1.

    Raw Report Format (16 bytes):
      Byte 0:  Report ID / Header (0x01)
      Byte 1:  Deck A Buttons [Play, Cue, LoopIn, LoopOut, FX1, FX2, FX3, CueSel]
      Byte 2:  Deck B Buttons [Play, Cue, LoopIn, LoopOut, FX1, FX2, FX3, CueSel]
      Byte 3:  Pitch bend & Sync [PitchBend+ A, PitchBend- A, PitchBend+ B, PitchBend- B, AutoBeat, MasterTempo, Talkover, Reserved]
      Byte 4:  Mouse buttons [LeftBtn, RightBtn, Reserved...]
      Byte 5:  Mouse X delta (signed 8-bit)
      Byte 6:  Mouse Y delta (signed 8-bit)
      Byte 7:  Jog Wheel A velocity delta (signed 8-bit, 2's complement)
      Byte 8:  Jog Wheel B velocity delta (signed 8-bit, 2's complement)
      Byte 9:  Crossfader (0 = Deck A, 128 = Center, 255 = Deck B)
      Byte 10: Pitch Fader Deck A (0..255)
      Byte 11: Pitch Fader Deck B (0..255)
      Byte 12: EQ Bass A (0..255)
      Byte 13: EQ Mid A (0..255)
      Byte 14: EQ Treble A (0..255)
      Byte 15: EQ Bass B / Master Gain (0..255)
    """

    @staticmethod
    def decode(packet: bytes | bytearray, state: HerculesMK1State | None = None) -> HerculesMK1State:
        if len(packet) < 16:
            raise ValueError(f"Expected 16-byte HID report, got {len(packet)} bytes")

        s = state if state is not None else HerculesMK1State()
        raw = bytes(packet)

        # Buttons Deck A (Byte 1)
        b1 = raw[1]
        s.btn_play_a = bool(b1 & 0x01)
        s.btn_cue_a = bool(b1 & 0x02)
        s.btn_loop_in_a = bool(b1 & 0x04)
        s.btn_loop_out_a = bool(b1 & 0x08)
        s.btn_fx1_a = bool(b1 & 0x10)
        s.btn_fx2_a = bool(b1 & 0x20)
        s.btn_fx3_a = bool(b1 & 0x40)
        s.btn_cue_select_a = bool(b1 & 0x80)

        # Buttons Deck B (Byte 2)
        b2 = raw[2]
        s.btn_play_b = bool(b2 & 0x01)
        s.btn_cue_b = bool(b2 & 0x02)
        s.btn_loop_in_b = bool(b2 & 0x04)
        s.btn_loop_out_b = bool(b2 & 0x08)
        s.btn_fx1_b = bool(b2 & 0x10)
        s.btn_fx2_b = bool(b2 & 0x20)
        s.btn_fx3_b = bool(b2 & 0x40)
        s.btn_cue_select_b = bool(b2 & 0x80)

        # Pitch bend & Navigation (Byte 3)
        b3 = raw[3]
        s.btn_pitch_bend_pos_a = bool(b3 & 0x01)
        s.btn_pitch_bend_neg_a = bool(b3 & 0x02)
        s.btn_pitch_bend_pos_b = bool(b3 & 0x04)
        s.btn_pitch_bend_neg_b = bool(b3 & 0x08)
        s.btn_autobeat = bool(b3 & 0x10)
        s.btn_master_tempo = bool(b3 & 0x20)
        s.btn_talkover = bool(b3 & 0x40)

        # Mouse Buttons (Byte 4)
        b4 = raw[4]
        s.mouse_left_btn = bool(b4 & 0x01)
        s.mouse_right_btn = bool(b4 & 0x02)

        # Relative movements (signed 8-bit int8)
        s.mouse_x = struct.unpack("b", bytes([raw[5]]))[0]
        s.mouse_y = struct.unpack("b", bytes([raw[6]]))[0]

        delta_a = struct.unpack("b", bytes([raw[7]]))[0]
        delta_b = struct.unpack("b", bytes([raw[8]]))[0]
        s.jog_a_delta = delta_a
        s.jog_b_delta = delta_b
        s.jog_a_pos += delta_a
        s.jog_b_pos += delta_b

        # Faders & Pots (unsigned 8-bit uint8)
        s.crossfader = raw[9]
        s.pitch_a = raw[10]
        s.pitch_b = raw[11]
        s.bass_a = raw[12]
        s.mid_a = raw[13]
        s.treble_a = raw[14]
        s.bass_b = raw[15]

        return s

    @staticmethod
    def encode(state: HerculesMK1State) -> bytes:
        """Encodes state into a 16-byte raw USB interrupt packet."""
        b0 = 0x01  # Report ID

        # Byte 1: Deck A
        b1 = (
            (1 if state.btn_play_a else 0)
            | ((1 if state.btn_cue_a else 0) << 1)
            | ((1 if state.btn_loop_in_a else 0) << 2)
            | ((1 if state.btn_loop_out_a else 0) << 3)
            | ((1 if state.btn_fx1_a else 0) << 4)
            | ((1 if state.btn_fx2_a else 0) << 5)
            | ((1 if state.btn_fx3_a else 0) << 6)
            | ((1 if state.btn_cue_select_a else 0) << 7)
        )

        # Byte 2: Deck B
        b2 = (
            (1 if state.btn_play_b else 0)
            | ((1 if state.btn_cue_b else 0) << 1)
            | ((1 if state.btn_loop_in_b else 0) << 2)
            | ((1 if state.btn_loop_out_b else 0) << 3)
            | ((1 if state.btn_fx1_b else 0) << 4)
            | ((1 if state.btn_fx2_b else 0) << 5)
            | ((1 if state.btn_fx3_b else 0) << 6)
            | ((1 if state.btn_cue_select_b else 0) << 7)
        )

        # Byte 3: Pitch bend / Sync
        b3 = (
            (1 if state.btn_pitch_bend_pos_a else 0)
            | ((1 if state.btn_pitch_bend_neg_a else 0) << 1)
            | ((1 if state.btn_pitch_bend_pos_b else 0) << 2)
            | ((1 if state.btn_pitch_bend_neg_b else 0) << 3)
            | ((1 if state.btn_autobeat else 0) << 4)
            | ((1 if state.btn_master_tempo else 0) << 5)
            | ((1 if state.btn_talkover else 0) << 6)
        )

        # Byte 4: Mouse
        b4 = (1 if state.mouse_left_btn else 0) | ((1 if state.mouse_right_btn else 0) << 1)

        # Clamping signed deltas (-128..127)
        mx = max(-128, min(127, state.mouse_x))
        my = max(-128, min(127, state.mouse_y))
        ja = max(-128, min(127, state.jog_a_delta))
        jb = max(-128, min(127, state.jog_b_delta))

        b5 = struct.pack("b", mx)[0]
        b6 = struct.pack("b", my)[0]
        b7 = struct.pack("b", ja)[0]
        b8 = struct.pack("b", jb)[0]

        b9 = state.crossfader & 0xFF
        b10 = state.pitch_a & 0xFF
        b11 = state.pitch_b & 0xFF
        b12 = state.bass_a & 0xFF
        b13 = state.mid_a & 0xFF
        b14 = state.treble_a & 0xFF
        b15 = state.bass_b & 0xFF

        return bytes([b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12, b13, b14, b15])

    @staticmethod
    def encode_led_report(state: HerculesMK1State) -> bytes:
        """
        Encodes 4-byte LED control packet (EP 2 OUT).
        Controls hardware illumination under rubber tactile buttons.
        """
        # Byte 0: Report ID (0x02)
        # Byte 1: Deck A LEDs [Play, Cue, FX1, FX2, FX3, CueSel]
        l1 = (
            (1 if state.led_play_a else 0)
            | ((1 if state.led_cue_a else 0) << 1)
            | ((1 if state.led_fx1_a else 0) << 2)
            | ((1 if state.led_fx2_a else 0) << 3)
            | ((1 if state.led_fx3_a else 0) << 4)
            | ((1 if state.led_cue_sel_a else 0) << 5)
        )
        # Byte 2: Deck B LEDs [Play, Cue, FX1, FX2, FX3, CueSel]
        l2 = (
            (1 if state.led_play_b else 0)
            | ((1 if state.led_cue_b else 0) << 1)
            | ((1 if state.led_fx1_b else 0) << 2)
            | ((1 if state.led_fx2_b else 0) << 3)
            | ((1 if state.led_fx3_b else 0) << 4)
            | ((1 if state.led_cue_sel_b else 0) << 5)
        )
        # Byte 3: Global LEDs [AutoBeat]
        l3 = 1 if state.led_autobeat else 0

        return bytes([0x02, l1, l2, l3])


class HerculesMK1MidiBridge:
    """
    Translates raw Hercules MK1 state changes into standard MIDI Channel/Note/CC events
    for modern digital audio workstations (Mixxx, Traktor, Ableton Live, FL Studio).
    """

    # CC Mappings (0xB0)
    CC_CROSSFADER = 8
    CC_PITCH_A = 9
    CC_PITCH_B = 10
    CC_JOG_A = 16
    CC_JOG_B = 17
    CC_EQ_BASS_A = 20
    CC_EQ_MID_A = 21
    CC_EQ_TREBLE_A = 22
    CC_EQ_BASS_B = 23
    CC_EQ_MID_B = 24
    CC_EQ_TREBLE_B = 25

    # Note Mappings (0x90 Note On / 0x80 Note Off)
    NOTE_PLAY_A = 36
    NOTE_CUE_A = 37
    NOTE_LOOP_IN_A = 38
    NOTE_LOOP_OUT_A = 39
    NOTE_FX1_A = 40
    NOTE_FX2_A = 41
    NOTE_FX3_A = 42
    NOTE_CUE_SEL_A = 43

    NOTE_PLAY_B = 48
    NOTE_CUE_B = 49
    NOTE_LOOP_IN_B = 50
    NOTE_LOOP_OUT_B = 51
    NOTE_FX1_B = 52
    NOTE_FX2_B = 53
    NOTE_FX3_B = 54
    NOTE_CUE_SEL_B = 55

    NOTE_AUTOBEAT = 60
    NOTE_MASTER_TEMPO = 61
    NOTE_TALKOVER = 62

    def __init__(self, channel: int = 0):
        self.channel = channel
        self._last_state: HerculesMK1State | None = None

    def diff_to_midi(self, current: HerculesMK1State) -> list[MidiMessage]:
        """Compares current state to previous state and emits MIDI events."""
        msgs: list[MidiMessage] = []
        last = self._last_state

        if last is None:
            self._last_state = HerculesMK1State(**current.to_dict())
            return msgs

        # Check Faders (scale 0-255 down to 0-127 for 7-bit MIDI CC)
        if (current.crossfader >> 1) != (last.crossfader >> 1):
            msgs.append(MidiMessage(0xB0, self.CC_CROSSFADER, current.crossfader >> 1, self.channel))
        if (current.pitch_a >> 1) != (last.pitch_a >> 1):
            msgs.append(MidiMessage(0xB0, self.CC_PITCH_A, current.pitch_a >> 1, self.channel))
        if (current.pitch_b >> 1) != (last.pitch_b >> 1):
            msgs.append(MidiMessage(0xB0, self.CC_PITCH_B, current.pitch_b >> 1, self.channel))

        # Check EQ Pots
        if (current.bass_a >> 1) != (last.bass_a >> 1):
            msgs.append(MidiMessage(0xB0, self.CC_EQ_BASS_A, current.bass_a >> 1, self.channel))
        if (current.mid_a >> 1) != (last.mid_a >> 1):
            msgs.append(MidiMessage(0xB0, self.CC_EQ_MID_A, current.mid_a >> 1, self.channel))
        if (current.treble_a >> 1) != (last.treble_a >> 1):
            msgs.append(MidiMessage(0xB0, self.CC_EQ_TREBLE_A, current.treble_a >> 1, self.channel))
        if (current.bass_b >> 1) != (last.bass_b >> 1):
            msgs.append(MidiMessage(0xB0, self.CC_EQ_BASS_B, current.bass_b >> 1, self.channel))

        # Check Jog Wheels (relative tick mode: 64 is center, >64 CW, <64 CCW)
        if current.jog_a_delta != 0:
            rel_val = max(1, min(127, 64 + current.jog_a_delta))
            msgs.append(MidiMessage(0xB0, self.CC_JOG_A, rel_val, self.channel))
        if current.jog_b_delta != 0:
            rel_val = max(1, min(127, 64 + current.jog_b_delta))
            msgs.append(MidiMessage(0xB0, self.CC_JOG_B, rel_val, self.channel))

        # Check Buttons
        btn_map = [
            ("btn_play_a", self.NOTE_PLAY_A),
            ("btn_cue_a", self.NOTE_CUE_A),
            ("btn_loop_in_a", self.NOTE_LOOP_IN_A),
            ("btn_loop_out_a", self.NOTE_LOOP_OUT_A),
            ("btn_fx1_a", self.NOTE_FX1_A),
            ("btn_fx2_a", self.NOTE_FX2_A),
            ("btn_fx3_a", self.NOTE_FX3_A),
            ("btn_cue_select_a", self.NOTE_CUE_SEL_A),
            ("btn_play_b", self.NOTE_PLAY_B),
            ("btn_cue_b", self.NOTE_CUE_B),
            ("btn_loop_in_b", self.NOTE_LOOP_IN_B),
            ("btn_loop_out_b", self.NOTE_LOOP_OUT_B),
            ("btn_fx1_b", self.NOTE_FX1_B),
            ("btn_fx2_b", self.NOTE_FX2_B),
            ("btn_fx3_b", self.NOTE_FX3_B),
            ("btn_cue_select_b", self.NOTE_CUE_SEL_B),
            ("btn_autobeat", self.NOTE_AUTOBEAT),
            ("btn_master_tempo", self.NOTE_MASTER_TEMPO),
            ("btn_talkover", self.NOTE_TALKOVER),
        ]

        for attr, note in btn_map:
            curr_val = getattr(current, attr)
            last_val = getattr(last, attr)
            if curr_val != last_val:
                status = 0x90 if curr_val else 0x80
                velocity = 127 if curr_val else 0
                msgs.append(MidiMessage(status, note, velocity, self.channel))

        self._last_state = HerculesMK1State(**current.to_dict())
        return msgs


class HerculesMK1VirtualConsole:
    """
    In-memory virtual hardware emulator of the Hercules DJ Console MK1.
    Allows testing, UI control, and protocol synthesis without physical hardware.
    """

    def __init__(self):
        self.state = HerculesMK1State()
        self.midi_bridge = HerculesMK1MidiBridge()
        # Prime the bridge with current initial state so subsequent diffs emit immediately
        self.midi_bridge._last_state = HerculesMK1State(**self.state.to_dict())
        self.packet_history: list[str] = []

    def spin_jog(self, deck: str, ticks: int) -> tuple[bytes, list[MidiMessage]]:
        """Simulate spinning jog wheel (positive for forward/CW, negative for back/CCW)."""
        if deck.upper() == "A":
            self.state.jog_a_delta = ticks
            self.state.jog_a_pos += ticks
        else:
            self.state.jog_b_delta = ticks
            self.state.jog_b_pos += ticks

        pkt = HerculesMK1Decoder.encode(self.state)
        self.packet_history.append(pkt.hex().upper())
        midi = self.midi_bridge.diff_to_midi(self.state)
        # reset deltas after impulse
        self.state.jog_a_delta = 0
        self.state.jog_b_delta = 0
        return pkt, midi

    def set_fader(self, fader: str, value: int) -> tuple[bytes, list[MidiMessage]]:
        """Set crossfader, pitch_a, or pitch_b (0..255)."""
        val = max(0, min(255, value))
        if fader == "crossfader":
            self.state.crossfader = val
        elif fader == "pitch_a":
            self.state.pitch_a = val
        elif fader == "pitch_b":
            self.state.pitch_b = val

        pkt = HerculesMK1Decoder.encode(self.state)
        self.packet_history.append(pkt.hex().upper())
        midi = self.midi_bridge.diff_to_midi(self.state)
        return pkt, midi

    def press_button(self, button_name: str, pressed: bool = True) -> tuple[bytes, list[MidiMessage]]:
        """Toggle or press a button by attribute name."""
        attr = f"btn_{button_name}" if not button_name.startswith("btn_") else button_name
        if hasattr(self.state, attr):
            setattr(self.state, attr, pressed)
        else:
            raise AttributeError(f"Unknown button: {button_name}")

        pkt = HerculesMK1Decoder.encode(self.state)
        self.packet_history.append(pkt.hex().upper())
        midi = self.midi_bridge.diff_to_midi(self.state)
        return pkt, midi

    def get_hardware_info(self) -> dict[str, Any]:
        """Returns comprehensive physical and USB hardware descriptors."""
        return {
            "name": "Hercules DJ Console (MK1)",
            "year": 2003,
            "manufacturer": "Guillemot Corporation",
            "usb_vid": "0x06F8",
            "usb_pid": "0xB100",
            "usb_alt_pid": "0xD000",
            "class": "USB Composite Audio + Custom HID Interrupt",
            "dimensions_mm": {
                "width": 235,
                "depth": 200,
                "height": 65,
                "weight_g": 1150,
            },
            "controls": {
                "jog_wheels": 2,
                "crossfader": "45mm travel, 8-bit ADC",
                "pitch_faders": "2x 60mm travel, center detent",
                "eq_knobs": "6x 270-degree rotary pots (Bass, Mid, Treble per deck)",
                "buttons": "28x backlit tactile silicone rubber pads",
                "mouse_pointer": "2-axis mini-joystick + Left/Right buttons",
            },
            "audio_io": {
                "outputs": "5.1 Surround (6x RCA channels, 48kHz / 16-bit)",
                "digital_io": "Optical & Coaxial S/PDIF In and Out",
                "inputs": "2x Stereo RCA (Line/Phono switchable with GND lug)",
                "midi_ports": "Standard 5-pin DIN MIDI IN & MIDI OUT",
                "headphone_out": "1/4 inch and 1/8 inch stereo with analog pot",
                "mic_in": "1/4 inch dynamic mic with gain pot and hardware talkover",
            },
            "missing_accessories_note": (
                "The original release included a smoked transparent polycarbonate clamshell cover "
                "with side latching pins and a 25mm black nylon shoulder carrying strap. "
                "Vintage units frequently lack this shell, exposing the metal faceplate."
            ),
        }
