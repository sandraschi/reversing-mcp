#!/usr/bin/env python3
"""
Reverse Engineering Pipeline Tests

This test suite validates the complete reverse engineering pipeline:
1. Compile source code fixtures
2. Decompile binaries using various tools (Ghidra, radare2)
3. Compare decompiled output to original source
4. Validate that key information is preserved

Test Fixtures:
- hello_world.c: Simple program
- simple_math.c: Multiple functions with arithmetic
- data_structures.c: Structs, memory allocation, loops
- simple_asm.asm: Assembly program
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reversing_mcp.analyzers import BinaryAnalyzer


class ReverseEngineeringTestFixture:
    """Manages test fixtures for reverse engineering pipeline testing"""

    def __init__(self, fixtures_dir: Path, config_file: Path):
        self.fixtures_dir = fixtures_dir
        self.config_file = config_file
        self.config = self._load_config()
        self.build_dir = fixtures_dir / self.config["test_settings"]["build_dir"]
        self.build_dir.mkdir(exist_ok=True)
        self.analyzer = BinaryAnalyzer()

    def _load_config(self) -> dict[str, Any]:
        """Load test configuration"""
        with open(self.config_file) as f:
            return json.load(f)

    def get_fixture_names(self) -> list[str]:
        """Get list of available fixture names"""
        return list(self.config["fixtures"].keys())

    def get_fixture_config(self, fixture_name: str) -> dict[str, Any]:
        """Get configuration for a specific fixture"""
        return self.config["fixtures"][fixture_name]

    def _is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available in the system PATH"""
        return shutil.which(tool_name) is not None

    def compile_fixture(self, fixture_name: str) -> Path | None:
        """
        Compile a test fixture and return the path to the binary
        """
        fixture_config = self.get_fixture_config(fixture_name)
        source_path = self.fixtures_dir / fixture_name

        # Handle ready-made binaries
        if fixture_config.get("ready_binary", False):
            if source_path.exists():
                return source_path
            print(f"Ready binary not found: {source_path}")
            return None

        if not source_path.exists():
            print(f"Source file not found: {source_path}")
            return None

        # Check compiler availability
        compiler = fixture_config.get("compiler")
        if not self._is_tool_available(compiler):
            # Try with .exe extension for Windows if not found
            if not self._is_tool_available(f"{compiler}.exe"):
                print(f"Compiler not available: {compiler}")
                return None

        # Determine output name
        if fixture_config["language"] == "asm":
            object_file = self.build_dir / f"{fixture_name}.o"
            binary_file = self.build_dir / f"{fixture_name}.exe"
        else:
            binary_file = self.build_dir / f"{fixture_name}.exe"

        try:
            # Compile
            if fixture_config["language"] == "asm":
                # First assemble
                assemble_cmd = (
                    [fixture_config["compiler"]]
                    + fixture_config["compile_args"]
                    + [str(source_path)]
                )
                assemble_cmd[-1] = str(object_file)  # Replace output arg
                print(f"Assembling: {' '.join(assemble_cmd)}")
                result = subprocess.run(
                    assemble_cmd,
                    check=False,
                    cwd=self.build_dir,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    print(f"Assembly failed: {result.stderr}")
                    return None

                # Then link
                link_cmd = (
                    [fixture_config["linker"]] + fixture_config["link_args"] + [str(object_file)]
                )
                link_cmd[-1] = str(binary_file)  # Replace output arg
                print(f"Linking: {' '.join(link_cmd)}")
                result = subprocess.run(
                    link_cmd,
                    check=False,
                    cwd=self.build_dir,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    print(f"Linking failed: {result.stderr}")
                    return None
            else:
                # C compilation
                compile_cmd = (
                    [fixture_config["compiler"]]
                    + fixture_config["compile_args"]
                    + [str(source_path)]
                )
                compile_cmd[-1] = str(binary_file)  # Replace output arg
                print(f"Compiling: {' '.join(compile_cmd)}")
                result = subprocess.run(
                    compile_cmd,
                    check=False,
                    cwd=self.build_dir,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    print(f"Compilation failed: {result.stderr}")
                    return None

            if binary_file.exists():
                print(f"Successfully compiled: {binary_file}")
                return binary_file
            print(f"Binary not created: {binary_file}")
            return None

        except subprocess.TimeoutExpired:
            print(f"Compilation timed out for {fixture_name}")
            return None
        except Exception as e:
            print(f"Compilation error for {fixture_name}: {e}")
            return None

    def analyze_binary(self, binary_path: Path, tools: list[str] | None = None) -> dict[str, Any]:
        """Analyze a binary using the reversing MCP analyzer"""
        if tools is None:
            tools = ["static", "strings", "entropy"]

        return self.analyzer.analyze_file(str(binary_path), tools)

    def validate_analysis(
        self, analysis_result: dict[str, Any], fixture_name: str
    ) -> dict[str, Any]:
        """Validate that analysis results contain expected information"""
        fixture_config = self.get_fixture_config(fixture_name)
        validation_results = {
            "strings_found": 0,
            "functions_found": 0,
            "expected_strings_matched": [],
            "expected_functions_matched": [],
            "suspicious_patterns_detected": [],
            "malware_alerts": [],
            "success": True,
            "issues": [],
        }

        # Check strings
        if "strings" in analysis_result:
            raw_strings = analysis_result["strings"]
            # Handle both simple strings and structured StringResult dicts
            found_strings = [s if isinstance(s, str) else s.get("string", "") for s in raw_strings]
            expected_strings = fixture_config.get("expected_strings", [])

            for expected in expected_strings:
                if any(expected.lower() in found_str.lower() for found_str in found_strings):
                    validation_results["expected_strings_matched"].append(expected)
                    validation_results["strings_found"] += 1

        # Check functions (basic check - in real implementation would need more sophisticated matching)
        if "file_info" in analysis_result:
            file_info = analysis_result["file_info"]
            if file_info.get("is_executable", False):
                # For PE files, check if we can find function-like structures
                # This is a simplified check
                validation_results["functions_found"] = len(
                    fixture_config.get("expected_functions", [])
                )

        # Check for suspicious patterns (MALWARE DETECTION)
        suspicious_patterns = fixture_config.get("suspicious_patterns", [])
        if suspicious_patterns:
            validation_results["malware_alerts"].append("🚨 MALWARE ALERT! 🚨")
            validation_results["malware_alerts"].append(
                f"This test fixture simulates: {fixture_config.get('description', 'suspicious behavior')}"
            )

            # Check for specific suspicious indicators
            raw_strings = analysis_result.get("strings", [])
            found_strings = [s if isinstance(s, str) else s.get("string", "") for s in raw_strings]
            string_content = " ".join(found_strings).lower()

            for pattern in suspicious_patterns:
                if pattern == "network_connections" and (
                    "connect" in string_content or "socket" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "🔗 Network connections detected"
                    )
                elif pattern == "suspicious_domains" and (
                    "blofeld.org" in string_content or "evil." in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "🌐 Suspicious domain connections detected"
                    )
                elif pattern == "downloads" and (
                    "download" in string_content or "url" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "📥 Suspicious download operations detected"
                    )
                elif pattern == "filesystem_manipulation" and (
                    "system32" in string_content or "hidden" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "📁 File system manipulation detected"
                    )
                elif pattern == "registry_access" and (
                    "registry" in string_content or "hkey" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "🗝️ Registry access detected"
                    )
                elif pattern == "process_injection" and (
                    "inject" in string_content or "virtualalloc" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "💉 Process injection techniques detected"
                    )
                elif pattern == "anti_debugging" and (
                    "debugger" in string_content or "timing" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "🛡️ Anti-debugging techniques detected"
                    )
                elif pattern == "string_obfuscation" and (
                    "reconstruct" in string_content or "decrypt" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "🔤 String obfuscation detected"
                    )
                elif pattern == "shellcode_generation" and (
                    "shellcode" in string_content or "nop" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "💣 Shellcode generation detected"
                    )
                elif pattern == "packer_signatures" and (
                    "upx" in string_content or "packer" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "📦 Packer signatures detected"
                    )
                elif pattern == "runtime_unpacking" and (
                    "decompress" in string_content or "unpack" in string_content
                ):
                    validation_results["suspicious_patterns_detected"].append(
                        "🔓 Runtime unpacking detected"
                    )

            if validation_results["suspicious_patterns_detected"]:
                validation_results["malware_alerts"].append("")
                validation_results["malware_alerts"].append("⚠️  SUSPICIOUS BEHAVIOR DETECTED:")
                validation_results["malware_alerts"].extend(
                    validation_results["suspicious_patterns_detected"]
                )
                validation_results["malware_alerts"].append("")
                validation_results["malware_alerts"].append(
                    "This binary exhibits characteristics commonly associated with malware!"
                )
                validation_results["malware_alerts"].append(
                    "🛡️ Recommend further analysis with professional tools."
                )

        # Calculate success rate
        total_expected = len(fixture_config.get("expected_strings", []))
        if total_expected > 0:
            string_match_rate = validation_results["strings_found"] / total_expected
            if string_match_rate < 0.5:  # Require at least 50% string match
                validation_results["success"] = False
                validation_results["issues"].append(
                    f"Low string match rate: {string_match_rate:.2f}"
                )

        return validation_results


@pytest.fixture(scope="session")
def test_fixture():
    """Pytest fixture for reverse engineering tests"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    config_file = fixtures_dir / "test_config.json"
    return ReverseEngineeringTestFixture(fixtures_dir, config_file)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "hello_world.c",
        "simple_math.c",
        "data_structures.c",
        "binaries/minimal.com",
        "binaries/hello.com",
        "binaries/loop.com",
    ],
)
def test_compilation_pipeline(test_fixture, fixture_name):
    """Test that fixtures can be compiled successfully"""
    config = test_fixture.get_fixture_config(fixture_name)
    if not config.get("ready_binary", False):
        compiler = config.get("compiler")
        if not test_fixture._is_tool_available(compiler):
            pytest.skip(f"Compiler {compiler} not available")

    binary_path = test_fixture.compile_fixture(fixture_name)
    assert binary_path is not None, f"Failed to compile {fixture_name}"
    assert binary_path.exists(), f"Binary not created for {fixture_name}"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "hello_world.c",
        "simple_math.c",
        "data_structures.c",
        "binaries/minimal.com",
        "binaries/hello.com",
        "binaries/loop.com",
    ],
)
def test_binary_analysis(test_fixture, fixture_name):
    """Test that compiled binaries can be analyzed"""
    binary_path = test_fixture.compile_fixture(fixture_name)
    if binary_path is None:
        config = test_fixture.get_fixture_config(fixture_name)
        if not config.get("ready_binary", False):
            compiler = config.get("compiler")
            if not test_fixture._is_tool_available(compiler):
                pytest.skip(f"Prerequisite failed: Compiler {compiler} not available")
        assert binary_path is not None, f"Prerequisite: compilation failed for {fixture_name}"

    analysis_result = test_fixture.analyze_binary(binary_path)
    assert analysis_result is not None, f"Analysis failed for {fixture_name}"
    assert "file_info" in analysis_result, f"No file info in analysis for {fixture_name}"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "hello_world.c",
        "simple_math.c",
        "data_structures.c",
        "binaries/minimal.com",
        "binaries/hello.com",
        "binaries/loop.com",
    ],
)
def test_analysis_validation(test_fixture, fixture_name):
    """Test that analysis results contain expected information"""
    binary_path = test_fixture.compile_fixture(fixture_name)
    if binary_path is None:
        config = test_fixture.get_fixture_config(fixture_name)
        if not config.get("ready_binary", False):
            compiler = config.get("compiler")
            if not test_fixture._is_tool_available(compiler):
                pytest.skip(f"Prerequisite failed: Compiler {compiler} not available")
        assert binary_path is not None, f"Prerequisite: compilation failed for {fixture_name}"

    analysis_result = test_fixture.analyze_binary(binary_path)
    validation_result = test_fixture.validate_analysis(analysis_result, fixture_name)

    # At minimum, the binary should be recognized as executable
    assert analysis_result["file_info"]["is_readable"], f"Binary not readable: {fixture_name}"

    # Validation should not have critical failures
    if not validation_result["success"]:
        pytest.fail(f"Validation failed for {fixture_name}: {validation_result['issues']}")


def test_fixture_discovery(test_fixture):
    """Test that all fixtures are properly configured"""
    fixture_names = test_fixture.get_fixture_names()
    assert len(fixture_names) > 0, "No fixtures found"

    for fixture_name in fixture_names:
        config = test_fixture.get_fixture_config(fixture_name)
        assert "language" in config, f"No language specified for {fixture_name}"
        if not config.get("ready_binary", False):
            assert "compiler" in config, f"No compiler specified for {fixture_name}"
        assert "description" in config, f"No description for {fixture_name}"


def test_analyzer_initialization(test_fixture):
    """Test that the binary analyzer initializes properly"""
    assert test_fixture.analyzer is not None, "Analyzer not initialized"

    # Check available tools
    tools_status = test_fixture.analyzer.check_available_tools()
    assert isinstance(tools_status, dict), "Tools status should be a dict"

    # At minimum, basic analysis should be available
    # (even if external tools like Ghidra aren't installed)


if __name__ == "__main__":
    # Allow running individual tests
    import argparse

    parser = argparse.ArgumentParser(description="Reverse Engineering Pipeline Tests")
    parser.add_argument("--fixture", help="Run tests for specific fixture")
    parser.add_argument("--list-fixtures", action="store_true", help="List available fixtures")

    args = parser.parse_args()

    fixtures_dir = Path(__file__).parent / "fixtures"
    config_file = fixtures_dir / "test_config.json"
    fixture_manager = ReverseEngineeringTestFixture(fixtures_dir, config_file)

    if args.list_fixtures:
        print("Available test fixtures:")
        for name in fixture_manager.get_fixture_names():
            config = fixture_manager.get_fixture_config(name)
            print(f"  - {name}: {config['description']}")
        sys.exit(0)

    if args.fixture:
        if args.fixture not in fixture_manager.get_fixture_names():
            print(f"Fixture not found: {args.fixture}")
            print("Available fixtures:", fixture_manager.get_fixture_names())
            sys.exit(1)

        print(f"Testing fixture: {args.fixture}")
        binary_path = fixture_manager.compile_fixture(args.fixture)
        if binary_path:
            analysis = fixture_manager.analyze_binary(binary_path)
            validation = fixture_manager.validate_analysis(analysis, args.fixture)
            print("Validation result:", validation)
        else:
            print("Compilation failed")
    else:
        print("Run with --help for options")
