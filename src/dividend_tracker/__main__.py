#!/usr/bin/env python3
"""Dividend Tracker - Main Entry Point."""

import argparse
import sys

from rich.console import Console

from dividend_tracker.api import ensure_cache_dir
from dividend_tracker.constants import DEFAULT_PORTFOLIO_FILE
from dividend_tracker.core import (
    calculate_all,
    check_historical_exists,
    load_portfolio,
    save_historical,
)
from dividend_tracker.exceptions import PortfolioError, PortfolioFileNotFoundError
from dividend_tracker.ui import display_dashboard, get_previous_run_data
from dividend_tracker.utils import setup_logging

console = Console()


def _handle_portfolio_error(error: PortfolioError) -> None:
    """Display helpful message for portfolio errors."""
    console.print(f"[red]Error: {error}[/red]")

    if isinstance(error, PortfolioFileNotFoundError):
        console.print("\n[yellow]Create a portfolio.csv file with this format:[/yellow]")
        console.print("symbol,shares,cost_basis")
        console.print("AAPL,50,150.00")
        console.print("VTI,100,200.00")
        console.print("\n[dim]cost_basis is optional[/dim]")


def main() -> None:
    """Main function to run the dividend tracker."""
    parser = argparse.ArgumentParser(
        description="Track your portfolio dividends and value over time."
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to historical data",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache and fetch fresh dividend data",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch live prices from Yahoo instead of using Fidelity export values",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    ensure_cache_dir()

    try:
        portfolio = load_portfolio()
    except PortfolioError as e:
        _handle_portfolio_error(e)
        sys.exit(1)

    # Get previous run data for comparison
    previous_data = get_previous_run_data()

    # Calculate current state
    status_msg = "[cyan]Fetching live prices...[/cyan]" if args.live else "[cyan]Loading...[/cyan]"
    with console.status(status_msg):
        results = calculate_all(
            portfolio=portfolio,
            months_ahead=12,
            use_cache=not args.no_cache,
            show_metrics=True,
            live_prices=args.live,
        )

    # Save historical data by default
    if not args.no_save:
        if check_historical_exists():
            console.print("[dim]Updating today's historical data...[/dim]")
        save_historical(results=dict(results), portfolio_path=DEFAULT_PORTFOLIO_FILE)

    # Display the dashboard
    display_dashboard(results, previous_data)  # type: ignore[arg-type]

    console.print()


if __name__ == "__main__":
    main()
