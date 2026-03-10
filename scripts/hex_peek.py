import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: hex_peek.py <file> <offset_hex> [length]")
        return

    path = sys.argv[1]
    offset = int(sys.argv[2], 16)
    length = int(sys.argv[3]) if len(sys.argv) > 3 else 128

    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read(length)

    start_display = offset

    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_bytes = " ".join(f"{b:02X}" for b in chunk)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{start_display + i:08X}: {hex_bytes:<48} {ascii_str}")


if __name__ == "__main__":
    main()
