"""Core business logic for dividend calculations and portfolio management."""

from dividend_tracker.core.calculator import (
    calculate_all,
    calculate_dividends,
    calculate_metrics,
    estimate_future_dividends,
)
from dividend_tracker.core.historical_storage import (
    check_historical_exists,
    get_historical_summary,
    list_historical_dates,
    load_historical,
    save_historical,
)
from dividend_tracker.core.portfolio import load_portfolio

__all__ = [
    "calculate_all",
    "calculate_dividends",
    "calculate_metrics",
    "estimate_future_dividends",
    "load_portfolio",
    "save_historical",
    "load_historical",
    "check_historical_exists",
    "list_historical_dates",
    "get_historical_summary",
]
