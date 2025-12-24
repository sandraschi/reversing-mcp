#!/usr/bin/env python3
"""
Test Runner for Reverse Engineering Pipeline Tests

This script provides an easy way to run the reverse engineering tests
with proper setup and reporting.
"""

import sys
import subprocess
import os
from pathlib import Path


def install_test_deps():
    """Install test dependencies if not already installed"""
    try:
        import pytest
        print("✓ pytest already installed")
    except ImportError:
        print("Installing test dependencies...")
        requirements_file = Path(__file__).parent.parent / "requirements-dev.txt"
        if requirements_file.exists():
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"])


def run_tests(args=None):
    """Run the test suite"""
    if args is None:
        args = []

    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Add src and tests to Python path
    sys.path.insert(0, str(project_root / "src"))
    sys.path.insert(0, str(project_root / "tests"))

    # Run pytest
    cmd = [sys.executable, "-m", "pytest"] + args
    print(f"Running: {' '.join(cmd)}")
    return subprocess.call(cmd)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Reverse Engineering Test Runner")
    parser.add_argument("--install-deps", action="store_true",
                       help="Install test dependencies first")
    parser.add_argument("--fixtures", action="store_true",
                       help="List available test fixtures")
    parser.add_argument("--compile-only", action="store_true",
                       help="Only test compilation, skip analysis")
    parser.add_argument("--fixture", help="Run tests for specific fixture")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--coverage", action="store_true",
                       help="Run with coverage reporting")

    args, unknown = parser.parse_known_args()

    if args.install_deps:
        install_test_deps()

    # Build pytest arguments
    pytest_args = []

    if args.verbose:
        pytest_args.append("-v")

    if args.coverage:
        pytest_args.extend(["--cov=reversing_mcp", "--cov-report=html", "--cov-report=term"])

    if args.fixture:
        pytest_args.extend(["-k", args.fixture])

    if args.compile_only:
        pytest_args.extend(["-m", "compilation"])

    # Add any unknown args
    pytest_args.extend(unknown)

    if args.fixtures:
        # List fixtures instead of running tests
        from test_reverse_engineering_pipeline import ReverseEngineeringTestFixture
        from pathlib import Path

        fixtures_dir = Path(__file__).parent / "fixtures"
        config_file = fixtures_dir / "test_config.json"
        fixture_manager = ReverseEngineeringTestFixture(fixtures_dir, config_file)

        print("Available test fixtures:")
        print("=" * 50)
        for name in fixture_manager.get_fixture_names():
            config = fixture_manager.get_fixture_config(name)
            print("30")
        return 0

    # Run the tests
    return run_tests(pytest_args)


if __name__ == "__main__":
    sys.exit(main())
