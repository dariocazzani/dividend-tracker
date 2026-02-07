"""Portfolio management module. Handles loading portfolio from CSV file."""

import csv
import re
from pathlib import Path

from dividend_tracker.constants import DEFAULT_PORTFOLIO_FILE
from dividend_tracker.exceptions import (
    PortfolioEmptyError,
    PortfolioFileNotFoundError,
    PortfolioInvalidFormatError,
)
from dividend_tracker.types import Portfolio
from dividend_tracker.utils import get_logger

logger = get_logger("core.portfolio")

# Pattern to extract ticker from formats like "(XNAS:VXUS)" or "(ARCX:VTI)"
TICKER_PATTERN = re.compile(r"\(([A-Z]+):([A-Z]+)\)")


def extract_ticker(raw_symbol: str) -> str:
    """
    Extract ticker symbol from raw input.

    Handles formats like:
    - "VANGUARD TOT I S;ETF (XNAS:VXUS)" → "VXUS"
    - "AAPL" → "AAPL"
    - "Apple Inc (NASDAQ:AAPL)" → "AAPL"

    Args:
        raw_symbol: Raw symbol string from CSV

    Returns:
        Clean ticker symbol
    """
    match = TICKER_PATTERN.search(raw_symbol)
    if match:
        return match.group(2)
    return raw_symbol.strip().upper()


def parse_number(value: str) -> float:
    """Parse a number string that may contain commas as thousands separators."""
    return float(value.replace(",", ""))


def load_portfolio(portfolio_path: str | Path | None = None) -> Portfolio:
    """
    Load portfolio from CSV file.

    Args:
        portfolio_path: Optional custom path to portfolio file

    Returns:
        Dictionary mapping symbol to {shares, cost_basis}

    Raises:
        PortfolioFileNotFoundError: If file doesn't exist
        PortfolioInvalidFormatError: If CSV format is invalid
        PortfolioEmptyError: If no valid entries found
    """
    path = Path(portfolio_path) if portfolio_path else DEFAULT_PORTFOLIO_FILE

    if not path.exists():
        raise PortfolioFileNotFoundError(str(path))

    portfolio: Portfolio = {}

    with open(path) as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames or "symbol" not in reader.fieldnames:
            raise PortfolioInvalidFormatError("CSV must have 'symbol' column")
        if "shares" not in reader.fieldnames:
            raise PortfolioInvalidFormatError("CSV must have 'shares' column")

        for row in reader:
            raw_symbol = row["symbol"].strip()
            if not raw_symbol:
                continue

            symbol = extract_ticker(raw_symbol)

            try:
                shares = parse_number(row["shares"])
            except ValueError:
                logger.warning(f"Invalid shares value for {symbol}, skipping")
                continue

            cost_basis: float | None = None
            if "cost_basis" in row and row["cost_basis"].strip():
                try:
                    cost_basis = parse_number(row["cost_basis"])
                except ValueError:
                    logger.warning(f"Invalid cost_basis for {symbol}")

            portfolio[symbol] = {"shares": shares, "cost_basis": cost_basis}

    if not portfolio:
        raise PortfolioEmptyError(str(path))

    logger.info(f"Loaded {len(portfolio)} positions from {path}")
    return portfolio
