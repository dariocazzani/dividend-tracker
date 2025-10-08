"""Core business logic for dividend calculations and portfolio management."""

from .calculator import (
    calculate_all,
    calculate_dividends,
    calculate_metrics,
    estimate_future_dividends,
)
from .comparison import compare_portfolios, display_comparison
from .historical import (
    check_historical_exists,
    get_historical_summary,
    list_historical_dates,
    load_historical,
    save_historical,
)
from .portfolio import load_portfolio

__all__ = [
    "calculate_all",
    "calculate_dividends",
    "calculate_metrics",
    "estimate_future_dividends",
    "load_portfolio",
    "compare_portfolios",
    "display_comparison",
    "save_historical",
    "load_historical",
    "check_historical_exists",
    "list_historical_dates",
    "get_historical_summary",
]
