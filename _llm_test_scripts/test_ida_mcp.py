#!/usr/bin/env python3
"""
Test script for IDA Pro MCP functionality
"""

import os
import sys

sys.path.insert(0, "src")

from reversing_mcp.analyzers import BinaryAnalyzer


def test_directmedia_setup():
    """Teste Analyse der Directmedia Setup.exe"""

    analyzer = BinaryAnalyzer()

    print("Reversing MCP - Directmedia Setup.exe Analysis")
    print("=" * 60)

    # Überprüfe verfügbare Tools
    print("1. VERFÜGBARE TOOLS:")
    tools = analyzer.check_available_tools()
    for tool_name, tool_info in tools.items():
        status = "[VERFUEGBAR]" if tool_info["available"] else "[NICHT VERFUEGBAR]"
        version = f" ({tool_info['version']})" if tool_info["version"] else ""
        print(f"  {tool_name:10} {status} {version}")

    print("\n" + "=" * 60)

    # Analysiere Directmedia Setup.exe
    setup_path = r"L:\Multimedia Files\Written Word\Digitale Bibliothek\DB105\Setup.exe"

    if not os.path.exists(setup_path):
        print(f"Setup.exe nicht gefunden: {setup_path}")
        return

    print(f"2. ANALYSIERE: {setup_path}")
    print("-" * 60)

    # Grundlegende Datei-Info
    try:
        stat_info = os.stat(setup_path)
        print(f"Dateigröße: {stat_info.st_size:,} Bytes")
        print(f"Dateityp: {analyzer.detect_file_type(setup_path)}")
        print(f"Lesbar: {os.access(setup_path, os.R_OK)}")
        print(f"Ausführbar: {os.access(setup_path, os.X_OK)}")
    except Exception as e:
        print(f"Fehler bei Datei-Info: {e}")

    # PE-Analyse
    print("\n3. PE-ANALYSE:")
    pe_info = analyzer.analyze_pe_file(setup_path)
    if "error" not in pe_info:
        print(f"Architektur: {pe_info['machine']}")
        print(f"Anzahl Sektionen: {pe_info['num_sections']}")
    else:
        print(f"Fehler: {pe_info['error']}")

    # Strings extrahieren
    print("\n4. STRING-EXTRAKTION (erste 10 Strings):")
    strings = analyzer.extract_strings(setup_path, min_length=8)
    for i, s in enumerate(strings[:10]):
        print("8")

    # Hexdump
    print("\n5. HEXDUMP (erste 256 Bytes):")
    hexdump = analyzer.get_hexdump(setup_path, 0, 256)
    print(hexdump)

    # Entropie-Analyse
    print("\n6. ENTROPIE-ANALYSE:")
    entropy = analyzer.analyze_entropy(setup_path)
    if "error" not in entropy:
        print(".2f")
        print(f"Komprimierte Regionen: {len(entropy['compressed_regions'])}")
        print(f"Zufällige Regionen: {len(entropy['random_regions'])}")
    else:
        print(f"Fehler: {entropy['error']}")

    # Vollständige Analyse
    print("\n7. VOLLSTÄNDIGE ANALYSE:")
    analysis = analyzer.analyze_file(setup_path, ["static", "file", "strings"])
    print(f"Analysierte Tools: {list(analysis.keys())}")

    print("\n" + "=" * 60)
    print("ANALYSE ABGESCHLOSSEN")
    print("Empfehlungen für Directmedia Reverse Engineering:")
    print("- Verwende IDA Pro für detaillierte Analyse")
    print("- Schaue nach Kompressionsbibliotheken (LZ77, etc.)")
    print("- Suche nach Directmedia-spezifischen Strings")
    print("- Analysiere Entropie-Spitzen (können komprimierten Code anzeigen)")


if __name__ == "__main__":
    test_directmedia_setup()
