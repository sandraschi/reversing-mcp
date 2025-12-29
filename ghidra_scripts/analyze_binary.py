#!/usr/bin/env python3
"""
Ghidra script for headless binary analysis
Extracts functions, strings, and basic analysis results
"""

import sys
import json
import os
from pathlib import Path

# Ghidra imports
from ghidra.app.decompiler import DecompInterface
from ghidra.app.util.headless import HeadlessScript
from ghidra.program.model.listing import Function, FunctionIterator
from ghidra.program.model.symbol import Symbol, SymbolType
from ghidra.program.model.data import DataType
from ghidra.program.model.mem import Memory
from ghidra.util.task import ConsoleTaskMonitor


class BinaryAnalyzer(HeadlessScript):
    """Headless Ghidra binary analyzer"""

    def __init__(self):
        super().__init__()
        self.results = {
            "functions": [],
            "strings": [],
            "symbols": [],
            "analysis_info": {}
        }

    def run(self):
        """Main analysis function"""
        try:
            print(f"[Ghidra] Analyzing: {currentProgram.getName()}")
            monitor = ConsoleTaskMonitor()

            # Get program info
            self.results["analysis_info"] = {
                "program_name": currentProgram.getName(),
                "program_path": str(currentProgram.getExecutablePath()),
                "language": str(currentProgram.getLanguage()),
                "compiler": str(currentProgram.getCompilerSpec()),
                "image_base": hex(currentProgram.getImageBase().getOffset()),
                "min_address": hex(currentProgram.getMinAddress().getOffset()),
                "max_address": hex(currentProgram.getMaxAddress().getOffset())
            }

            # Extract functions
            self._extract_functions()

            # Extract strings
            self._extract_strings()

            # Extract symbols
            self._extract_symbols()

            # Save results to JSON file
            self._save_results()

            print(f"[Ghidra] Analysis complete for {currentProgram.getName()}")

        except Exception as e:
            print(f"[Ghidra] Error during analysis: {e}")
            import traceback
            traceback.print_exc()

    def _extract_functions(self):
        """Extract function information"""
        print("[Ghidra] Extracting functions...")
        function_manager = currentProgram.getFunctionManager()
        functions = function_manager.getFunctions(True)  # True = forward iteration

        for func in functions:
            func_info = {
                "name": func.getName(),
                "address": hex(func.getEntryPoint().getOffset()),
                "size": func.getBody().getNumAddresses(),
                "signature": str(func.getSignature()),
                "calling_convention": str(func.getCallingConventionName()) if func.getCallingConventionName() else None,
                "has_custom_storage": func.hasCustomVariableStorage(),
                "is_external": func.isExternal(),
                "is_thunk": func.isThunk()
            }

            # Try to get decompiled code (if possible)
            try:
                decomp = DecompInterface()
                decomp.openProgram(currentProgram)
                results = decomp.decompileFunction(func, 30, ConsoleTaskMonitor())  # 30 second timeout
                if results and results.getDecompiledFunction():
                    # Get first few lines of decompiled code
                    decompiled = str(results.getDecompiledFunction())
                    lines = decompiled.split('\n')[:10]  # First 10 lines
                    func_info["decompiled_preview"] = '\n'.join(lines)
            except:
                pass

            self.results["functions"].append(func_info)

        print(f"[Ghidra] Extracted {len(self.results['functions'])} functions")

    def _extract_strings(self):
        """Extract string literals from the binary"""
        print("[Ghidra] Extracting strings...")
        listing = currentProgram.getListing()
        strings_found = []

        # Get all defined data
        data_iter = listing.getDefinedData(True)

        for data in data_iter:
            try:
                data_type = data.getDataType()
                if data_type and data_type.getName() in ["string", "unicode", "TerminatedCString"]:
                    value = data.getValue()
                    if value and len(str(value)) > 3:  # Minimum 4 characters
                        string_info = {
                            "address": hex(data.getAddress().getOffset()),
                            "value": str(value),
                            "length": len(str(value)),
                            "encoding": "auto"
                        }
                        strings_found.append(string_info)
            except:
                continue

        self.results["strings"] = strings_found
        print(f"[Ghidra] Extracted {len(strings_found)} strings")

    def _extract_symbols(self):
        """Extract symbol information"""
        print("[Ghidra] Extracting symbols...")
        symbol_table = currentProgram.getSymbolTable()
        symbols = symbol_table.getAllSymbols(True)  # True = include dynamic symbols

        for symbol in symbols:
            try:
                symbol_info = {
                    "name": symbol.getName(),
                    "address": hex(symbol.getAddress().getOffset()) if symbol.getAddress() else None,
                    "type": str(symbol.getSymbolType()),
                    "source": str(symbol.getSource()),
                    "is_external": symbol.isExternal(),
                    "is_global": symbol.isGlobal()
                }
                self.results["symbols"].append(symbol_info)
            except:
                continue

        print(f"[Ghidra] Extracted {len(self.results['symbols'])} symbols")

    def _save_results(self):
        """Save analysis results to JSON file"""
        try:
            # Create output filename based on input file
            input_name = Path(currentProgram.getName()).stem
            output_file = f"{input_name}_ghidra_analysis.json"

            # Save in current directory (Ghidra working directory)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            print(f"[Ghidra] Results saved to: {output_file}")

        except Exception as e:
            print(f"[Ghidra] Error saving results: {e}")


# Run the analyzer when script is executed
if __name__ == "__main__":
    analyzer = BinaryAnalyzer()
    analyzer.run()