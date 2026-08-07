#!/usr/bin/env python3
"""
Comprehensive Test Runner for Reversing MCP

This script provides extensive testing capabilities:
- Unit tests for MCP server functionality
- Integration tests for reverse engineering pipeline
- Binary fixture testing
- Performance benchmarks
- Coverage reporting
- Detailed error reporting and debugging
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class ComprehensiveTestRunner:
    """Comprehensive test runner for reversing MCP"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.start_time = None

    def run_command(self, cmd: list[str], cwd: Path | None = None, timeout: int = 300) -> dict[str, Any]:
        """Run a command and return results"""
        try:
            result = subprocess.run(
                cmd,
                check=False,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out", "command": " ".join(cmd)}
        except Exception as e:
            return {"success": False, "error": str(e), "command": " ".join(cmd)}

    def check_prerequisites(self) -> dict[str, Any]:
        """Check test prerequisites"""
        print("[INFO] Checking prerequisites...")

        results = {
            "python_version": sys.version,
            "project_structure": {},
            "dependencies": {},
            "test_fixtures": {},
        }

        # Check project structure
        required_dirs = ["src", "tests", "tests/fixtures"]
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            results["project_structure"][dir_name] = {
                "exists": dir_path.exists(),
                "path": str(dir_path),
            }

        # Check Python dependencies
        required_modules = ["fastmcp", "pydantic", "pytest"]
        for module in required_modules:
            try:
                __import__(module)
                results["dependencies"][module] = {"available": True}
            except ImportError:
                results["dependencies"][module] = {"available": False}

        # Check test fixtures
        fixtures_dir = self.project_root / "tests" / "fixtures"
        if fixtures_dir.exists():
            fixture_files = [
                "hello_world.c",
                "simple_math.c",
                "data_structures.c",
                "binaries/minimal.com",
                "binaries/hello.com",
                "binaries/loop.com",
                "binaries/packed_test.bin",
            ]

            for fixture in fixture_files:
                fixture_path = fixtures_dir / fixture
                results["test_fixtures"][fixture] = {
                    "exists": fixture_path.exists(),
                    "size": fixture_path.stat().st_size if fixture_path.exists() else 0,
                }

        return results

    def run_unit_tests(self, coverage: bool = False, verbose: bool = False) -> dict[str, Any]:
        """Run unit tests"""
        print("[INFO] Running unit tests...")

        cmd = [sys.executable, "-m", "pytest", "tests/test_mcp_server.py"]
        if coverage:
            cmd.extend(["--cov=reversing_mcp", "--cov-report=html", "--cov-report=term"])
        if verbose:
            cmd.append("-v")

        result = self.run_command(cmd)
        result["test_type"] = "unit"

        return result

    def run_integration_tests(self, verbose: bool = False) -> dict[str, Any]:
        """Run integration tests"""
        print("🔗 Running integration tests...")

        cmd = [sys.executable, "-m", "pytest", "tests/test_reverse_engineering_pipeline.py"]
        if verbose:
            cmd.append("-v")

        result = self.run_command(cmd)
        result["test_type"] = "integration"

        return result

    def run_binary_fixture_tests(self) -> dict[str, Any]:
        """Test binary fixtures existence and basic properties"""
        print("[INFO] Testing binary fixtures...")

        results = {"fixtures_tested": [], "success_count": 0, "total_count": 0}

        # Test binary fixtures existence and basic properties
        fixture_tests = [
            ("tests/fixtures/binaries/minimal.com", "minimal COM file", 2),
            ("tests/fixtures/binaries/hello.com", "hello COM file", 16),
            ("tests/fixtures/binaries/loop.com", "loop COM file", 2),
            ("tests/fixtures/binaries/packed_test.bin", "packed binary", 1024),
        ]

        for fixture_path, description, expected_size in fixture_tests:
            full_path = self.project_root / fixture_path
            if full_path.exists():
                results["total_count"] += 1
                actual_size = full_path.stat().st_size
                size_correct = actual_size == expected_size

                # Basic file validation
                readable = bool(full_path.stat().st_mode & 0o400)  # Check read permission
                file_valid = size_correct and readable

                results["fixtures_tested"].append(
                    {
                        "fixture": fixture_path,
                        "description": description,
                        "size": actual_size,
                        "expected_size": expected_size,
                        "size_correct": size_correct,
                        "readable": readable,
                        "overall_success": file_valid,
                    }
                )

                if file_valid:
                    results["success_count"] += 1
            else:
                results["fixtures_tested"].append(
                    {
                        "fixture": fixture_path,
                        "description": description,
                        "error": "Fixture file not found",
                        "overall_success": False,
                    }
                )

        return results

    def run_performance_tests(self) -> dict[str, Any]:
        """Run performance benchmarks"""
        print("[INFO] Running performance tests...")

        results = {"benchmarks": []}

        try:
            import time

            sys.path.insert(0, str(self.project_root / "src"))

            # Test MCP server import time
            start_time = time.time()
            import_time = time.time() - start_time

            results["benchmarks"].append(
                {"test": "MCP server import", "time_seconds": import_time, "status": "success"}
            )

            # Test analyzer initialization
            start_time = time.time()
            from reversing_mcp.analyzers import BinaryAnalyzer

            analyzer = BinaryAnalyzer()
            init_time = time.time() - start_time

            results["benchmarks"].append(
                {
                    "test": "BinaryAnalyzer initialization",
                    "time_seconds": init_time,
                    "status": "success",
                }
            )

            # Test tool detection
            start_time = time.time()
            tools = analyzer.check_available_tools()
            detection_time = time.time() - start_time

            results["benchmarks"].append(
                {
                    "test": "Tool detection",
                    "time_seconds": detection_time,
                    "tools_found": len(tools),
                    "status": "success",
                }
            )

        except Exception as e:
            results["benchmarks"].append({"test": "Performance testing", "error": str(e), "status": "failed"})

        return results

    def generate_report(self, all_results: dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report_lines = []

        report_lines.append("=== Comprehensive Reversing MCP Test Report ===")
        report_lines.append("=" * 60)

        # Summary
        total_tests = 0
        passed_tests = 0

        for category, results in all_results.items():
            if isinstance(results, dict):
                if "success" in results and isinstance(results["success"], bool):
                    total_tests += 1
                    if results["success"]:
                        passed_tests += 1
                elif "success_count" in results:
                    total_tests += results.get("total_count", 0)
                    passed_tests += results["success_count"]

        report_lines.append(f"[SUMMARY] Overall Results: {passed_tests}/{total_tests} tests passed")
        report_lines.append("")

        # Detailed results
        for category, results in all_results.items():
            report_lines.append(f"[SECTION] {category.replace('_', ' ').title()}")
            report_lines.append("-" * 40)

            if category == "prerequisites":
                self._report_prerequisites(report_lines, results)
            elif category == "unit_tests":
                self._report_test_results(report_lines, results, "Unit Tests")
            elif category == "integration_tests":
                self._report_test_results(report_lines, results, "Integration Tests")
            elif category == "binary_fixtures":
                self._report_binary_fixtures(report_lines, results)
            elif category == "performance":
                self._report_performance(report_lines, results)

            report_lines.append("")

        # Recommendations
        report_lines.append("[RECOMMENDATIONS]")
        report_lines.append("-" * 20)

        if not all_results.get("prerequisites", {}).get("dependencies", {}).get("fastmcp", {}).get("available"):
            report_lines.append("[WARNING] Install FastMCP: pip install fastmcp")

        if len(all_results.get("binary_fixtures", {}).get("fixtures_tested", [])) < 5:
            report_lines.append(
                "[WARNING] Create binary test fixtures: cd tests/fixtures/binaries && python create_test_binaries.py"
            )

        if not any(
            tool.get("available", False)
            for tool in all_results.get("prerequisites", {}).get("test_fixtures", {}).values()
        ):
            report_lines.append(
                "[WARNING] Ghidra not detected - install Ghidra and ReVa MCP for decompilation workflows"
            )

        report_lines.append("")
        report_lines.append("[SUCCESS] Report generated successfully")

        return "\n".join(report_lines)

    def _report_prerequisites(self, lines: list[str], results: dict[str, Any]):
        """Report prerequisites check results"""
        for category, items in results.items():
            if category == "python_version":
                lines.append(f"[PYTHON] Python: {items}")
            elif isinstance(items, dict):
                for item, status in items.items():
                    if isinstance(status, dict):
                        if "available" in status:
                            status_icon = "[OK]" if status["available"] else "[FAIL]"
                            lines.append(f"{status_icon} {item}: {status}")
                        elif "exists" in status:
                            status_icon = "[OK]" if status["exists"] else "[MISSING]"
                            size_info = f" ({status.get('size', 0)} bytes)" if "size" in status else ""
                            lines.append(f"{status_icon} {item}: {status['exists']}{size_info}")

    def _report_test_results(self, lines: list[str], results: dict[str, Any], title: str):
        """Report test execution results"""
        if results.get("success"):
            lines.append(f"[PASS] {title}: PASSED")
            if results.get("stdout"):
                # Count passed tests from output
                output_lines = results["stdout"].split("\n")
                for line in output_lines[-10:]:  # Last 10 lines
                    if "passed" in line.lower() or "failed" in line.lower():
                        lines.append(f"   {line.strip()}")
        else:
            lines.append(f"[FAIL] {title}: FAILED")
            if results.get("stderr"):
                lines.append(f"   Error: {results['stderr'][:200]}...")

    def _report_binary_fixtures(self, lines: list[str], results: dict[str, Any]):
        """Report binary fixture test results"""
        tested = results.get("fixtures_tested", [])
        success_count = results.get("success_count", 0)
        total_count = results.get("total_count", 0)

        lines.append(f"📁 Binary Fixtures: {success_count}/{total_count} passed")

        for fixture in tested:
            status_icon = "[PASS]" if fixture.get("overall_success") else "[FAIL]"
            lines.append(f"{status_icon} {fixture['fixture']} ({fixture.get('size', 0)} bytes)")

            if not fixture.get("overall_success"):
                if "error" in fixture:
                    lines.append(f"   Error: {fixture['error']}")
                else:
                    failed_tests = []
                    if not fixture.get("analysis_success", True):
                        failed_tests.append("analysis")
                    if not fixture.get("strings_success", True):
                        failed_tests.append("strings")
                    if not fixture.get("hexdump_success", True):
                        failed_tests.append("hexdump")
                    if failed_tests:
                        lines.append(f"   Failed: {', '.join(failed_tests)}")

    def _report_performance(self, lines: list[str], results: dict[str, Any]):
        """Report performance test results"""
        for benchmark in results.get("benchmarks", []):
            status_icon = "[OK]" if benchmark.get("status") == "success" else "[ERROR]"
            time_str = ".3f"
            extra_info = ""
            if "tools_found" in benchmark:
                extra_info = f" ({benchmark['tools_found']} tools)"
            elif "error" in benchmark:
                extra_info = f" - {benchmark['error']}"

            lines.append(f"{status_icon} {benchmark['test']}: {time_str}{extra_info}")

    def run_all_tests(self, coverage: bool = False, verbose: bool = False) -> dict[str, Any]:
        """Run all comprehensive tests"""
        print("[START] Starting Comprehensive Reversing MCP Test Suite")
        print("=" * 60)

        self.start_time = time.time()
        all_results = {}

        try:
            # Prerequisites check
            all_results["prerequisites"] = self.check_prerequisites()

            # Unit tests
            all_results["unit_tests"] = self.run_unit_tests(coverage, verbose)

            # Integration tests
            all_results["integration_tests"] = self.run_integration_tests(verbose)

            # Binary fixture tests
            all_results["binary_fixtures"] = self.run_binary_fixture_tests()

            # Performance tests
            all_results["performance"] = self.run_performance_tests()

        except Exception as e:
            all_results["error"] = str(e)
            print(f"[ERROR] Test suite failed: {e}")

        # Generate report
        total_time = time.time() - self.start_time
        report = self.generate_report(all_results)

        print("\n" + report)
        print(".2f")
        # Save detailed results
        results_file = self.project_root / "test_results.json"
        with open(results_file, "w") as f:
            json.dump(
                {"timestamp": time.time(), "duration_seconds": total_time, "results": all_results},
                f,
                indent=2,
            )

        print(f"[SAVE] Detailed results saved to: {results_file}")

        return all_results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive Reversing MCP Test Runner")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--fixtures-only", action="store_true", help="Run only binary fixture tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")

    args = parser.parse_args()

    runner = ComprehensiveTestRunner()

    if args.unit_only:
        result = runner.run_unit_tests(args.coverage, args.verbose)
        print(json.dumps(result, indent=2))
    elif args.integration_only:
        result = runner.run_integration_tests(args.verbose)
        print(json.dumps(result, indent=2))
    elif args.fixtures_only:
        result = runner.run_binary_fixture_tests()
        print(json.dumps(result, indent=2))
    elif args.performance_only:
        result = runner.run_performance_tests()
        print(json.dumps(result, indent=2))
    else:
        # Run all tests
        runner.run_all_tests(args.coverage, args.verbose)


if __name__ == "__main__":
    main()
