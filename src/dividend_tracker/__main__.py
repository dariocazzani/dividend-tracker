#!/usr/bin/env python3
"""
Dividend Tracker - Main Entry Point
Calculates projected monthly dividend income from your portfolio.
"""

import argparse
from rich.console import Console

from .core import load_portfolio, calculate_all
from .api import ensure_cache_dir
from .ui import display_portfolio_header, display_portfolio_metrics, display_dividend_projections, export_to_csv

console = Console()

def main():
    """Main function to run the dividend calculator."""
    parser = argparse.ArgumentParser(
        description='Calculate projected monthly dividend income from your portfolio.'
    )
    parser.add_argument('--summary', action='store_true',
                        help='Show only monthly totals without per-stock details')
    parser.add_argument('--quiet', action='store_true',
                        help='Reduce verbosity during data fetching')
    parser.add_argument('--months', type=int, default=12,
                        help='Number of months to project (default: 12)')
    parser.add_argument('--no-cache', action='store_true',
                        help='Bypass cache and fetch fresh data')
    parser.add_argument('--export', type=str, metavar='FILE',
                        help='Export results to CSV file')
    parser.add_argument('--no-metrics', action='store_true',
                        help='Skip portfolio metrics display')

    args = parser.parse_args()

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
        show_metrics=not args.no_metrics
    )

    # Display results
    if not args.no_metrics:
        display_portfolio_metrics(
            results['metrics'],
            results['total_value'],
            results['total_cost'],
            results['stock_annual_dividends']
        )

    display_dividend_projections(
        results['monthly_dividends'],
        results['dividend_details'],
        show_details=not args.summary
    )

    # Export if requested
    if args.export:
        export_to_csv(
            results['monthly_dividends'],
            results['dividend_details'],
            args.export
        )

    console.print()

if __name__ == "__main__":
    main()
