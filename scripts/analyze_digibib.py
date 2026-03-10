import sys
from pathlib import Path
from reversing_mcp.analyzers import BinaryAnalyzer


def main():
    exe_path = r"d:\Dev\repos\reversing-mcp\tests\fixtures\exe files\Digibib5.exe"
    analyzer = BinaryAnalyzer()
    analyzer.check_available_tools()

    print(f"Analyzing {exe_path}...")

    # 1. File Info
    info = analyzer.get_file_info(exe_path)
    print(f"File Size: {info.get('size')} bytes")

    # 2. Extract Strings
    print("Extracting interesting strings...")
    strings = analyzer.extract_strings(exe_path, min_length=6)

    keywords = ["DKI", "Directmedia", "Huffman", "Table", "Decompress", "Unpack", "Bibliothek"]
    interesting = []
    for s in strings:
        val = s.string
        for k in keywords:
            if k.lower() in val.lower():
                interesting.append(s)
                break

    for s in interesting[:50]:
        print(f"0x{s.offset:08X}: {s.string}")

    # 3. List imports (via static PE analysis if available)
    if "pe_info" in info:
        print("\nImports found in PE:")
        pe = info["pe_info"]
        if "imports" in pe:
            for imp in pe["imports"]:
                print(f"  {imp}")

    # 4. Ghidra Analysis
    print("\nRunning Ghidra Headless Analysis (Fast Scan)...")
    print(f"\nAnalyzing {exe_path}...")
    functions = analyzer.find_functions(exe_path, tool="ghidra", auto_analyze=False)

    if not functions:
        print("Function analysis failed.")
        # Try to retrieve the last error from internal state if we could (not exposed in find_functions)
        pass  # The analyzer logs errors
    else:
        # The original code had a check for "error" in ghidra_results[0].
        # Assuming 'functions' is a list of dicts, and an error would be indicated by an empty list
        # or a specific error dict if the tool returns partial results + error.
        # The instruction implies that if 'functions' is not empty, it's a success.
        print(f"\nFound {len(functions)} functions via Ghidra:")
        # Print top 10 largest functions
        sorted_funcs = sorted(functions, key=lambda x: x.get("size", 0), reverse=True)
        for f in sorted_funcs[:10]:
            print(f"  {f['name']} @ 0x{f['address']:08X} (Size: {f['size']})")
        print(f"Ghidra analysis failed: {ghidra_results[0].get('error')}")


if __name__ == "__main__":
    main()
