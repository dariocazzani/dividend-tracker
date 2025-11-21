#!/usr/bin/env python3
"""
Dividend Tracker - Main Entry Point
Calculates projected monthly dividend income from your portfolio.
"""

import argparse

from rich.console import Console

from .api import ensure_cache_dir
from .core import calculate_all, load_portfolio
from .ui import (
    display_dividend_projections,
    display_portfolio_header,
    display_portfolio_metrics,
    export_to_csv,
)
from .utils import setup_logging

console = Console()


def main() -> None:
    """Main function to run the dividend calculator."""
    parser = argparse.ArgumentParser(
        description="Calculate projected monthly dividend income from your portfolio."
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show only monthly totals without per-stock details",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Reduce verbosity during data fetching"
    )
    parser.add_argument(
        "--months", type=int, default=12, help="Number of months to project (default: 12)"
    )
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache and fetch fresh data")
    parser.add_argument("--export", type=str, metavar="FILE", help="Export results to CSV file")
    parser.add_argument("--no-metrics", action="store_true", help="Skip portfolio metrics display")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--compare", nargs="+", metavar="FILE", help="Compare multiple portfolio files"
    )
    parser.add_argument(
        "--save-historical", action="store_true", help="Save results to historical data"
    )
    parser.add_argument(
        "--show-history", action="store_true", help="Show historical tracking summary"
    )
    parser.add_argument(
        "--view-historical",
        type=str,
        metavar="DATE",
        help='View historical projection (YYYY-MM-DD or "latest")',
    )
    parser.add_argument(
        "--historical-trend", action="store_true", help="Show portfolio trends from historical data"
    )
    parser.add_argument(
        "--trend-days",
        type=int,
        default=90,
        help="Number of days for trend analysis (default: 90)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Handle view historical before any other processing
    if args.view_historical:
        from datetime import datetime

        from .core import display_historical_run

        if args.view_historical.lower() == "latest":
            display_historical_run("latest")
        else:
            try:
                date = datetime.strptime(args.view_historical, "%Y-%m-%d")
                display_historical_run(date)
            except ValueError:
                console.print("[red]Error: Invalid date format[/red]")
                console.print("[yellow]Use YYYY-MM-DD format or 'latest'[/yellow]")
                console.print(
                    "[dim]Example: uv run dividend-tracker --view-historical 2025-10-08[/dim]"
                )
                return

        return  # Exit after displaying historical run

    # Handle trend analysis before any other processing
    if args.historical_trend:
        from .core import display_historical_trend

        display_historical_trend(args.trend_days)
        return  # Exit after displaying trend

    # Show history if requested
    if args.show_history:
        from rich.table import Table

        from .core import get_historical_summary

        summary = get_historical_summary()

        if summary["count"] == 0:
            console.print("[yellow]No historical data found[/yellow]")
        else:
            console.print("\n[cyan]Historical Data Summary[/cyan]")
            console.print(f"Total runs: {summary['count']}")
            console.print(f"First run: {summary['first_date'].strftime('%Y-%m-%d')}")
            console.print(f"Last run: {summary['last_date'].strftime('%Y-%m-%d')}")

            # Show last 10 runs
            recent_dates = summary["dates"][-10:]

            table = Table(title="Recent Runs")
            table.add_column("Date", style="cyan")

            for date in reversed(recent_dates):
                table.add_row(date.strftime("%Y-%m-%d"))

            console.print()
            console.print(table)

        console.print()
        return  # Exit after showing history

    # Compare mode
    if args.compare:
        from .core import compare_portfolios, display_comparison

        comparison_results = compare_portfolios(
            portfolio_files=args.compare, months_ahead=args.months, use_cache=not args.no_cache
        )

        display_comparison(comparison_results)
        console.print()
        return  # Exit after comparison

    # Setup
    ensure_cache_dir()
    display_portfolio_header()

    # Load portfolio
    portfolio = load_portfolio()

    # Calculate everything
    results = calculate_all(
        portfolio=portfolio,
        months_ahead=args.months,
        verbose=not args.quiet,
        use_cache=not args.no_cache,
        show_metrics=not args.no_metrics,
    )

    # Save historical if requested
    if args.save_historical:
        from .core import check_historical_exists, save_historical
        from .core.portfolio import PORTFOLIO_FILE

        if check_historical_exists():
            console.print(
                "[yellow]Historical data for today already exists, will overwrite[/yellow]"
            )

        saved_path = save_historical(results=results, portfolio_path=PORTFOLIO_FILE)
        console.print(f"[green]✓ Saved to historical data: {saved_path}[/green]")

    # Display results
    if not args.no_metrics:
        display_portfolio_metrics(
            results["metrics"],  # type: ignore
            results["total_value"],  # type: ignore
            results["total_cost"],  # type: ignore
            results["stock_annual_dividends"],  # type: ignore
        )

    display_dividend_projections(
        results["monthly_dividends"],  # type: ignore
        results["dividend_details"],  # type: ignore
        show_details=not args.summary,
    )

    # Export if requested
    if args.export:
        export_to_csv(
            results["monthly_dividends"],  # type: ignore
            results["dividend_details"],  # type: ignore
            args.export,
        )

    console.print()


if __name__ == "__main__":
    main()
