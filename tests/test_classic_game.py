#!/usr/bin/env python3
"""
Test for Classic Game Test Fixture

This test validates the classic_game.c fixture which simulates
early Windows games like Nibbles/Ants with text-based graphics.
"""

import subprocess
from pathlib import Path

import pytest


def test_classic_game_compilation():
    """Test that the classic game fixture compiles successfully"""
    fixture_dir = Path(__file__).parent / "fixtures"
    source_file = fixture_dir / "classic_game.c"
    output_file = fixture_dir / "classic_game.exe"

    # Skip test if GCC not available
    try:
        # Try to compile
        result = subprocess.run(
            ["gcc", "-o", str(output_file), str(source_file)],
            check=False,
            capture_output=True,
            text=True,
            cwd=fixture_dir,
        )

        # Check compilation success
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"

        # Verify output file exists
        assert output_file.exists(), "Output executable not created"

        # Clean up
        if output_file.exists():
            output_file.unlink()

    except FileNotFoundError:
        pytest.skip("GCC not available for compilation testing")


def test_classic_game_strings():
    """Test that expected strings are present in the source"""
    source_file = Path(__file__).parent / "fixtures" / "classic_game.c"

    with open(source_file, encoding="utf-8") as f:
        content = f.read()

    # Test for expected strings from config
    expected_strings = [
        "Classic Snake Game",
        "Score:",
        "Snake Length:",
        "Game Over!",
        "Final Score:",
    ]

    for string in expected_strings:
        assert string in content, f"Expected string '{string}' not found in source"


def test_classic_game_functions():
    """Test that expected functions are present in the source"""
    source_file = Path(__file__).parent / "fixtures" / "classic_game.c"

    with open(source_file, encoding="utf-8") as f:
        content = f.read()

    # Test for expected functions from config
    expected_functions = [
        "main",
        "initialize_game",
        "update_game",
        "render_board",
        "check_collision",
        "place_food",
        "move_snake",
        "handle_input",
        "calculate_score_multiplier",
        "save_high_score",
        "load_high_score",
    ]

    for func in expected_functions:
        assert f"{func}(" in content, f"Expected function '{func}' not found in source"


def test_classic_game_config():
    """Test that the fixture is properly configured"""
    import json

    config_file = Path(__file__).parent / "fixtures" / "test_config.json"

    with open(config_file, encoding="utf-8") as f:
        config = json.load(f)

    # Verify classic_game.c is in config
    assert "classic_game.c" in config["fixtures"], "classic_game.c not found in test config"

    fixture_config = config["fixtures"]["classic_game.c"]

    # Verify required fields
    assert fixture_config["language"] == "c"
    assert fixture_config["compiler"] == "gcc"
    assert "expected_strings" in fixture_config
    assert "expected_functions" in fixture_config
    assert len(fixture_config["expected_functions"]) == 11  # All functions listed


if __name__ == "__main__":
    # Run basic validation
    test_classic_game_strings()
    test_classic_game_functions()
    test_classic_game_config()
    print("Classic game test fixture validation passed!")
