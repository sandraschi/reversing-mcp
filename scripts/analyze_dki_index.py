import sys
import struct


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_dki_index.py <file>")
        return

    path = sys.argv[1]

    with open(path, "rb") as f:
        # Read Header
        header = f.read(16)
        magic, version, count, data_offset = struct.unpack("<IIII", header)

        print(f"File: {path}")
        print(f"Magic: {magic:08X}")
        print(f"Version: {version}")
        print(f"Count: {count} (0x{count:X})")
        print(f"Data Offset: {data_offset} (0x{data_offset:X})")

        # Calculate entry size
        # Index region size = data_offset - 16
        index_size = data_offset - 16
        if count > 0:
            entry_size_float = index_size / count
            print(f"Calculated Entry Size: {entry_size_float}")
            entry_size = int(entry_size_float)
        else:
            print("Count is 0.")
            return

        print(f"Assuming Entry Size: {entry_size}")

        # Read specific entries
        f.seek(16)
        # Entry 0
        entry0 = f.read(entry_size)
        print(f"Entry 00: {' '.join(f'{b:02X}' for b in entry0)}")
        words0 = struct.unpack("<IIIIII", entry0)
        for j, w in enumerate(words0):
            print(f"  Word[{j}]: {w} (0x{w:X})")

        # Entry 1
        entry1 = f.read(entry_size)
        print(f"Entry 01: {' '.join(f'{b:02X}' for b in entry1)}")
        words1 = struct.unpack("<IIIIII", entry1)
        for j, w in enumerate(words1):
            print(f"  Word[{j}]: {w} (0x{w:X})")

        # Check continuity
        # E0.W5 vs E1.W0? Or E0.W0 -> E0.W1 -> ... -> E0.W5 -> E1.W0?
        print(f"Diff E0.W5 -> E1.W0: {words1[0] - words0[5]}")


if __name__ == "__main__":
    main()
