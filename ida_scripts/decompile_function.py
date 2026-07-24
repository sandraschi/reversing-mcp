"""IDA Python script — decompile a function by address.
Run headless: ida64.exe -A -S"decompile_function.py <address> <output.json>" <binary>"""

import json
import sys
import ida_auto
import ida_funcs
import ida_hexrays

def main():
    if len(sys.argv) < 3:
        print("Usage: decompile_function.py <address> [output.json]")
        ida_pro.qexit(1)

    address = int(sys.argv[2], 16) if sys.argv[2].startswith("0x") else int(sys.argv[2])
    output_path = sys.argv[3] if len(sys.argv) > 3 else "ida_decompile.json"

    ida_auto.auto_wait()

    func = ida_funcs.get_func(address)
    if not func:
        with open(output_path, "w") as f:
            json.dump({"error": f"Function not found at 0x{address:x}"}, f)
        ida_pro.qexit(1)

    func_name = ida_funcs.get_func_name(address) or f"sub_{address:x}"
    try:
        cfunc = ida_hexrays.decompile(address)
        decompiled = str(cfunc) if cfunc else None
    except Exception as e:
        decompiled = None

    result = {
        "address": address,
        "name": func_name,
        "size": func.end_ea - func.start_ea,
        "decompiled": decompiled,
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

if __name__ == "__main__":
    main()
    ida_pro.qexit(0)
