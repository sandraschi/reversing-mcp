"""
Unit tests for Hercules DJ Console MK1 Hardware Virtualizer and Decoder.
"""

from reversing_mcp.hardware.hercules_mk1 import (
    HerculesMK1Decoder,
    HerculesMK1MidiBridge,
    HerculesMK1State,
    HerculesMK1VirtualConsole,
)


def test_state_defaults():
    s = HerculesMK1State()
    assert s.crossfader == 128
    assert s.pitch_a == 128
    assert s.pitch_b == 128
    assert s.jog_a_pos == 0
    assert not s.btn_play_a
    assert not s.btn_cue_a


def test_encode_decode_roundtrip():
    s1 = HerculesMK1State(
        crossfader=42,
        pitch_a=200,
        pitch_b=10,
        bass_a=64,
        mid_a=128,
        treble_a=250,
        btn_play_a=True,
        btn_fx1_a=True,
        btn_cue_b=True,
        btn_autobeat=True,
        mouse_left_btn=True,
        mouse_x=12,
        mouse_y=-8,
        jog_a_delta=15,
        jog_b_delta=-20,
    )

    pkt = HerculesMK1Decoder.encode(s1)
    assert len(pkt) == 16
    assert pkt[0] == 0x01

    s2 = HerculesMK1Decoder.decode(pkt)
    assert s2.crossfader == 42
    assert s2.pitch_a == 200
    assert s2.pitch_b == 10
    assert s2.bass_a == 64
    assert s2.mid_a == 128
    assert s2.treble_a == 250
    assert s2.btn_play_a is True
    assert s2.btn_fx1_a is True
    assert s2.btn_cue_b is True
    assert s2.btn_autobeat is True
    assert s2.mouse_left_btn is True
    assert s2.mouse_x == 12
    assert s2.mouse_y == -8
    assert s2.jog_a_delta == 15
    assert s2.jog_b_delta == -20
    assert s2.jog_a_pos == 15
    assert s2.jog_b_pos == -20


def test_jog_accumulation():
    state = HerculesMK1State()
    pkt1 = HerculesMK1Decoder.encode(HerculesMK1State(jog_a_delta=5))
    HerculesMK1Decoder.decode(pkt1, state)
    assert state.jog_a_pos == 5

    pkt2 = HerculesMK1Decoder.encode(HerculesMK1State(jog_a_delta=10))
    HerculesMK1Decoder.decode(pkt2, state)
    assert state.jog_a_pos == 15

    pkt3 = HerculesMK1Decoder.encode(HerculesMK1State(jog_a_delta=-8))
    HerculesMK1Decoder.decode(pkt3, state)
    assert state.jog_a_pos == 7


def test_led_encoding():
    s = HerculesMK1State(
        led_play_a=True,
        led_fx2_a=True,
        led_cue_b=True,
        led_autobeat=True,
    )
    led_report = HerculesMK1Decoder.encode_led_report(s)
    assert len(led_report) == 4
    assert led_report[0] == 0x02
    assert led_report[1] & 0x01  # Play A
    assert led_report[1] & 0x08  # FX2 A
    assert led_report[2] & 0x02  # Cue B
    assert led_report[3] & 0x01  # AutoBeat


def test_midi_bridge():
    bridge = HerculesMK1MidiBridge(channel=0)
    s0 = HerculesMK1State()
    # Initial diff primes state, returns empty
    assert bridge.diff_to_midi(s0) == []

    # Move crossfader
    s1 = HerculesMK1State(crossfader=250)
    msgs = bridge.diff_to_midi(s1)
    assert len(msgs) == 1
    assert msgs[0].status == 0xB0
    assert msgs[0].data1 == HerculesMK1MidiBridge.CC_CROSSFADER
    assert msgs[0].data2 == 125

    # Press Play A
    s2 = HerculesMK1State(crossfader=250, btn_play_a=True)
    msgs = bridge.diff_to_midi(s2)
    assert len(msgs) == 1
    assert msgs[0].status == 0x90
    assert msgs[0].data1 == HerculesMK1MidiBridge.NOTE_PLAY_A
    assert msgs[0].data2 == 127

    # Release Play A
    s3 = HerculesMK1State(crossfader=250, btn_play_a=False)
    msgs = bridge.diff_to_midi(s3)
    assert len(msgs) == 1
    assert msgs[0].status == 0x80
    assert msgs[0].data1 == HerculesMK1MidiBridge.NOTE_PLAY_A
    assert msgs[0].data2 == 0


def test_virtual_console():
    console = HerculesMK1VirtualConsole()
    info = console.get_hardware_info()
    assert info["usb_vid"] == "0x06F8"
    assert info["usb_pid"] == "0xB100"
    assert "missing_accessories_note" in info

    pkt, midi = console.spin_jog("A", 12)
    assert len(pkt) == 16
    assert any(m.data1 == HerculesMK1MidiBridge.CC_JOG_A for m in midi)

    pkt, midi = console.press_button("play_a", True)
    assert len(pkt) == 16
    assert any(m.status == 0x90 and m.data1 == HerculesMK1MidiBridge.NOTE_PLAY_A for m in midi)
