"""Dividend Tracker - A tool for projecting dividend income from your portfolio."""

__version__ = "0.1.0"

# Re-export shared modules for absolute imports
from dividend_tracker import constants, exceptions, types

__all__ = [
    "__version__",
    "constants",
    "exceptions",
    "types",
]
