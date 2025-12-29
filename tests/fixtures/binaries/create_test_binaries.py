#!/usr/bin/env python3
"""
Create minimal test binaries for reverse engineering testing

This script creates simple COM and PE files for testing the reversing MCP.
These are educational fixtures, not malicious code.
"""

import os
import struct
from pathlib import Path


def create_minimal_com():
    """
    Create a minimal DOS COM file
    COM files are raw x86 machine code that starts executing at offset 0x100
    """
    # Minimal COM file that just returns to DOS
    # INT 20h = terminate program
    code = b"\xcd\x20"  # INT 20h

    # COM files need to be at least 1 byte, but this is minimal
    with open("minimal.com", "wb") as f:
        f.write(code)

    print(f"Created minimal.com ({len(code)} bytes)")


def create_hello_com():
    """
    Create a COM file that prints "Hello!" and exits
    Uses DOS interrupt 21h function 09h (print string)
    """
    # Assembly equivalent:
    # mov dx, msg     ; DS:DX points to message
    # mov ah, 09h     ; DOS print string function
    # int 21h         ; Call DOS
    # int 20h         ; Exit

    code = (
        b"\xba\x1a\x01"  # mov dx, 011Ah (offset of message)
        b"\xb4\x09"  # mov ah, 09h
        b"\xcd\x21"  # int 21h
        b"\xcd\x20"  # int 20h (exit)
        b"Hello!$"  # Message with $ terminator
    )

    with open("hello.com", "wb") as f:
        f.write(code)

    print(f"Created hello.com ({len(code)} bytes)")


def create_loop_com():
    """
    Create a COM file with an infinite loop (for disassembly testing)
    """
    # Simple infinite loop: jmp to self
    # This creates a recognizable pattern in disassembly
    code = b"\xeb\xfe"  # jmp short $-2 (infinite loop)

    with open("loop.com", "wb") as f:
        f.write(code)

    print(f"Created loop.com ({len(code)} bytes)")


def create_test_pe():
    """
    Create a minimal Windows PE file
    This is a very basic PE structure for testing
    """
    # PE file header structure (simplified)
    # DOS header
    dos_header = (
        b"MZ"  # e_magic
        b"\x00\x00"  # e_cblp
        b"\x00\x00"  # e_cp
        b"\x00\x00"  # e_crlc
        b"\x00\x00"  # e_cparhdr
        b"\x00\x00"  # e_minalloc
        b"\x00\x00"  # e_maxalloc
        b"\x00\x00"  # e_ss
        b"\x00\x00"  # e_sp
        b"\x00\x00"  # e_csum
        b"\x00\x00"  # e_ip
        b"\x00\x00"  # e_cs
        b"\x00\x00"  # e_lfarlc
        b"\x00\x00"  # e_ovno
        + b"\x00\x00" * 4  # e_res (reserved)
        + b"\x00\x00"  # e_oemid
        + b"\x00\x00"  # e_oeminfo
        + b"\x00\x00" * 10  # e_res2 (reserved)
        + struct.pack("<I", 0x80)  # e_lfanew (PE header offset)
    )

    # PE header
    pe_header = (
        b"PE\x00\x00"  # Signature
        + struct.pack("<H", 0x014C)  # Machine (i386)
        + struct.pack("<H", 1)  # NumberOfSections
        + struct.pack("<I", 0)  # TimeDateStamp
        + struct.pack("<I", 0)  # PointerToSymbolTable
        + struct.pack("<I", 0)  # NumberOfSymbols
        + struct.pack("<H", 0xE0)  # SizeOfOptionalHeader
        + struct.pack("<H", 0x0102)  # Characteristics (32-bit, executable)
    )

    # Optional header (simplified)
    optional_header = (
        struct.pack("<H", 0x010B)  # Magic (PE32)
        + b"\x00"  # MajorLinkerVersion
        + b"\x00"  # MinorLinkerVersion
        + struct.pack("<I", 0x200)  # SizeOfCode
        + struct.pack("<I", 0x200)  # SizeOfInitializedData
        + struct.pack("<I", 0)  # SizeOfUninitializedData
        + struct.pack("<I", 0x1000)  # AddressOfEntryPoint
        + struct.pack("<I", 0x1000)  # BaseOfCode
        + struct.pack("<I", 0x2000)  # BaseOfData
        + struct.pack("<I", 0x400000)  # ImageBase
        + struct.pack("<I", 0x1000)  # SectionAlignment
        + struct.pack("<I", 0x200)  # FileAlignment
        + b"\x00" * 16  # Version fields
        + struct.pack("<I", 2)  # SizeOfImage
        + struct.pack("<I", 0x200)  # SizeOfHeaders
        + struct.pack("<I", 0)  # CheckSum
        + struct.pack("<H", 2)  # Subsystem (Windows GUI)
        + b"\x00"  # DllCharacteristics
        + b"\x00" * 16  # Size fields
        + struct.pack("<I", 0)  # NumberOfRvaAndSizes
    )

    # Section header
    section_header = (
        b".text\x00\x00\x00"  # Name
        + struct.pack("<I", 0x200)  # VirtualSize
        + struct.pack("<I", 0x1000)  # VirtualAddress
        + struct.pack("<I", 0x200)  # SizeOfRawData
        + struct.pack("<I", 0x400)  # PointerToRawData
        + b"\x00" * 12  # Pointers
        + struct.pack("<I", 0x60000020)  # Characteristics (readable, executable, code)
    )

    # Code section (minimal function that returns)
    code_section = (
        b"\x31\xc0"  # xor eax, eax
        b"\xc3" + b"\x00" * (0x200 - 3)  # ret  # Pad to section size
    )

    # Combine all parts
    pe_file = dos_header + pe_header + optional_header + section_header + code_section

    with open("test_pe.exe", "wb") as f:
        f.write(pe_file)

    print(f"Created test_pe.exe ({len(pe_file)} bytes)")


def create_packed_test():
    """
    Create a file with high entropy (simulating packed/compressed data)
    """
    import random

    random.seed(42)  # For reproducible results

    # Create 1KB of high-entropy data
    data = bytes([random.randint(0, 255) for _ in range(1024)])

    with open("packed_test.bin", "wb") as f:
        f.write(data)

    print(f"Created packed_test.bin ({len(data)} bytes - high entropy)")


def main():
    """Create all test binaries"""
    print("Creating test binary fixtures for reversing MCP...")
    print("=" * 50)

    # Change to the binaries directory
    os.chdir(Path(__file__).parent)

    # Create COM files
    create_minimal_com()
    create_hello_com()
    create_loop_com()

    # Create PE file
    create_test_pe()

    # Create packed data file
    create_packed_test()

    print("=" * 50)
    print("All test binaries created successfully!")
    print("\nThese fixtures are for educational testing only.")
    print("They demonstrate basic reverse engineering concepts.")


if __name__ == "__main__":
    main()
