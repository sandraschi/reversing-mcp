#!/usr/bin/env python3
"""
MCP Server Functionality Tests

This test suite validates the MCP server tools and functionality:
- Tool registration and availability
- Binary analysis tools
- Ghidra integration
- Help system
- Error handling
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reversing_mcp.analyzers import BinaryAnalyzer
from reversing_mcp.server import mcp


class TestBinaryAnalysis:
    """Test binary analysis functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = BinaryAnalyzer()

    def test_analyzer_initialization(self):
        """Test BinaryAnalyzer initializes correctly"""
        assert self.analyzer is not None
        assert hasattr(self.analyzer, "check_available_tools")
        assert hasattr(self.analyzer, "analyze_file")

    def test_detect_file_type_pe(self):
        """Test PE file detection"""
        # Create a minimal PE-like file
        dos_header = b"MZ" + b"\x00" * 58 + b"\x80\x00\x00\x00"  # MZ + padding + PE offset
        pe_header = b"PE\x00\x00" + b"\x00" * 20  # PE signature + basic header

        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe", mode="wb") as f:
            f.write(dos_header + pe_header)
            temp_path = f.name

        try:
            file_type = self.analyzer.detect_file_type(temp_path)
            # On Windows without 'file' command, it should detect by extension
            assert "PE executable" in file_type
        finally:
            os.unlink(temp_path)

    def test_entropy_calculation(self):
        """Test entropy calculation"""
        # Low entropy data (repeated)
        low_entropy = b"A" * 1000
        entropy = self.analyzer._calculate_entropy(low_entropy)
        assert entropy < 0.1  # Very low entropy

        # High entropy data (random-like)
        high_entropy = bytes(range(256)) * 4  # 0-255 repeated
        entropy = self.analyzer._calculate_entropy(high_entropy)
        assert entropy > 7.0  # High entropy

    def test_hexdump_generation(self):
        """Test hexdump generation"""
        test_data = b"\x00\x01\x02\x03\x04\x05\x10\x20\x30\x40\x50\x60"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_data)
            temp_path = f.name

        try:
            hexdump = self.analyzer.get_hexdump(temp_path, 0, 12)
            assert isinstance(hexdump, str)
            assert len(hexdump) > 0
            # Should contain hex representation
            assert "00 01 02 03" in hexdump
        finally:
            os.unlink(temp_path)


class TestGhidraIntegration:
    """Test Ghidra integration functionality"""

    def test_ghidra_placeholder_methods(self):
        """Test that Ghidra methods return appropriate placeholders when not available"""
        analyzer = BinaryAnalyzer()

        # Mock tools cache to simulate Ghidra not available
        analyzer.tools_cache = {"ghidra": {"available": False}}

        result = analyzer._analyze_with_ghidra("/fake/path")
        assert "error" in result
        assert not result.get("available", True)

        # Test function finding placeholder
        result = analyzer._find_functions_ghidra("/fake/path")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "note" in result[0] or "error" in result[0]


class TestMCPServerBasic:
    """Test basic MCP server functionality"""

    def test_mcp_server_initialization(self):
        """Test that MCP server initializes correctly"""
        assert mcp is not None
        assert getattr(mcp, "name", None) == "ReversingMCP"
        assert callable(mcp.get_tool)


if __name__ == "__main__":
    pytest.main([__file__])
