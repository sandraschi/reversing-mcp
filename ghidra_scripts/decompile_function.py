# Decompile a specific function by address or name
# @category Analysis

import sys
import json
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor


def get_function(identifier):
    # Try as address
    try:
        addr = toAddr(identifier)
        if addr:
            func = getFunctionAt(addr)
            if func:
                return func
    except:
        pass

    # Try as name
    funcs = getGlobalFunctions(identifier)
    if funcs:
        return funcs[0]

    return None


def main():
    args = getScriptArgs()
    if not args:
        print(json.dumps({"error": "No function identifier provided"}))
        return

    identifier = args[0]
    func = get_function(identifier)

    if not func:
        print(json.dumps({"error": f"Function '{identifier}' not found"}))
        return

    try:
        decomp = DecompInterface()
        decomp.openProgram(currentProgram)

        # Decompile
        results = decomp.decompileFunction(func, 60, ConsoleTaskMonitor())

        if not results.decompileCompleted():
            print(
                json.dumps({"error": "Decompilation failed", "msg": str(results.getErrorMessage())})
            )
            return

        code = results.getDecompiledFunction().getC()
        signature = str(results.getDecompiledFunction().getSignature())

        output = {
            "name": func.getName(),
            "address": hex(func.getEntryPoint().getOffset()),
            "signature": signature,
            "code": str(code),
        }

        # Determine output filename
        output_file = f"{currentProgram.getName()}_decompiled_{func.getName()}.json"

        import os

        # Write to CWD (or where script is run)
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)

        print(json.dumps({"success": True, "output_file": output_file}))

    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
