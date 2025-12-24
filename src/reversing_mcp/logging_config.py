"""
Logging configuration for IDA Pro MCP
"""

import logging
import sys
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""

    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger

