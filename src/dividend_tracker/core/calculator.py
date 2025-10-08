"""
Calculator module.
Contains all dividend projection and portfolio metric calculations.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from rich.console import Console
from ..api import get_dividend_data, get_current_price

console = Console()

def estimate_future_dividends(dividends, months_ahead=12):
    """
    Estimate future dividend payments based on historical pattern.
    Returns list of (date, amount) tuples.
    """
    if dividends is None or len(dividends) < 2:
        return []

    # Convert to sorted list
    div_list = [(date.to_pydatetime() if hasattr(date, 'to_pydatetime') else date, amount)
                for date, amount in dividends.items()]
    div_list.sort(key=lambda x: x[0])

    # Calculate average interval between dividends
    intervals = [
        (div_list[-i][0] - div_list[-i-1][0]).days
        for i in range(1, min(5, len(div_list)))
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

    console.print(f"  [dim]Frequency: {frequency} (avg {avg_interval:.0f} days)[/dim]")

    # Project future dividends
    last_date, last_amount = div_list[-1]
    future_dividends = []
    current_date = datetime.now()
    projection_end = current_date + timedelta(days=30 * months_ahead)

    next_date = last_date + timedelta(days=avg_interval)
    while next_date <= projection_end and len(future_dividends) < 20:
        if next_date > current_date:
            future_dividends.append((next_date, last_amount))
        next_date += timedelta(days=avg_interval)

    return future_dividends

def calculate_dividends(portfolio, months_ahead=12, verbose=True, use_cache=True):
    """Calculate monthly dividend projections."""
    monthly_totals = defaultdict(float)
    dividend_details = []
    stock_annual_dividends = {}

    for symbol, data in portfolio.items():
        shares = data['shares']

        if verbose:
            console.print(f"\n[cyan]Fetching {symbol}...[/cyan]")

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

        # Aggregate by month
        for div_date, div_amount in future_dividends:
            month_key = div_date.strftime('%B %Y')
            total = div_amount * shares
            monthly_totals[month_key] += total

            dividend_details.append({
                'symbol': symbol,
                'date': div_date,
                'amount_per_share': div_amount,
                'shares': shares,
                'total': total
            })

    return monthly_totals, dividend_details, stock_annual_dividends

def calculate_metrics(portfolio):
    """Calculate portfolio value and metrics."""
    metrics = {}
    total_value = 0
    total_cost = 0

    for symbol, data in portfolio.items():
        shares = data['shares']
        cost_basis_per_share = data['cost_basis']

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
                'shares': shares,
                'current_price': current_price,
                'current_value': current_value,
                'cost_basis': cost_basis,
                'gain_loss': gain_loss,
                'gain_loss_pct': gain_loss_pct
            }

    return metrics, total_value, total_cost

def calculate_all(portfolio, months_ahead=12, verbose=True, use_cache=True, show_metrics=True):
    """Run all calculations and return results."""
    results = {}

    # Calculate dividends
    monthly_divs, div_details, stock_annual = calculate_dividends(
        portfolio, months_ahead, verbose, use_cache
    )

    results['monthly_dividends'] = monthly_divs
    results['dividend_details'] = div_details
    results['stock_annual_dividends'] = stock_annual

    # Calculate metrics if requested
    if show_metrics:
        with console.status("[cyan]Calculating portfolio metrics...[/cyan]"):
            metrics, total_value, total_cost = calculate_metrics(portfolio)

        results['metrics'] = metrics
        results['total_value'] = total_value
        results['total_cost'] = total_cost

    return results
