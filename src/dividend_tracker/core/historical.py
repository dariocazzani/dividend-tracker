"""
Historical tracking module.
Store and retrieve historical dividend projections.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..utils import get_logger

logger = get_logger("core.historical")

HISTORICAL_DIR = Path("data/historical")


def ensure_historical_dir() -> None:
    """Create historical directory if it doesn't exist."""
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)


def get_historical_filename(run_date: datetime | None = None) -> Path:
    """
    Get filename for historical data.

    Args:
        run_date: Date of the run, defaults to today

    Returns:
        Path to historical file
    """
    if run_date is None:
        run_date = datetime.now()

    date_str = run_date.strftime("%Y-%m-%d")
    return HISTORICAL_DIR / f"projection_{date_str}.json"


def check_historical_exists(run_date: datetime | None = None) -> bool:
    """Check if historical data already exists for a date."""
    return get_historical_filename(run_date).exists()


def save_historical(
    results: dict[str, Any], portfolio_path: str | Path, run_date: datetime | None = None
) -> Path:
    """
    Save calculation results to historical data.

    Args:
        results: Calculation results dictionary
        portfolio_path: Path to portfolio file used
        run_date: Date of the run

    Returns:
        Path to saved file
    """
    ensure_historical_dir()

    if run_date is None:
        run_date = datetime.now()

    filepath = get_historical_filename(run_date)

    # Check if already exists
    if filepath.exists():
        logger.info(f"Historical data for {run_date.date()} already exists, overwriting")

    # Prepare data for JSON serialization
    historical_data = {
        "date": run_date.isoformat(),
        "portfolio_file": str(portfolio_path),
        "total_value": results.get("total_value", 0),
        "total_cost": results.get("total_cost", 0),
        "monthly_dividends": results.get("monthly_dividends", {}),
        "stock_annual_dividends": results.get("stock_annual_dividends", {}),
        "metrics": _serialize_metrics(results.get("metrics", {})),
    }

    with open(filepath, "w") as f:
        json.dump(historical_data, f, indent=2)

    logger.info(f"Saved historical data to {filepath}")
    return filepath


def _serialize_metrics(metrics: dict) -> dict:
    """Convert metrics to JSON-serializable format."""
    serialized = {}
    for symbol, data in metrics.items():
        serialized[symbol] = {k: v for k, v in data.items() if v is not None}
    return serialized


def load_historical(run_date: datetime | None = None) -> dict | None:
    """
    Load historical data for a specific date.

    Args:
        run_date: Date to load, defaults to today

    Returns:
        Historical data dictionary or None if not found
    """
    filepath = get_historical_filename(run_date)

    if not filepath.exists():
        logger.debug(f"No historical data found for {run_date.date() if run_date else 'today'}")
        return None

    try:
        with open(filepath) as f:
            data = json.load(f)

        logger.info(f"Loaded historical data from {filepath}")
        return data

    except Exception as e:
        logger.error(f"Failed to load historical data: {e}")
        return None


def list_historical_dates() -> list[datetime]:
    """
    List all dates with historical data.

    Returns:
        Sorted list of dates with historical data
    """
    if not HISTORICAL_DIR.exists():
        return []

    dates = []
    for file in HISTORICAL_DIR.glob("projection_*.json"):
        try:
            # Extract date from filename: projection_YYYY-MM-DD.json
            date_str = file.stem.replace("projection_", "")
            date = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(date)
        except ValueError:
            logger.warning(f"Invalid historical filename: {file}")
            continue

    return sorted(dates)


def get_historical_summary() -> dict:
    """
    Get summary statistics from all historical data.

    Returns:
        Dictionary with historical statistics
    """
    dates = list_historical_dates()

    if not dates:
        return {"count": 0, "first_date": None, "last_date": None, "dates": []}

    return {"count": len(dates), "first_date": dates[0], "last_date": dates[-1], "dates": dates}


def display_historical_run(run_date: datetime | str | None = None) -> None:
    """
    Display a specific historical projection.

    Args:
        run_date: Date to display, datetime object, 'latest' string, or None for latest
    """
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    # Handle 'latest' or None
    if run_date is None or (isinstance(run_date, str) and run_date == "latest"):
        dates = list_historical_dates()
        if not dates:
            console.print("[yellow]No historical data found[/yellow]")
            return
        run_date = dates[-1]

    # Ensure run_date is a datetime at this point
    if not isinstance(run_date, datetime):
        console.print(f"[red]Invalid date format: {run_date}[/red]")
        return

    # Load the data
    data = load_historical(run_date)
    if not data:
        date_str = run_date.strftime("%Y-%m-%d")
        console.print(f"[red]No data found for {date_str}[/red]")
        return

    # Display header
    date_str = run_date.strftime("%Y-%m-%d")
    console.print(f"\n[cyan bold]Historical Projection from {date_str}[/cyan bold]")
    console.print(f"[dim]Portfolio: {data['portfolio_file']}[/dim]\n")

    # Portfolio Summary Panel
    total_annual_div = sum(data["stock_annual_dividends"].values())
    portfolio_yield = (
        (total_annual_div / data["total_value"] * 100) if data["total_value"] > 0 else 0
    )

    summary_parts = [f"[bold green]Portfolio Value:[/bold green] ${data['total_value']:,.2f}"]

    if data["total_cost"] > 0:
        total_gain = data["total_value"] - data["total_cost"]
        total_gain_pct = (total_gain / data["total_cost"]) * 100
        gain_color = "green" if total_gain >= 0 else "red"
        summary_parts.append(
            f"[bold cyan]Cost Basis:[/bold cyan] ${data['total_cost']:,.2f}\n"
            f"[bold {gain_color}]Gain/Loss:[/bold {gain_color}] "
            f"${total_gain:,.2f} ({total_gain_pct:+.1f}%)"
        )

    summary_parts.append(
        f"[bold yellow]Annual Dividends:[/bold yellow] ${total_annual_div:,.2f}\n"
        f"[bold yellow]Portfolio Yield:[/bold yellow] {portfolio_yield:.2f}%"
    )

    console.print(
        Panel(
            "\n".join(summary_parts),
            title="Portfolio Summary",
            border_style="green",
            box=box.ROUNDED,
        )
    )

    # Stock-level metrics table
    if data.get("metrics"):
        console.print()
        metrics_table = Table(title="Stock Positions", box=box.ROUNDED, title_style="bold magenta")

        metrics_table.add_column("Symbol", style="cyan", justify="left")
        metrics_table.add_column("Shares", justify="right")
        metrics_table.add_column("Value", style="green", justify="right")
        metrics_table.add_column("Annual Div", style="yellow", justify="right")

        for symbol, metrics in data["metrics"].items():
            annual_div = data["stock_annual_dividends"].get(symbol, 0)

            metrics_table.add_row(
                symbol,
                f"{metrics['shares']:.0f}",
                f"${metrics['current_value']:,.2f}",
                f"${annual_div:.2f}",
            )

        console.print(metrics_table)

    # Monthly Dividends Table
    console.print()
    monthly_table = Table(
        title="Monthly Dividend Projections", box=box.ROUNDED, title_style="bold magenta"
    )

    monthly_table.add_column("Month", style="cyan", justify="left")
    monthly_table.add_column("Amount", style="green bold", justify="right")

    # Sort months chronologically
    sorted_months = sorted(
        data["monthly_dividends"].items(), key=lambda x: datetime.strptime(x[0], "%B %Y")
    )

    for month, amount in sorted_months:
        monthly_table.add_row(month, f"${amount:.2f}")

    console.print(monthly_table)
    console.print()


def display_historical_trend(days: int = 90) -> None:
    """
    Display portfolio trends from historical data.

    Args:
        days: Number of days to look back (default: 90)
    """
    from datetime import timedelta

    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    # Get all historical dates
    dates = list_historical_dates()

    if not dates:
        console.print("[yellow]No historical data found[/yellow]")
        return

    # Filter by days
    cutoff = datetime.now() - timedelta(days=days)
    filtered_dates = [d for d in dates if d >= cutoff]

    if not filtered_dates:
        console.print(f"[yellow]No historical data found in the last {days} days[/yellow]")
        return

    console.print(f"\n[cyan bold]Historical Trends (Last {days} Days)[/cyan bold]\n")

    # Load all historical data
    historical_data: list[tuple[datetime, dict]] = []
    for date in filtered_dates:
        data = load_historical(date)
        if data:
            historical_data.append((date, data))

    if not historical_data:
        console.print("[yellow]Failed to load historical data[/yellow]")
        return

    # Create trend table
    table = Table(
        title="Portfolio Value & Dividend Trends", box=box.ROUNDED, title_style="bold magenta"
    )

    table.add_column("Date", style="cyan", justify="left")
    table.add_column("Portfolio Value", justify="right", style="green")
    table.add_column("Annual Dividends", justify="right", style="yellow")
    table.add_column("Yield", justify="right", style="blue")
    table.add_column("Change", justify="right")

    prev_value: float | None = None

    for date, data in historical_data:
        value = data["total_value"]
        annual_div = sum(data["stock_annual_dividends"].values())
        yield_pct = (annual_div / value * 100) if value > 0 else 0

        # Calculate change from previous run
        if prev_value is not None:
            change = value - prev_value
            change_pct = (change / prev_value * 100) if prev_value > 0 else 0

            if change >= 0:
                change_str = f"[green]+${change:,.2f} (+{change_pct:.1f}%)[/green]"
            else:
                change_str = f"[red]${change:,.2f} ({change_pct:.1f}%)[/red]"
        else:
            change_str = "[dim]—[/dim]"

        table.add_row(
            date.strftime("%Y-%m-%d"),
            f"${value:,.2f}",
            f"${annual_div:,.2f}",
            f"{yield_pct:.2f}%",
            change_str,
        )

        prev_value = value

    console.print(table)

    # Calculate and display period summary
    if len(historical_data) >= 2:
        first_date, first_data = historical_data[0]
        last_date, last_data = historical_data[-1]

        first_value = first_data["total_value"]
        last_value = last_data["total_value"]
        first_annual_div = sum(first_data["stock_annual_dividends"].values())
        last_annual_div = sum(last_data["stock_annual_dividends"].values())

        value_change = last_value - first_value
        value_change_pct = (value_change / first_value * 100) if first_value > 0 else 0

        div_change = last_annual_div - first_annual_div
        div_change_pct = (div_change / first_annual_div * 100) if first_annual_div > 0 else 0

        # Determine colors
        value_color = "green" if value_change >= 0 else "red"
        div_color = "green" if div_change >= 0 else "red"

        summary = (
            f"[bold]Period:[/bold] {first_date.strftime('%Y-%m-%d')} to "
            f"{last_date.strftime('%Y-%m-%d')} "
            f"[dim]({len(historical_data)} data points)[/dim]\n\n"
            f"[bold]Portfolio Value Change:[/bold] "
            f"[{value_color}]${value_change:+,.2f} ({value_change_pct:+.1f}%)[/{value_color}]\n"
            f"[bold]Annual Dividend Change:[/bold] "
            f"[{div_color}]${div_change:+,.2f} ({div_change_pct:+.1f}%)[/{div_color}]"
        )

        console.print()
        console.print(Panel(summary, title="Period Summary", border_style="blue", box=box.ROUNDED))

    console.print()
