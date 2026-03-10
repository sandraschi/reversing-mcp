import sys
import struct


def main():
    if len(sys.argv) < 3:
        print("Usage: dump_dki_header.py <file> <outfile>")
        return

    path = sys.argv[1]
    out_path = sys.argv[2]

    with open(path, "rb") as f:
        header = f.read(16)
        magic, version, count, data_offset = struct.unpack("<IIII", header)

        # Determine end of Data Header (Start of First Chunk)
        # We can read Entry 0 Word 0
        f.seek(16)
        entry0 = f.read(24)
        first_chunk_offset = struct.unpack("<I", entry0[:4])[0]

        data_header_size = first_chunk_offset - data_offset
        print(f"Data Header Offset: {data_offset} (0x{data_offset:X})")
        print(f"First Chunk Offset: {first_chunk_offset} (0x{first_chunk_offset:X})")
        print(f"Data Header Size: {data_header_size}")

        f.seek(data_offset)
        data_header = f.read(data_header_size)

        with open(out_path, "wb") as out:
            out.write(data_header)
        print(f"Dumped to {out_path}")


if __name__ == "__main__":
    main()
