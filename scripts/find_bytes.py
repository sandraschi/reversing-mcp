import sys


def main():
    path = sys.argv[1]
    pattern_hex = sys.argv[2]  # e.g. "50 D8 4C 00"
    pattern = bytes.fromhex(pattern_hex.replace(" ", ""))

    with open(path, "rb") as f:
        data = f.read()

    offset = 0
    while True:
        idx = data.find(pattern, offset)
        if idx == -1:
            break
        print(f"Found at Offset: {idx} (0x{idx:X})")
        offset = idx + 1


if __name__ == "__main__":
    main()
