#!/usr/bin/env python3
"""
Test Ghidra-Integration im IDA Pro MCP System
"""

import os
import sys

sys.path.insert(0, "src")

from reversing_mcp.analyzers import BinaryAnalyzer


def test_ghidra_integration():
    """Teste Ghidra-Erkennung und -Integration"""

    analyzer = BinaryAnalyzer()

    print("Reversing MCP - Ghidra Integration Test")
    print("=" * 60)

    # Tool-Erkennung
    print("1. VERFÜGBARE TOOLS:")
    tools = analyzer.check_available_tools()
    for tool_name, tool_info in tools.items():
        status = "[VERFÜGBAR]" if tool_info["available"] else "[NICHT VERFÜGBAR]"
        version = f" ({tool_info['version']})" if tool_info.get("version") else ""
        path = f" - {tool_info['path']}" if tool_info.get("path") else ""
        print(f"  {tool_name:10} {status}{version}{path}")

    print("\n" + "=" * 60)

    # Ghidra-spezifische Tests
    if tools["ghidra"]["available"]:
        print("2. GHIDRA IST VERFÜGBAR!")
        print("   Pfad:", tools["ghidra"]["path"])
        print("   Version:", tools["ghidra"]["version"])

        # Teste Ghidra-Analyse-Funktionen
        print("\n3. GHIDRA-FUNKTIONEN TESTEN:")

        setup_path = r"L:\Multimedia Files\Written Word\Digitale Bibliothek\DB105\Setup.exe"

        if os.path.exists(setup_path):
            print(f"   Analysiere: {setup_path}")

            # Teste verschiedene Ghidra-Funktionen
            try:
                # Funktionen finden (placeholder)
                functions = analyzer._find_functions_ghidra(setup_path)
                print(f"   Funktionsanalyse: {len(functions)} Ergebnisse")

                # Vollständige Analyse
                analysis = analyzer.analyze_file(setup_path, ["ghidra"])
                if "ghidra" in analysis:
                    print("   Ghidra-Analyse: Erfolgreich")
                else:
                    print("   Ghidra-Analyse: Nicht verfügbar")

            except Exception as e:
                print(f"   Fehler bei Ghidra-Test: {e}")
        else:
            print(f"   Setup.exe nicht gefunden: {setup_path}")

    else:
        print("2. GHIDRA NICHT GEFUNDEN")
        print("   Installationspfade gesucht:")
        for path in [
            r"D:\Dev\repos\temp\ghidra-install\ghidra_12.0_PUBLIC\ghidraRun.bat",
            r"C:\Program Files\ghidra\ghidraRun.bat",
            r"C:\ghidra\ghidraRun.bat",
        ]:
            exists = os.path.exists(path)
            print(f"     {path}: {'✓' if exists else '✗'}")

    print("\n" + "=" * 60)
    print("GHIDRA INTEGRATION TEST ABGESCHLOSSEN")

    # Vergleich Ghidra vs IDA Pro
    print("\n4. GHIDRA vs IDA PRO VERGLEICH:")
    print("   " + "=" * 50)

    comparison = {
        "Preis": ["Kostenlos/Open Source", "Kommerziell (~$2,500-10,000)"],
        "Plattform": ["Windows/Linux/macOS", "Windows/Linux/macOS"],
        "Scripting": ["Python/Java", "IDC/Python/IDAPython"],
        "UI": ["Modern/GUI-fokussiert", "Klassisch/Keyboard-fokussiert"],
        "Decompiler": ["Exzellent (mehrere Engines)", "Exzellent"],
        "Debugger": ["Integriert (GADP)", "Umfangreich"],
        "Plugin-API": ["Umfangreich", "Umfangreich"],
        "Community": ["Aktiv/NSA-geführt", "Professionell"],
        "Updates": ["Regelmäßig", "Regelmäßig"],
        "Lernkurve": ["Steil aber gut dokumentiert", "Sehr steil"],
        "Für Directmedia": ["Perfekt geeignet", "Perfekt geeignet"],
    }

    for _feature, values in comparison.items():
        _ghidra_val, _ida_val = values
        print("15")


if __name__ == "__main__":
    test_ghidra_integration()
