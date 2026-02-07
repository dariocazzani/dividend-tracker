"""Calculator module. Contains all dividend projection and portfolio metric calculations."""

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta

import pandas as pd

from dividend_tracker.api import get_current_price, get_dividend_data, get_yield_rate
from dividend_tracker.constants import (
    MAX_PROJECTED_DIVIDENDS,
    MONTHLY_INTERVAL_MAX,
    QUARTERLY_INTERVAL_MAX,
    SEMI_ANNUAL_INTERVAL_MAX,
)
from dividend_tracker.types import (
    CalculationResults,
    DividendDetail,
    MonthlyDividends,
    Portfolio,
    StockMetrics,
)
from dividend_tracker.utils import get_logger

logger = get_logger("core.calculator")


def _detect_frequency(avg_interval: float) -> str:
    """Determine dividend payment frequency from average interval in days."""
    if avg_interval < MONTHLY_INTERVAL_MAX:
        return "monthly"
    if avg_interval < QUARTERLY_INTERVAL_MAX:
        return "quarterly"
    if avg_interval < SEMI_ANNUAL_INTERVAL_MAX:
        return "semi-annual"
    return "annual"


def estimate_future_dividends(
    dividends: pd.Series,  # type: ignore[type-arg]
    months_ahead: int = 12,
) -> tuple[list[tuple[datetime, float]], str, float]:
    """
    Estimate future dividend payments based on historical pattern.

    Args:
        dividends: Historical dividend data
        months_ahead: Number of months to project

    Returns:
        Tuple of (future_dividends, frequency, avg_interval)
    """
    if dividends is None or len(dividends) < 2:
        return [], "unknown", 0.0

    div_list: list[tuple[datetime, float]] = []
    for idx, amount in zip(dividends.index, dividends.values, strict=False):
        dt = pd.Timestamp(idx).to_pydatetime()
        div_list.append((dt, float(amount)))
    div_list.sort(key=lambda x: x[0])

    intervals = [
        (div_list[-i][0] - div_list[-i - 1][0]).days for i in range(1, min(5, len(div_list)))
    ]

    if not intervals:
        return [], "unknown", 0.0

    avg_interval = sum(intervals) / len(intervals)
    frequency = _detect_frequency(avg_interval)

    logger.debug(f"Dividend frequency: {frequency} (avg {avg_interval:.0f} days)")

    last_date, last_amount = div_list[-1]
    future_dividends: list[tuple[datetime, float]] = []
    current_date = datetime.now()
    projection_end = current_date + timedelta(days=30 * months_ahead)

    next_date = last_date + timedelta(days=avg_interval)
    while next_date <= projection_end and len(future_dividends) < MAX_PROJECTED_DIVIDENDS:
        if next_date > current_date:
            future_dividends.append((next_date, last_amount))
        next_date += timedelta(days=avg_interval)

    return future_dividends, frequency, avg_interval


# Callback type aliases for cleaner signatures
SymbolStartCallback = Callable[[str], None]
SymbolDataCallback = Callable[[str, int, int, str, float], None]


def calculate_dividends(
    portfolio: Portfolio,
    months_ahead: int = 12,
    use_cache: bool = True,
    on_symbol_start: SymbolStartCallback | None = None,
    on_symbol_data: SymbolDataCallback | None = None,
) -> tuple[MonthlyDividends, list[DividendDetail], dict[str, float]]:
    """
    Calculate monthly dividend projections.

    Args:
        portfolio: Portfolio dictionary {symbol: {shares, cost_basis}}
        months_ahead: Number of months to project
        use_cache: Whether to use cached data
        on_symbol_start: Optional callback(symbol) when starting to process a symbol
        on_symbol_data: Optional callback(symbol, hist_count, proj_count, freq, interval)

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

        if on_symbol_start:
            on_symbol_start(symbol)

        logger.info(f"Processing {symbol}")

        dividends = get_dividend_data(symbol, use_cache=use_cache)

        # Fallback: use yield rate for funds without dividend history
        if dividends is None or dividends.empty:
            yield_rate = get_yield_rate(symbol)
            if yield_rate:
                price = get_current_price(symbol, use_cache=use_cache)
                if price:
                    annual_div = price * yield_rate * shares
                    stock_annual_dividends[symbol] = annual_div
                    logger.info(f"{symbol}: yield {yield_rate:.2%} -> ${annual_div:.2f}/yr")
            continue

        future_dividends, frequency, avg_interval = estimate_future_dividends(
            dividends, months_ahead
        )

        if on_symbol_data:
            on_symbol_data(symbol, len(dividends), len(future_dividends), frequency, avg_interval)

        annual_div = sum(amount * shares for _, amount in future_dividends)
        stock_annual_dividends[symbol] = annual_div
        logger.debug(f"{symbol} annual dividend: ${annual_div:.2f}")

        for div_date, div_amount in future_dividends:
            month_key = div_date.strftime("%B %Y")
            total = div_amount * shares
            monthly_totals[month_key] += total

            dividend_details.append(
                DividendDetail(
                    symbol=symbol,
                    date=div_date,
                    amount_per_share=div_amount,
                    shares=shares,
                    total=total,
                )
            )

    return dict(monthly_totals), dividend_details, stock_annual_dividends


def calculate_metrics(
    portfolio: Portfolio,
    use_cache: bool = True,
) -> tuple[StockMetrics, float, float]:
    """
    Calculate portfolio value and metrics.

    Args:
        portfolio: Portfolio dictionary
        use_cache: Whether to use cached price data

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

        current_price = get_current_price(symbol, use_cache=use_cache)

        if not current_price:
            continue

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
    portfolio: Portfolio,
    months_ahead: int = 12,
    use_cache: bool = True,
    show_metrics: bool = True,
    on_symbol_start: SymbolStartCallback | None = None,
    on_symbol_data: SymbolDataCallback | None = None,
) -> CalculationResults:
    """
    Run all calculations and return results.

    Args:
        portfolio: Portfolio dictionary
        months_ahead: Number of months to project
        use_cache: Whether to use cached data
        show_metrics: Whether to calculate portfolio metrics
        on_symbol_start: Callback when starting to process a symbol
        on_symbol_data: Callback with symbol data (symbol, hist_count, proj_count, freq, interval)

    Returns:
        Dictionary containing all calculation results
    """
    logger.info("Starting dividend calculations")

    monthly_divs, div_details, stock_annual = calculate_dividends(
        portfolio,
        months_ahead,
        use_cache,
        on_symbol_start=on_symbol_start,
        on_symbol_data=on_symbol_data,
    )

    results: CalculationResults = {
        "monthly_dividends": monthly_divs,
        "dividend_details": div_details,
        "stock_annual_dividends": stock_annual,
    }

    if show_metrics:
        logger.info("Calculating portfolio metrics")
        metrics, total_value, total_cost = calculate_metrics(portfolio, use_cache=use_cache)

        results["metrics"] = metrics
        results["total_value"] = total_value
        results["total_cost"] = total_cost

    return results
