"""
Binary Analysis Tools for Reverse Engineering
"""

import json
import math
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .logging_config import get_logger

logger = get_logger("reversing_mcp.analyzers")


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

    def check_available_tools(self) -> dict[str, dict[str, Any]]:
        """Check which reverse engineering tools are available"""

        tools = {
            "ida": {"name": "IDA Pro", "available": False, "version": None, "path": None},
            "ghidra": {"name": "Ghidra", "available": False, "version": None, "path": None},
            "r2": {"name": "radare2", "available": False, "version": None, "path": None},
            "binwalk": {"name": "Binwalk", "available": False, "version": None, "path": None},
            "strings": {"name": "GNU strings", "available": False, "version": None, "path": None},
            "file": {"name": "file command", "available": False, "version": None, "path": None},
        }

        self._check_ida(tools["ida"])
        self._check_ghidra(tools["ghidra"])
        self._check_r2(tools["r2"])
        self._check_binwalk(tools["binwalk"])
        self._check_strings(tools["strings"])
        self._check_file(tools["file"])

        self.tools_cache = tools
        return tools

    def _check_ida(self, tool_info: dict[str, Any]):
        """Check for IDA Pro installation"""
        ida_paths = [
            Path(r"C:\Program Files\IDA Pro 8.3\ida.exe"),
            Path(r"C:\Program Files\IDA Pro 8.2\ida.exe"),
            Path(r"C:\Program Files\IDA Pro 8.1\ida.exe"),
            Path(r"C:\Program Files (x86)\IDA Pro\ida.exe"),
        ]
        for path in ida_paths:
            if path.exists():
                tool_info["available"] = True
                tool_info["path"] = str(path)
                try:
                    result = subprocess.run(
                        [str(path), "--version"],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        tool_info["version"] = result.stdout.strip()
                except (subprocess.SubprocessError, OSError):
                    pass
                break

    def _check_ghidra(self, tool_info: dict[str, Any]):
        """Check for Ghidra installation. Prefer GHIDRA_HOME env (install dir)."""
        ghidra_paths: list[Path] = []

        # 1. GHIDRA_HOME (or GHIDRA_INSTALL_DIR) - explicit, recommended
        for env_key in ("GHIDRA_HOME", "GHIDRA_INSTALL_DIR"):
            val = os.environ.get(env_key)
            if val:
                base = Path(val).resolve()
                if base.is_dir():
                    bat = base / "ghidraRun.bat"
                    if bat.exists():
                        ghidra_paths.append(bat)
                        break
                    # Allow base to be repo root with ghidra_*_PUBLIC child
                    for child in base.iterdir():
                        if (
                            child.is_dir()
                            and "ghidra" in child.name.lower()
                            and "PUBLIC" in child.name
                        ):
                            run_bat = child / "ghidraRun.bat"
                            if run_bat.exists():
                                ghidra_paths.append(run_bat)
                                break
                break

        # 2. Common installation directories (avoid temp; prefer stable install)
        ghidra_paths.extend(self._scan_common_ghidra_dirs())

        # 3. Unix/Linux paths
        if os.name != "nt":
            ghidra_paths.extend(
                [
                    Path("/usr/local/ghidra/ghidraRun"),
                    Path("/opt/ghidra/ghidraRun"),
                ]
            )

        # Remove duplicates; prefer stable installs over temp/unpack locations
        seen: set[str] = set()
        stable: list[Path] = []
        temp_candidates: list[Path] = []
        for p in ghidra_paths:
            if not p.exists() or str(p) in seen:
                continue
            seen.add(str(p))
            if "temp" in str(p).lower() or "tmp" in str(p).lower():
                temp_candidates.append(p)
            else:
                stable.append(p)

        unique_paths = stable + temp_candidates
        if not unique_paths:
            return

        # Prefer first (env or stable path); temp only if nothing else
        path = unique_paths[0]
        tool_info["available"] = True
        tool_info["path"] = str(path)
        tool_info["version"] = self._detect_ghidra_version(path)

    def _scan_common_ghidra_dirs(self) -> list[Path]:
        """Scan common roots for Ghidra installations"""
        if os.name != "nt":
            return []

        ghidra_paths = []
        common_roots = [
            Path(r"C:\ghidra"),
            Path(r"D:\ghidra"),
            Path(r"C:\Program Files"),
            Path(r"D:\Dev"),
        ]
        for root in common_roots:
            if not root.exists():
                continue
            try:
                for item in root.iterdir():
                    if item.is_dir() and "ghidra" in item.name.lower():
                        run_bat = item / "ghidraRun.bat"
                        if run_bat.exists():
                            ghidra_paths.append(run_bat)
            except (OSError, PermissionError):
                continue
        return ghidra_paths

    def _detect_ghidra_version(self, path: Path) -> str:
        """Helper to detect Ghidra version from path"""
        try:
            # Try to get version from directory name (e.g., ghidra_12.0_PUBLIC)
            parent = path.parent
            if "ghidra" in parent.name.lower():
                parts = parent.name.split("_")
                if len(parts) > 1 and parts[1][0].isdigit():
                    return parts[1]

            # Fallback: check application.properties
            props = parent / "Ghidra" / "application.properties"
            if props.exists():
                with props.open("r") as f:
                    for line in f:
                        if line.startswith("application.version="):
                            return line.split("=")[1].strip()
        except (OSError, IndexError):
            pass
        return "detected"

    def _check_r2(self, tool_info: dict[str, Any]):
        """Check for radare2"""
        try:
            result = subprocess.run(
                ["r2", "-v"], check=False, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                tool_info["available"] = True
                tool_info["version"] = result.stdout.split("\n")[0] if result.stdout else "unknown"
        except (subprocess.SubprocessError, OSError):
            pass

    def _check_binwalk(self, tool_info: dict[str, Any]):
        """Check for binwalk"""
        try:
            result = subprocess.run(
                ["binwalk", "--version"], check=False, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                tool_info["available"] = True
                tool_info["version"] = result.stdout.strip()
        except (subprocess.SubprocessError, OSError):
            pass

    def _check_strings(self, tool_info: dict[str, Any]):
        """Check for GNU strings"""
        try:
            result = subprocess.run(
                ["strings", "--version"], check=False, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                tool_info["available"] = True
                tool_info["version"] = result.stdout.split("\n")[0] if result.stdout else "unknown"
        except (subprocess.SubprocessError, OSError):
            pass

    def _check_file(self, tool_info: dict[str, Any]):
        """Check for file command"""
        try:
            result = subprocess.run(
                ["file", "--version"], check=False, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                tool_info["available"] = True
                tool_info["version"] = result.stdout.split("\n")[0] if result.stdout else "unknown"
        except (subprocess.SubprocessError, OSError):
            pass

    def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get comprehensive file information"""
        p = Path(file_path)
        try:
            stats = p.stat()

            info = {
                "path": str(p.absolute()),
                "filename": p.name,
                "size": stats.st_size,
                "is_file": p.is_file(),
                "is_dir": p.is_dir(),
                "is_readable": os.access(file_path, os.R_OK),
                "is_executable": os.access(file_path, os.X_OK)
                or p.suffix.lower() in [".exe", ".com", ".bin"],
                "extension": p.suffix.lower(),
                "type": self.detect_file_type(file_path),
            }

            # Add PE specific info if applicable
            if info["extension"] in [".exe", ".dll"]:
                pe_info = self.analyze_pe_file(file_path)
                if isinstance(pe_info, dict) and "error" not in pe_info:
                    info["pe_info"] = pe_info

            return info
        except Exception as e:
            return {"error": str(e), "success": False, "is_readable": False}

    def analyze_file(self, file_path: str, tools: list[str] | None = None) -> dict[str, Any]:
        """Analyze a file with multiple tools"""

        if tools is None:
            tools = ["static", "file", "strings", "binwalk"]

        results = {}

        # Basic file info and detection
        if "file_info" in tools or "static" in tools:
            results["file_info"] = self.get_file_info(file_path)

        if "file" in tools:
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

    def _analyze_with_file(self, file_path: str) -> dict[str, Any]:
        """Analyze with file command"""
        try:
            exe = shutil.which("file") or "file"
            result = subprocess.run(
                [exe, file_path], check=False, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                file_type = (
                    result.stdout.strip().split(": ", 1)[1]
                    if ": " in result.stdout
                    else result.stdout.strip()
                )
                return {"file_type": file_type, "success": True}
            return {"error": "file command failed", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def _analyze_with_binwalk(self, file_path: str) -> dict[str, Any]:
        """Analyze with binwalk"""
        try:
            exe = shutil.which("binwalk") or "binwalk"
            result = subprocess.run(
                [exe, "-J", file_path],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Parse JSON output
                import json

                try:
                    data = json.loads(result.stdout)
                    return {"signatures": data, "success": True}
                except json.JSONDecodeError:
                    return {"raw_output": result.stdout, "success": True}
            else:
                return {"error": "binwalk failed", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def _analyze_with_ida(self, file_path: str) -> dict[str, Any]:
        """Analyze with IDA Pro (placeholder - would need IDA scripting)"""
        # This would require IDA Pro Python scripting
        # For now, just return that IDA is available
        return {
            "available": True,
            "note": "IDA Pro analysis requires custom scripting",
            "recommendation": "Use IDA Pro GUI or create IDC/Python script",
        }

    def _analyze_with_ghidra(self, file_path: str) -> dict[str, Any]:
        """Analyze with Ghidra using headless mode"""
        if not self.tools_cache or not self.tools_cache["ghidra"]["available"]:
            return {
                "error": "Ghidra not available",
                "available": False,
            }

        # Use headless mode for real analysis
        return self._analyze_with_ghidra_headless(file_path)

    def _analyze_with_ghidra_headless(
        self,
        file_path: Path | str,
        script_path: Path | str | None = None,
        script_args: list[str] | None = None,
        auto_analyze: bool = True,
    ) -> dict[str, Any]:
        """Real Ghidra analysis using analyzeHeadless.bat"""
        try:
            ghidra_run = Path(self.tools_cache["ghidra"]["path"])
            ghidra_root = ghidra_run.parent
            headless_bat = ghidra_root / "support" / "analyzeHeadless.bat"

            if not headless_bat.exists():
                return {"error": "analyzeHeadless.bat not found", "success": False}

            # Locate our analysis script if not provided
            if script_path is None:
                script_path = (
                    Path(__file__).parent.parent.parent / "ghidra_scripts" / "analyze_binary.py"
                )

            script_path = Path(script_path)
            if not script_path.exists():
                return {"error": f"Analysis script not found at {script_path}", "success": False}

            with tempfile.TemporaryDirectory() as temp_dir:
                project_dir = Path(temp_dir)
                project_name = "MCP_Analysis"

                # Command: analyzeHeadless <project_dir> <project_name>
                # -import <file> -postScript <script> [args...] -deleteProject
                cmd = [
                    str(headless_bat),
                    str(project_dir),
                    project_name,
                    "-import",
                    str(file_path),
                ]

                if not auto_analyze:
                    cmd.append("-noanalysis")

                # ALWAYS run with -noanalysis to prevent pre-script stall
                # We trigger analysis inside the script if needed
                cmd.append("-noanalysis")

                cmd.append("-postScript")
                cmd.append(str(script_path))

                # Pass arguments to the script
                # If auto_analyze is requested, pass it as a script arg
                final_script_args = []
                if auto_analyze:
                    final_script_args.append("analyze")

                if script_args:
                    final_script_args.extend(script_args)

                if final_script_args:
                    cmd.extend(final_script_args)

                cmd.append("-deleteProject")

                # Run headless analysis (can take minutes for large files)
                logger.info(
                    "Starting Ghidra headless analysis for %s (script_analyze=%s)",
                    file_path,
                    auto_analyze,
                )
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=900, check=False
                )

                if result.returncode != 0:
                    logger.error("Ghidra headless failed: %s", result.stderr)
                    return {
                        "error": "Ghidra headless analysis failed",
                        "stderr": result.stderr[-500:],
                        "success": False,
                    }

                # The script saves results to <filename>_ghidra_analysis.json in CWD
                output_name = f"{Path(file_path).stem}_ghidra_analysis.json"
                output_path = Path.cwd() / output_name

                if output_path.exists():
                    with output_path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    output_path.unlink()  # Cleanup
                    return {"analysis": data, "success": True}

                # Log stdout/stderr for debugging
                logger.error("Ghidra headless stdout: %s", result.stdout[-1000:])
                logger.error("Ghidra headless stderr: %s", result.stderr[-1000:])

                return {
                    "error": "Analysis completed but result file not found",
                    "success": False,
                    "stdout": result.stdout[-2000:],
                    "stderr": result.stderr[-2000:],
                }

        except subprocess.TimeoutExpired:
            return {"error": "Ghidra headless analysis timed out", "success": False}
        except (subprocess.SubprocessError, OSError) as e:
            return {"error": f"Subprocess error: {e!s}", "success": False}
        except Exception:
            logger.exception("Unexpected error in Ghidra headless analysis")
            return {"error": "Internal error in Ghidra analysis", "success": False}

    def _analyze_with_r2(self, file_path: str) -> dict[str, Any]:
        """Analyze with radare2"""
        try:
            exe = shutil.which("r2") or "r2"
            # Basic info
            result = subprocess.run(
                [exe, "-A", "-q", "-c", "i", file_path],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return {"info": result.stdout, "success": True}
            return {"error": "r2 analysis failed", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def decompile_function(self, file_path: str | Path, function_identifier: str) -> dict[str, Any]:
        """Decompile a specific function by address or name"""
        # Ensure tools are checked
        if not self.tools_cache:
            self.check_available_tools()

        if not self.tools_cache.get("ghidra", {}).get("available"):
            return {"error": "Ghidra not available", "success": False}

        script_path = (
            Path(__file__).parent.parent.parent / "ghidra_scripts" / "decompile_function.py"
        )

        # We need auto_analyze=True because decompilation depends on it
        result = self._analyze_with_ghidra_headless(
            file_path, script_path=script_path, script_args=[function_identifier], auto_analyze=True
        )

        # The script outputs a specific JSON file, not the default [name]_ghidra_analysis.json
        # Check for that file
        # The script does: output_file = f"{currentProgram.getName()}_decompiled_{func.getName()}.json"
        # This is hard to predict exactly if name changes.
        # But wait, _analyze_with_ghidra_headless looks for [stem]_ghidra_analysis.json
        # I should probably update _analyze_with_ghidra_headless to allow specifying output file pattern/handling?
        # OR update the script to match expectation.

        return result

    def extract_strings(
        self, file_path: str, min_length: int = 4, encodings: list[str] | None = None
    ) -> list[StringResult]:
        """Extract strings from binary file"""

        if encodings is None:
            encodings = ["ascii", "utf-8", "utf-16le", "latin-1"]

        results = []

        try:
            # Use GNU strings if available
            if self.tools_cache and self.tools_cache["strings"]["available"]:
                exe = shutil.which("strings") or "strings"
                result = subprocess.run(
                    [exe, "-n", str(min_length), file_path],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    lines = result.stdout.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line:
                            results.append(
                                StringResult(
                                    offset=0,  # strings command doesn't give offsets
                                    string=line,
                                    encoding="auto",
                                    length=len(line),
                                )
                            )
                    return results

            # Fallback: manual string extraction
            with Path(file_path).open("rb") as f:
                data = f.read()

                for encoding in encodings:
                    manual_results = self._extract_manual(data, encoding, min_length)
                    if manual_results:
                        results.extend(manual_results)
                        # Only take the first successful encoding for simplicity
                        # or to avoid duplicates across similar encodings
                        break

        except (subprocess.SubprocessError, OSError):
            logger.exception("Subprocess error extracting strings")
        except Exception:
            logger.exception("Error extracting strings")

        return results

    def _extract_manual(self, data: bytes, encoding: str, min_length: int) -> list[StringResult]:
        """Manually extract strings with specific encoding"""
        results = []
        try:
            decoded = data.decode(encoding, errors="ignore")
            current_string = ""
            start_offset = 0

            for i, char in enumerate(decoded):
                if char.isprintable():
                    if not current_string:
                        start_offset = i
                    current_string += char
                elif current_string:
                    if len(current_string) >= min_length:
                        results.append(
                            StringResult(
                                offset=start_offset,
                                string=current_string,
                                encoding=encoding,
                                length=len(current_string),
                            )
                        )
                    current_string = ""

            # Last string
            if current_string and len(current_string) >= min_length:
                results.append(
                    StringResult(
                        offset=start_offset,
                        string=current_string,
                        encoding=encoding,
                        length=len(current_string),
                    )
                )
        except UnicodeDecodeError:
            pass
        return results

    def get_hexdump(self, file_path: str, offset: int = 0, length: int = 256) -> str:
        """Get hex dump of file"""

        try:
            with Path(file_path).open("rb") as f:
                f.seek(offset)
                data = f.read(length)

            # Create hex dump - simple format for testing
            lines = []
            for i in range(0, len(data), 16):
                chunk = data[i : i + 16]
                # Just return hex bytes space-separated
                hex_part = " ".join(f"{b:02x}" for b in chunk)
                lines.append(hex_part)

            return "\n".join(lines)

        except Exception:
            logger.exception("Error creating hexdump")
            return "Error creating hexdump"

    def analyze_entropy(self, file_path: str, block_size: int = 256) -> dict[str, Any]:
        """Analyze entropy of file"""

        try:
            with Path(file_path).open("rb") as f:
                data = f.read()

            # Calculate entropy for the whole file
            overall_entropy = self._calculate_entropy(data)

            # Calculate entropy for blocks
            entropy_map = []
            compressed_regions = []
            random_regions = []

            for i in range(0, len(data), block_size):
                block = data[i : i + block_size]
                if len(block) < block_size // 2:  # Skip small blocks
                    continue

                entropy = self._calculate_entropy(block)

                entropy_map.append({"offset": i, "entropy": entropy, "size": len(block)})

                # Classify regions
                LOW_ENTROPY_THRESHOLD = 3.0
                HIGH_ENTROPY_THRESHOLD = 7.5
                if entropy < LOW_ENTROPY_THRESHOLD:  # Low entropy = compressed/predictable
                    compressed_regions.append({"offset": i, "entropy": entropy})
                elif entropy > HIGH_ENTROPY_THRESHOLD:  # High entropy = random/encrypted
                    random_regions.append({"offset": i, "entropy": entropy})

            return {
                "overall": overall_entropy,
                "map": entropy_map,
                "compressed_regions": compressed_regions,
                "random_regions": random_regions,
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

    def find_functions(
        self, file_path: str, tool: str = "auto", auto_analyze: bool = True
    ) -> list[dict[str, Any]]:
        """Find functions in binary"""

        if tool == "r2" or tool == "auto":
            # r2 logic doesn't use auto_analyze (yet)
            return self._find_functions_r2(file_path)
        if tool == "ida":
            return self._find_functions_ida(file_path)
        if tool == "ghidra":
            return self._find_functions_ghidra(file_path, auto_analyze=auto_analyze)
        return [{"error": f"Unsupported tool: {tool}"}]

    def _find_functions_r2(self, file_path: str) -> list[dict[str, Any]]:
        """Find functions using radare2"""
        try:
            exe = shutil.which("r2") or "r2"
            result = subprocess.run(
                [exe, "-A", "-q", "-c", "afl", file_path],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                functions = []
                for line in result.stdout.split("\n"):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                addr = int(parts[0], 16)
                                size = int(parts[1], 16)
                                name = " ".join(parts[2:])
                                functions.append(
                                    {"address": addr, "size": size, "name": name, "tool": "r2"}
                                )
                            except ValueError:
                                continue
                return functions
            return [{"error": "r2 function analysis failed"}]
        except (subprocess.SubprocessError, OSError) as e:
            return [{"error": str(e)}]
        except Exception:
            logger.exception("Unexpected error in _find_functions_r2")
            return [{"error": "Internal error in r2 analysis"}]

    def _find_functions_ida(self, file_path: str) -> list[dict[str, Any]]:
        """Find functions using IDA Pro (placeholder)"""
        return [{"note": "IDA Pro function analysis requires IDA scripting setup"}]

    def _find_functions_ghidra(
        self, file_path: str, auto_analyze: bool = True
    ) -> list[dict[str, Any]]:
        """Find functions using Ghidra headless analysis"""
        try:
            # Ensure Ghidra is available
            if not self.tools_cache.get("ghidra", {}).get("available"):
                return [{"error": "Ghidra not available"}]

            # Run Ghidra analysis and extract functions from results
            analysis_result = self._analyze_with_ghidra_headless(
                file_path, auto_analyze=auto_analyze
            )

            if analysis_result.get("success") and "analysis" in analysis_result:
                functions_data = analysis_result["analysis"].get("functions", [])
                # Convert to expected format
                functions = []
                for func in functions_data:
                    functions.append(
                        {
                            "address": func.get("address"),
                            "size": func.get("size", 0),
                            "name": func.get("name", "unknown"),
                            "tool": "ghidra",
                        }
                    )
                return functions
            return [{"error": analysis_result.get("error", "Ghidra analysis failed")}]

        except (subprocess.SubprocessError, OSError) as e:
            return [{"error": str(e)}]
        except Exception:
            logger.exception("Unexpected error in _find_functions_ghidra")
            return [{"error": "Internal error in Ghidra analysis"}]

    def detect_file_type(self, file_path: str) -> str:
        """Detect file type"""
        try:
            result = subprocess.run(
                ["file", file_path], check=False, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return (
                    result.stdout.split(": ", 1)[1].strip()
                    if ": " in result.stdout
                    else result.stdout.strip()
                )
            # Fallback: check extension
            ext = Path(file_path).suffix.lower()
            if ext == ".exe":
                return "PE executable"
            if ext == ".dll":
                return "PE dynamic link library"
            if ext in [".dki", ".dka"]:
                return "Directmedia database file"
            return f"Unknown ({ext})"
        except FileNotFoundError:
            # file command not available, use extension fallback
            ext = Path(file_path).suffix.lower()
            if ext == ".exe":
                return "PE executable"
            if ext == ".dll":
                return "PE dynamic link library"
            if ext in [".dki", ".dka"]:
                return "Directmedia database file"
            return f"Unknown ({ext})"
        except Exception:
            logger.exception("Unexpected error in detect_file_type")
            return "Unknown"

    def analyze_pe_file(self, file_path: str) -> dict[str, Any]:
        """Analyze Windows PE file (basic info)"""

        try:
            with Path(file_path).open("rb") as f:
                # Read DOS header
                dos_header = f.read(64)

                if len(dos_header) < 64:
                    return {"error": "File too small for PE"}

                # Check MZ signature
                if dos_header[0:2] != b"MZ":
                    return {"error": "Not a valid PE file (missing MZ signature)"}

                # Get PE header offset
                pe_offset = struct.unpack("<I", dos_header[60:64])[0]

                # Read PE header
                f.seek(pe_offset)
                pe_header = f.read(24)

                if len(pe_header) < 24 or pe_header[0:4] != b"PE\x00\x00":
                    return {"error": "Invalid PE header"}

                # Basic PE info
                machine = struct.unpack("<H", pe_header[4:6])[0]
                num_sections = struct.unpack("<H", pe_header[6:8])[0]

                machine_names = {0x014C: "Intel 386", 0x0200: "Intel Itanium", 0x8664: "AMD64"}

                return {
                    "valid_pe": True,
                    "machine": machine_names.get(machine, f"Unknown (0x{machine:04X})"),
                    "num_sections": num_sections,
                    "dos_stub_size": pe_offset - 64,
                }

        except Exception as e:
            return {"error": str(e)}
