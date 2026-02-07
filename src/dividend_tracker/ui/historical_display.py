"""Historical data display module. Handles rendering historical projections."""

from datetime import datetime, timedelta

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dividend_tracker.constants import DEFAULT_TREND_DAYS
from dividend_tracker.core.historical_storage import list_historical_dates, load_historical
from dividend_tracker.types import HistoricalData
from dividend_tracker.ui.summary_panel import render_portfolio_summary_panel

console = Console()


def display_historical_run(run_date: datetime | None = None) -> None:
    """
    Display a specific historical projection.

    Args:
        run_date: Date to display, defaults to latest available
    """
    if run_date is None:
        dates = list_historical_dates()
        if not dates:
            console.print("[yellow]No historical data found[/yellow]")
            return
        run_date = dates[-1]

    data = load_historical(run_date)
    if not data:
        date_str = run_date.strftime("%Y-%m-%d")
        console.print(f"[red]No data found for {date_str}[/red]")
        return

    _render_historical_run(run_date, data)


def _render_historical_run(run_date: datetime, data: HistoricalData) -> None:
    """Render a historical projection."""
    date_str = run_date.strftime("%Y-%m-%d")
    console.print(f"\n[cyan bold]Historical Projection from {date_str}[/cyan bold]")
    console.print(f"[dim]Portfolio: {data['portfolio_file']}[/dim]\n")

    total_annual_div = sum(data["stock_annual_dividends"].values())
    panel = render_portfolio_summary_panel(
        total_value=data["total_value"],
        total_cost=data["total_cost"],
        total_annual_div=total_annual_div,
    )
    console.print(panel)

    if data.get("metrics"):
        _render_stock_positions_table(data)

    _render_monthly_dividends_table(data)
    console.print()


def _render_stock_positions_table(data: HistoricalData) -> None:
    """Render stock positions table."""
    console.print()
    table = Table(title="Stock Positions", box=box.ROUNDED, title_style="bold magenta")

    table.add_column("Symbol", style="cyan", justify="left")
    table.add_column("Shares", justify="right")
    table.add_column("Value", style="green", justify="right")
    table.add_column("Annual Div", style="yellow", justify="right")

    for symbol, metrics in data["metrics"].items():
        annual_div = data["stock_annual_dividends"].get(symbol, 0)
        shares = metrics.get("shares", 0)
        current_value = metrics.get("current_value", 0)

        table.add_row(
            symbol,
            f"{shares:.0f}",
            f"${current_value:,.2f}",
            f"${annual_div:.2f}",
        )

    console.print(table)


def _render_monthly_dividends_table(data: HistoricalData) -> None:
    """Render monthly dividends table."""
    console.print()
    table = Table(title="Monthly Dividend Projections", box=box.ROUNDED, title_style="bold magenta")

    table.add_column("Month", style="cyan", justify="left")
    table.add_column("Amount", style="green bold", justify="right")

    sorted_months = sorted(
        data["monthly_dividends"].items(), key=lambda x: datetime.strptime(x[0], "%B %Y")
    )

    for month, amount in sorted_months:
        table.add_row(month, f"${amount:.2f}")

    console.print(table)


def display_historical_trend(days: int = DEFAULT_TREND_DAYS) -> None:
    """
    Display portfolio trends from historical data.

    Args:
        days: Number of days to look back
    """
    dates = list_historical_dates()

    if not dates:
        console.print("[yellow]No historical data found[/yellow]")
        return

    cutoff = datetime.now() - timedelta(days=days)
    filtered_dates = [d for d in dates if d >= cutoff]

    if not filtered_dates:
        console.print(f"[yellow]No historical data found in the last {days} days[/yellow]")
        return

    console.print(f"\n[cyan bold]Historical Trends (Last {days} Days)[/cyan bold]\n")

    historical_data: list[tuple[datetime, HistoricalData]] = []
    for date in filtered_dates:
        data = load_historical(date)
        if data:
            historical_data.append((date, data))

    if not historical_data:
        console.print("[yellow]Failed to load historical data[/yellow]")
        return

    _render_trend_table(historical_data)
    _render_period_summary(historical_data)
    console.print()


def _render_trend_table(historical_data: list[tuple[datetime, HistoricalData]]) -> None:
    """Render the trend table."""
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

        change_str = _format_change(value, prev_value)

        table.add_row(
            date.strftime("%Y-%m-%d"),
            f"${value:,.2f}",
            f"${annual_div:,.2f}",
            f"{yield_pct:.2f}%",
            change_str,
        )

        prev_value = value

    console.print(table)


def _format_change(value: float, prev_value: float | None) -> str:
    """Format the change column value."""
    if prev_value is None:
        return "[dim]—[/dim]"

    change = value - prev_value
    change_pct = (change / prev_value * 100) if prev_value > 0 else 0

    if change >= 0:
        return f"[green]+${change:,.2f} (+{change_pct:.1f}%)[/green]"
    return f"[red]${change:,.2f} ({change_pct:.1f}%)[/red]"


def _render_period_summary(historical_data: list[tuple[datetime, HistoricalData]]) -> None:
    """Render the period summary panel."""
    if len(historical_data) < 2:
        return

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
