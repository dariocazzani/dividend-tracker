"""API module for fetching dividend data."""

from .dividend_api import (
    ensure_cache_dir,
    get_dividend_data,
    get_current_price,
)

__all__ = [
    'ensure_cache_dir',
    'get_dividend_data',
    'get_current_price',
]
