"""
Logging configuration for reversing-mcp.

Log records go to stderr: stdout is reserved for JSON-RPC in stdio transport
(MCP clients such as opencode parse stdout strictly; log lines there corrupt
the stream and surface as Internal Server Error notifications).
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""

    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Console handler (stderr - never stdout: stdio transport owns stdout)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)

        # Format
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger
