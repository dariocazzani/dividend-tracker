"""
Portfolio management module.
Handles loading portfolio from CSV file.
"""

import csv
import sys
from pathlib import Path

from rich.console import Console

from ..utils import get_logger

logger = get_logger("core.portfolio")
console = Console()  # Keep for user-facing error messages

PORTFOLIO_FILE = "data/portfolio.csv"

Portfolio = dict[str, dict[str, float | None]]


def parse_number(value: str) -> float:
    """
    Parse a number string that may contain commas as thousands separators.
    Examples: "1,234.56" -> 1234.56, "1234.56" -> 1234.56
    """
    return float(value.replace(",", ""))


def load_portfolio(portfolio_path: str | Path | None = None) -> Portfolio:
    """
    Load portfolio from CSV file.
    Expects columns: symbol, shares, cost_basis
    Exits if file doesn't exist.

    Args:
        portfolio_path: Optional custom path to portfolio file

    Returns:
        Dictionary mapping symbol to {shares, cost_basis}
    """
    path = Path(portfolio_path) if portfolio_path else Path(PORTFOLIO_FILE)

    if not path.exists():
        console.print(f"[red]Error: Portfolio file '{path}' not found![/red]")
        console.print(
            "\n[yellow]Please create a portfolio.csv file with the following format:[/yellow]"
        )
        console.print("symbol,shares,cost_basis")
        console.print("AAPL,50,150.00")
        console.print("MSFT,30,280.00")
        console.print("KO,100,55.00")
        console.print("\n[cyan]Note: cost_basis is optional (average cost per share)[/cyan]")
        sys.exit(1)

    portfolio: Portfolio = {}

    try:
        with open(path) as f:
            reader = csv.DictReader(f)

            # Validate headers
            if (
                not reader.fieldnames
                or "symbol" not in reader.fieldnames
                or "shares" not in reader.fieldnames
            ):
                console.print("[red]Error: CSV must have 'symbol' and 'shares' columns[/red]")
                sys.exit(1)

            for row in reader:
                symbol = row["symbol"].strip().upper()

                if not symbol:
                    continue

                try:
                    shares = parse_number(row["shares"])
                except ValueError:
                    logger.warning(f"Invalid shares value for {symbol}, skipping")
                    continue

                # Parse cost basis (optional)
                cost_basis: float | None = None
                if "cost_basis" in row and row["cost_basis"].strip():
                    try:
                        cost_basis = parse_number(row["cost_basis"])
                    except ValueError:
                        logger.warning(f"Invalid cost_basis for {symbol}")

                portfolio[symbol] = {"shares": shares, "cost_basis": cost_basis}

        if not portfolio:
            console.print(f"[red]Error: No valid entries found in {path}[/red]")
            sys.exit(1)

        logger.info(f"Loaded {len(portfolio)} positions from {path}")
        console.print(f"[green]✓ Loaded {len(portfolio)} positions from {path}[/green]")
        return portfolio

    except Exception as e:
        console.print(f"[red]Error reading portfolio file: {e}[/red]")
        logger.error(f"Failed to load portfolio: {e}")
        sys.exit(1)
