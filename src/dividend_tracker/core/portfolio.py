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


def parse_number(value: str) -> float | None:
    """Parse a number string that may contain $, commas, or be n/a."""
    cleaned = value.strip().replace(",", "").replace("$", "")
    if not cleaned or cleaned.lower() in ("n/a", "--", ""):
        return None
    return float(cleaned)


def _detect_format(fieldnames: list[str]) -> str:
    """Detect CSV format based on column names."""
    # Normalize fieldnames (remove BOM, whitespace)
    normalized = [f.strip().lstrip("\ufeff") for f in fieldnames]

    # Fidelity export format
    if "Symbol" in normalized and "Quantity" in normalized:
        return "fidelity"
    # Simple format (symbol, shares, cost_basis)
    if "symbol" in normalized and "shares" in normalized:
        return "simple"
    return "unknown"


def _load_fidelity_format(reader: csv.DictReader) -> Portfolio:  # type: ignore[type-arg]
    """Load portfolio from Fidelity export CSV with full position data."""
    portfolio: Portfolio = {}

    for row in reader:
        # Handle None values and empty rows
        if not row or all(v is None for v in row.values()):
            continue

        symbol = (row.get("Symbol") or "").strip()
        if not symbol:
            continue

        # Skip summary/pending rows
        if symbol.lower() in ("pending activity",) or symbol.startswith('"'):
            continue

        # Clean up symbol (remove ** suffix for money market)
        symbol = symbol.rstrip("*")
        symbol = extract_ticker(symbol)

        # Get quantity - for money market (SPAXX), use Current Value as shares
        quantity_str = row.get("Quantity") or ""
        shares = parse_number(quantity_str)

        # Money market funds: use Current Value as shares (price is ~$1)
        current_value = parse_number(row.get("Current Value") or "")
        if shares is None:
            shares = current_value

        if shares is None:
            logger.warning(f"No quantity for {symbol}, skipping")
            continue

        # Extract all available Fidelity data
        current_price = parse_number(row.get("Last Price") or "")
        cost_basis = parse_number(row.get("Average Cost Basis") or "")
        cost_basis_total = parse_number(row.get("Cost Basis Total") or "")

        portfolio[symbol] = {
            "shares": shares,
            "cost_basis": cost_basis,
            "current_price": current_price,
            "current_value": current_value,
            "cost_basis_total": cost_basis_total,
        }

    return portfolio


def _load_simple_format(reader: csv.DictReader) -> Portfolio:  # type: ignore[type-arg]
    """Load portfolio from simple CSV format (symbol, shares, cost_basis)."""
    portfolio: Portfolio = {}

    for row in reader:
        raw_symbol = row["symbol"].strip()
        if not raw_symbol:
            continue

        symbol = extract_ticker(raw_symbol)

        shares = parse_number(row["shares"])
        if shares is None:
            logger.warning(f"Invalid shares value for {symbol}, skipping")
            continue

        cost_basis: float | None = None
        if "cost_basis" in row and row["cost_basis"].strip():
            cost_basis = parse_number(row["cost_basis"])

        portfolio[symbol] = {"shares": shares, "cost_basis": cost_basis}

    return portfolio


def load_portfolio(portfolio_path: str | Path | None = None) -> Portfolio:
    """
    Load portfolio from CSV file.

    Supports two formats:
    1. Fidelity export (Symbol, Quantity, Average Cost Basis, ...)
    2. Simple format (symbol, shares, cost_basis)

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

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])

        fmt = _detect_format(fieldnames)

        if fmt == "fidelity":
            logger.info("Detected Fidelity export format")
            portfolio = _load_fidelity_format(reader)
        elif fmt == "simple":
            portfolio = _load_simple_format(reader)
        else:
            raise PortfolioInvalidFormatError(
                "CSV must have either 'Symbol'+'Quantity' (Fidelity) or 'symbol'+'shares' columns"
            )

    if not portfolio:
        raise PortfolioEmptyError(str(path))

    logger.info(f"Loaded {len(portfolio)} positions from {path}")
    return portfolio
