"""
Calculator module.
Contains all dividend projection and portfolio metric calculations.
"""

from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd
from rich.console import Console

from ..api import get_current_price, get_dividend_data
from ..utils import get_logger

logger = get_logger("core.calculator")
console = Console()  # Keep for user-facing progress messages

DividendDetail = dict[str, datetime | str | float]
MonthlyDividends = dict[str, float]
StockMetrics = dict[str, dict[str, float | None]]
CalculationResults = dict[
    str, MonthlyDividends | list[DividendDetail] | dict[str, float] | StockMetrics | float
]


def estimate_future_dividends(
    dividends: pd.Series, months_ahead: int = 12
) -> list[tuple[datetime, float]]:
    """
    Estimate future dividend payments based on historical pattern.

    Args:
        dividends: Historical dividend data
        months_ahead: Number of months to project

    Returns:
        List of (date, amount) tuples for future dividends
    """
    if dividends is None or len(dividends) < 2:
        return []

    # Convert to sorted list
    div_list: list[tuple[datetime, float]] = []
    for date, amount in dividends.items():
        if hasattr(date, "to_pydatetime"):
            dt: datetime = date.to_pydatetime()  # type: ignore[union-attr]
        else:
            dt = date  # type: ignore[assignment]
        div_list.append((dt, float(amount)))
    div_list.sort(key=lambda x: x[0])

    # Calculate average interval between dividends
    intervals = [
        (div_list[-i][0] - div_list[-i - 1][0]).days for i in range(1, min(5, len(div_list)))
    ]

    if not intervals:
        return []

    avg_interval = sum(intervals) / len(intervals)

    # Determine frequency
    if avg_interval < 40:
        frequency = "monthly"
    elif avg_interval < 100:
        frequency = "quarterly"
    elif avg_interval < 200:
        frequency = "semi-annual"
    else:
        frequency = "annual"

    logger.debug(f"Dividend frequency: {frequency} (avg {avg_interval:.0f} days)")
    console.print(f"  [dim]Frequency: {frequency} (avg {avg_interval:.0f} days)[/dim]")

    # Project future dividends
    last_date, last_amount = div_list[-1]
    future_dividends: list[tuple[datetime, float]] = []
    current_date = datetime.now()
    projection_end = current_date + timedelta(days=30 * months_ahead)

    next_date = last_date + timedelta(days=avg_interval)
    while next_date <= projection_end and len(future_dividends) < 20:
        if next_date > current_date:
            future_dividends.append((next_date, last_amount))
        next_date += timedelta(days=avg_interval)

    return future_dividends


def calculate_dividends(
    portfolio: dict[str, dict[str, float | None]],
    months_ahead: int = 12,
    verbose: bool = True,
    use_cache: bool = True,
) -> tuple[MonthlyDividends, list[DividendDetail], dict[str, float]]:
    """
    Calculate monthly dividend projections.

    Args:
        portfolio: Portfolio dictionary {symbol: {shares, cost_basis}}
        months_ahead: Number of months to project
        verbose: Whether to show progress messages
        use_cache: Whether to use cached data

    Returns:
        Tuple of (monthly_totals, dividend_details, stock_annual_dividends)
    """
    monthly_totals: defaultdict[str, float] = defaultdict(float)
    dividend_details: list[DividendDetail] = []
    stock_annual_dividends: dict[str, float] = {}

    for symbol, data in portfolio.items():
        shares = data["shares"]
        if shares is None:
            continue

        if verbose:
            console.print(f"\n[cyan]Fetching {symbol}...[/cyan]")

        logger.info(f"Processing {symbol}")

        dividends = get_dividend_data(symbol, use_cache=use_cache)
        if dividends is None or dividends.empty:
            continue

        if verbose:
            console.print(f"  [green]Found {len(dividends)} historical payments[/green]")

        future_dividends = estimate_future_dividends(dividends, months_ahead)

        if verbose:
            console.print(f"  [green]Projected {len(future_dividends)} future payments[/green]")

        # Calculate annual dividend
        annual_div = sum(amount * shares for _, amount in future_dividends)
        stock_annual_dividends[symbol] = annual_div
        logger.debug(f"{symbol} annual dividend: ${annual_div:.2f}")

        # Aggregate by month
        for div_date, div_amount in future_dividends:
            month_key = div_date.strftime("%B %Y")
            total = div_amount * shares
            monthly_totals[month_key] += total

            dividend_details.append(
                {
                    "symbol": symbol,
                    "date": div_date,
                    "amount_per_share": div_amount,
                    "shares": shares,
                    "total": total,
                }
            )

    return dict(monthly_totals), dividend_details, stock_annual_dividends


def calculate_metrics(
    portfolio: dict[str, dict[str, float | None]],
) -> tuple[StockMetrics, float, float]:
    """
    Calculate portfolio value and metrics.

    Args:
        portfolio: Portfolio dictionary

    Returns:
        Tuple of (metrics_dict, total_value, total_cost)
    """
    metrics: StockMetrics = {}
    total_value = 0.0
    total_cost = 0.0

    for symbol, data in portfolio.items():
        shares = data["shares"]
        cost_basis_per_share = data["cost_basis"]

        if shares is None:
            continue

        current_price = get_current_price(symbol)

        if current_price:
            current_value = shares * current_price
            total_value += current_value

            if cost_basis_per_share:
                cost_basis = shares * cost_basis_per_share
                total_cost += cost_basis
                gain_loss = current_value - cost_basis
                gain_loss_pct = (gain_loss / cost_basis) * 100 if cost_basis > 0 else 0
            else:
                cost_basis = None
                gain_loss = None
                gain_loss_pct = None

            metrics[symbol] = {
                "shares": shares,
                "current_price": current_price,
                "current_value": current_value,
                "cost_basis": cost_basis,
                "gain_loss": gain_loss,
                "gain_loss_pct": gain_loss_pct,
            }

            logger.debug(f"{symbol}: {shares} shares @ ${current_price:.2f} = ${current_value:.2f}")

    return metrics, total_value, total_cost


def calculate_all(
    portfolio: dict[str, dict[str, float | None]],
    months_ahead: int = 12,
    verbose: bool = True,
    use_cache: bool = True,
    show_metrics: bool = True,
) -> CalculationResults:
    """
    Run all calculations and return results.

    Args:
        portfolio: Portfolio dictionary
        months_ahead: Number of months to project
        verbose: Whether to show progress messages
        use_cache: Whether to use cached data
        show_metrics: Whether to calculate portfolio metrics

    Returns:
        Dictionary containing all calculation results
    """
    results: CalculationResults = {}

    logger.info("Starting dividend calculations")

    # Calculate dividends
    monthly_divs, div_details, stock_annual = calculate_dividends(
        portfolio, months_ahead, verbose, use_cache
    )

    results["monthly_dividends"] = monthly_divs
    results["dividend_details"] = div_details
    results["stock_annual_dividends"] = stock_annual

    # Calculate metrics if requested
    if show_metrics:
        logger.info("Calculating portfolio metrics")
        with console.status("[cyan]Calculating portfolio metrics...[/cyan]"):
            metrics, total_value, total_cost = calculate_metrics(portfolio)

        results["metrics"] = metrics
        results["total_value"] = total_value
        results["total_cost"] = total_cost

    return results
