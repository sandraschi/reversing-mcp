import struct
import sys


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        # DOS Header
        f.seek(0x3C)
        pe_header_offset = struct.unpack("<I", f.read(4))[0]

        # PE Header
        f.seek(pe_header_offset)
        sig = f.read(4)
        if sig != b"PE\0\0":
            print("Not a PE file")
            return

        # File Header
        file_header = f.read(20)
        num_sections = struct.unpack("<H", file_header[2:4])[0]
        opt_header_size = struct.unpack("<H", file_header[16:18])[0]

        # Optional Header
        opt_header = f.read(opt_header_size)
        image_base = struct.unpack("<I", opt_header[28:32])[0]

        print(f"ImageBase: 0x{image_base:X}")

        # Section Table
        f.seek(pe_header_offset + 4 + 20 + opt_header_size)

        print("Sections:")
        for _i in range(num_sections):
            section_entry = f.read(40)
            name = section_entry[0:8].rstrip(b"\0").decode(errors="ignore")
            virtual_size, virtual_addr, raw_size, raw_ptr = struct.unpack(
                "<IIII", section_entry[8:24]
            )
            print(
                f"  {name}: VAddr=0x{virtual_addr:X}, VSize=0x{virtual_size:X}, RawOff=0x{raw_ptr:X}, RawSize=0x{raw_size:X}"
            )


if __name__ == "__main__":
    main()
