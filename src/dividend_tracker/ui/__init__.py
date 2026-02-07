"""UI module for display functionality."""

from dividend_tracker.ui.dashboard import display_dashboard, get_previous_run_data
from dividend_tracker.ui.display import (
    display_dividend_projections,
    display_portfolio_header,
    display_portfolio_metrics,
)
from dividend_tracker.ui.historical_display import (
    display_historical_run,
    display_historical_trend,
)
from dividend_tracker.ui.summary_panel import render_portfolio_summary_panel

__all__ = [
    "display_dashboard",
    "display_dividend_projections",
    "display_historical_run",
    "display_historical_trend",
    "display_portfolio_header",
    "display_portfolio_metrics",
    "get_previous_run_data",
    "render_portfolio_summary_panel",
]
