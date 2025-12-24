"""
Binary Analysis Tools for Reverse Engineering
"""

import os
import subprocess
import struct
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .logging_config import get_logger
from pydantic import BaseModel

logger = get_logger("ida_pro_mcp.analyzers")


class StringResult(BaseModel):
    """String extraction result"""
    offset: int
    string: str
    encoding: str
    length: int


class FunctionInfo(BaseModel):
    """Function information"""
    address: int
    name: str
    size: int
    tool: str


class BinaryAnalyzer:
    """Multi-tool binary analyzer supporting IDA Pro, Ghidra, radare2, etc."""

    def __init__(self):
        self.tools_cache = None

    def check_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Check which reverse engineering tools are available"""

        tools = {
            "ida": {"name": "IDA Pro", "available": False, "version": None, "path": None},
            "ghidra": {"name": "Ghidra", "available": False, "version": None, "path": None},
            "r2": {"name": "radare2", "available": False, "version": None, "path": None},
            "binwalk": {"name": "Binwalk", "available": False, "version": None, "path": None},
            "strings": {"name": "GNU strings", "available": False, "version": None, "path": None},
            "file": {"name": "file command", "available": False, "version": None, "path": None},
        }

        # Check IDA Pro (Windows registry or common paths)
        ida_paths = [
            r"C:\Program Files\IDA Pro 8.3\ida.exe",
            r"C:\Program Files\IDA Pro 8.2\ida.exe",
            r"C:\Program Files\IDA Pro 8.1\ida.exe",
            r"C:\Program Files (x86)\IDA Pro\ida.exe"
        ]
        for path in ida_paths:
            if os.path.exists(path):
                tools["ida"]["available"] = True
                tools["ida"]["path"] = path
                try:
                    result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        tools["ida"]["version"] = result.stdout.strip()
                except:
                    pass
                break

        # Check Ghidra
        ghidra_paths = [
            r"D:\Dev\repos\temp\ghidra-install\ghidra_12.0_PUBLIC\ghidraRun.bat",
            r"C:\Program Files\ghidra\ghidraRun.bat",
            r"C:\ghidra\ghidraRun.bat",
            "/usr/local/ghidra/ghidraRun",
            "/opt/ghidra/ghidraRun"
        ]
        for path in ghidra_paths:
            if os.path.exists(path):
                tools["ghidra"]["available"] = True
                tools["ghidra"]["path"] = path
                tools["ghidra"]["version"] = "12.0"
                break

        # Check radare2
        try:
            result = subprocess.run(["r2", "-v"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                tools["r2"]["available"] = True
                tools["r2"]["version"] = result.stdout.split('\n')[0] if result.stdout else "unknown"
        except:
            pass

        # Check binwalk
        try:
            result = subprocess.run(["binwalk", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                tools["binwalk"]["available"] = True
                tools["binwalk"]["version"] = result.stdout.strip()
        except:
            pass

        # Check GNU strings
        try:
            result = subprocess.run(["strings", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                tools["strings"]["available"] = True
                tools["strings"]["version"] = result.stdout.split('\n')[0] if result.stdout else "unknown"
        except:
            pass

        # Check file command
        try:
            result = subprocess.run(["file", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                tools["file"]["available"] = True
                tools["file"]["version"] = result.stdout.split('\n')[0] if result.stdout else "unknown"
        except:
            pass

        self.tools_cache = tools
        return tools

    def analyze_file(self, file_path: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze a file with multiple tools"""

        if tools is None:
            tools = ["static", "file", "strings", "binwalk"]

        results = {}

        # Basic file type detection
        if "file" in tools or "static" in tools:
            results["file"] = self._analyze_with_file(file_path)

        # String extraction
        if "strings" in tools or "static" in tools:
            results["strings"] = [s.model_dump() for s in self.extract_strings(file_path)]

        # Binwalk analysis
        if "binwalk" in tools:
            results["binwalk"] = self._analyze_with_binwalk(file_path)

        # IDA Pro analysis (if available)
        if "ida" in tools and self.tools_cache and self.tools_cache["ida"]["available"]:
            results["ida"] = self._analyze_with_ida(file_path)

        # Ghidra analysis (if available)
        if "ghidra" in tools and self.tools_cache and self.tools_cache["ghidra"]["available"]:
            results["ghidra"] = self._analyze_with_ghidra(file_path)

        # radare2 analysis
        if "r2" in tools or "radare2" in tools:
            results["r2"] = self._analyze_with_r2(file_path)

        return results

    def _analyze_with_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze with file command"""
        try:
            result = subprocess.run(["file", file_path], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                file_type = result.stdout.strip().split(': ', 1)[1] if ': ' in result.stdout else result.stdout.strip()
                return {"file_type": file_type, "success": True}
            else:
                return {"error": "file command failed", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def _analyze_with_binwalk(self, file_path: str) -> Dict[str, Any]:
        """Analyze with binwalk"""
        try:
            result = subprocess.run(["binwalk", "-J", file_path], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                # Parse JSON output
                import json
                try:
                    data = json.loads(result.stdout)
                    return {"signatures": data, "success": True}
                except:
                    return {"raw_output": result.stdout, "success": True}
            else:
                return {"error": "binwalk failed", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def _analyze_with_ida(self, file_path: str) -> Dict[str, Any]:
        """Analyze with IDA Pro (placeholder - would need IDA scripting)"""
        # This would require IDA Pro Python scripting
        # For now, just return that IDA is available
        return {
            "available": True,
            "note": "IDA Pro analysis requires custom scripting",
            "recommendation": "Use IDA Pro GUI or create IDC/Python script"
        }

    def _analyze_with_ghidra(self, file_path: str) -> Dict[str, Any]:
        """Analyze with Ghidra"""
        # This would require Ghidra Python API
        return {
            "available": True,
            "note": "Ghidra analysis requires Ghidra installation and scripting",
            "recommendation": "Use Ghidra GUI or create Ghidra script"
        }

    def _analyze_with_r2(self, file_path: str) -> Dict[str, Any]:
        """Analyze with radare2"""
        try:
            # Basic info
            result = subprocess.run(["r2", "-A", "-q", "-c", "i", file_path],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {"info": result.stdout, "success": True}
            else:
                return {"error": "r2 analysis failed", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def extract_strings(self, file_path: str, min_length: int = 4,
                       encodings: Optional[List[str]] = None) -> List[StringResult]:
        """Extract strings from binary file"""

        if encodings is None:
            encodings = ["ascii", "utf-8", "utf-16le", "latin-1"]

        results = []

        try:
            # Use GNU strings if available
            if self.tools_cache and self.tools_cache["strings"]["available"]:
                result = subprocess.run(["strings", "-n", str(min_length), file_path],
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:
                            results.append(StringResult(
                                offset=0,  # strings command doesn't give offsets
                                string=line,
                                encoding="auto",
                                length=len(line)
                            ))
                    return results

            # Fallback: manual string extraction
            with open(file_path, 'rb') as f:
                data = f.read()
                offset = 0

                for encoding in encodings:
                    try:
                        # Decode the entire file and find printable strings
                        decoded = data.decode(encoding, errors='ignore')

                        # Find sequences of printable characters
                        current_string = ""
                        start_offset = 0

                        for i, char in enumerate(decoded):
                            if char.isprintable() and not char.isspace():
                                if not current_string:
                                    start_offset = offset + i
                                current_string += char
                            else:
                                if len(current_string) >= min_length:
                                    results.append(StringResult(
                                        offset=start_offset,
                                        string=current_string,
                                        encoding=encoding,
                                        length=len(current_string)
                                    ))
                                current_string = ""

                        # Don't add duplicates from different encodings
                        break

                    except UnicodeDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Error extracting strings: {e}")

        return results

    def get_hexdump(self, file_path: str, offset: int = 0, length: int = 256) -> str:
        """Get hex dump of file"""

        try:
            with open(file_path, 'rb') as f:
                f.seek(offset)
                data = f.read(length)

            # Create hex dump
            lines = []
            for i in range(0, len(data), 16):
                chunk = data[i:i+16]

                # Hex part
                hex_part = ' '.join(f'{b:02x}' for b in chunk)
                hex_part = hex_part.ljust(47)  # 16 bytes * 3 chars - 1 space

                # ASCII part
                ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)

                lines.append("04X")

            return '\n'.join(lines)

        except Exception as e:
            return f"Error creating hexdump: {e}"

    def analyze_entropy(self, file_path: str, block_size: int = 256) -> Dict[str, Any]:
        """Analyze entropy of file"""

        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # Calculate entropy for the whole file
            overall_entropy = self._calculate_entropy(data)

            # Calculate entropy for blocks
            entropy_map = []
            compressed_regions = []
            random_regions = []

            for i in range(0, len(data), block_size):
                block = data[i:i+block_size]
                if len(block) < block_size // 2:  # Skip small blocks
                    continue

                entropy = self._calculate_entropy(block)

                entropy_map.append({
                    "offset": i,
                    "entropy": entropy,
                    "size": len(block)
                })

                # Classify regions
                if entropy < 3.0:  # Low entropy = compressed/predictable
                    compressed_regions.append({"offset": i, "entropy": entropy})
                elif entropy > 7.5:  # High entropy = random/encrypted
                    random_regions.append({"offset": i, "entropy": entropy})

            return {
                "overall": overall_entropy,
                "map": entropy_map,
                "compressed_regions": compressed_regions,
                "random_regions": random_regions
            }

        except Exception as e:
            return {"error": str(e)}

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""

        if not data:
            return 0.0

        # Count byte frequencies
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1

        # Calculate entropy
        entropy = 0.0
        data_len = len(data)

        for count in freq.values():
            p = count / data_len
            entropy -= p * math.log2(p)

        return entropy

    def find_functions(self, file_path: str, tool: str = "auto") -> List[Dict[str, Any]]:
        """Find functions in binary"""

        if tool == "r2" or tool == "auto":
            return self._find_functions_r2(file_path)
        elif tool == "ida":
            return self._find_functions_ida(file_path)
        elif tool == "ghidra":
            return self._find_functions_ghidra(file_path)
        else:
            return [{"error": f"Unsupported tool: {tool}"}]

    def _find_functions_r2(self, file_path: str) -> List[Dict[str, Any]]:
        """Find functions using radare2"""
        try:
            result = subprocess.run(["r2", "-A", "-q", "-c", "afl", file_path],
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                functions = []
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                addr = int(parts[0], 16)
                                size = int(parts[1], 16)
                                name = ' '.join(parts[2:])
                                functions.append({
                                    "address": addr,
                                    "size": size,
                                    "name": name,
                                    "tool": "r2"
                                })
                            except ValueError:
                                continue
                return functions
            else:
                return [{"error": "r2 function analysis failed"}]
        except Exception as e:
            return [{"error": str(e)}]

    def _find_functions_ida(self, file_path: str) -> List[Dict[str, Any]]:
        """Find functions using IDA Pro (placeholder)"""
        return [{"note": "IDA Pro function analysis requires IDA scripting setup"}]

    def _find_functions_ghidra(self, file_path: str) -> List[Dict[str, Any]]:
        """Find functions using Ghidra (placeholder)"""
        return [{"note": "Ghidra function analysis requires Ghidra scripting setup"}]

    def detect_file_type(self, file_path: str) -> str:
        """Detect file type"""
        try:
            result = subprocess.run(["file", file_path], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.split(': ', 1)[1].strip() if ': ' in result.stdout else result.stdout.strip()
            else:
                # Fallback: check extension
                ext = Path(file_path).suffix.lower()
                if ext == '.exe':
                    return "PE executable"
                elif ext == '.dll':
                    return "PE dynamic link library"
                elif ext in ['.dki', '.dka']:
                    return "Directmedia database file"
                else:
                    return f"Unknown ({ext})"
        except:
            return "Unknown"

    def analyze_pe_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze Windows PE file (basic info)"""

        try:
            with open(file_path, 'rb') as f:
                # Read DOS header
                dos_header = f.read(64)

                if len(dos_header) < 64:
                    return {"error": "File too small for PE"}

                # Check MZ signature
                if dos_header[0:2] != b'MZ':
                    return {"error": "Not a valid PE file (missing MZ signature)"}

                # Get PE header offset
                pe_offset = struct.unpack('<I', dos_header[60:64])[0]

                # Read PE header
                f.seek(pe_offset)
                pe_header = f.read(24)

                if len(pe_header) < 24 or pe_header[0:4] != b'PE\x00\x00':
                    return {"error": "Invalid PE header"}

                # Basic PE info
                machine = struct.unpack('<H', pe_header[4:6])[0]
                num_sections = struct.unpack('<H', pe_header[6:8])[0]

                machine_names = {
                    0x014c: "Intel 386",
                    0x0200: "Intel Itanium",
                    0x8664: "AMD64"
                }

                return {
                    "valid_pe": True,
                    "machine": machine_names.get(machine, f"Unknown (0x{machine:04X})"),
                    "num_sections": num_sections,
                    "dos_stub_size": pe_offset - 64
                }

        except Exception as e:
            return {"error": str(e)}
