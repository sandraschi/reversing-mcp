"""
Hardware virtualization and reverse engineering modules for reversing-mcp.
"""

from .hercules_mk1 import (
    HerculesMK1Decoder,
    HerculesMK1MidiBridge,
    HerculesMK1State,
    HerculesMK1VirtualConsole,
    MidiMessage,
)

__all__ = [
    "HerculesMK1Decoder",
    "HerculesMK1MidiBridge",
    "HerculesMK1State",
    "HerculesMK1VirtualConsole",
    "MidiMessage",
]
