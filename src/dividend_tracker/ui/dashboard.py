"""Dashboard display module. Shows consolidated portfolio view."""

from datetime import datetime

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dividend_tracker.core.historical_storage import list_historical_dates, load_historical
from dividend_tracker.types import (
    CalculationResults,
    DividendDetail,
    HistoricalData,
    StockMetrics,
)

console = Console()


def display_dashboard(
    results: CalculationResults,
    previous_data: HistoricalData | None = None,
) -> None:
    """Display the full portfolio dashboard."""
    total_value = results.get("total_value", 0.0)
    total_cost = results.get("total_cost", 0.0)
    stock_annual_dividends = results.get("stock_annual_dividends", {})
    total_annual_div = sum(stock_annual_dividends.values())

    _display_summary_panel(total_value, total_cost, total_annual_div, previous_data)

    metrics = results.get("metrics", {})
    if metrics:
        _display_positions_table(metrics, stock_annual_dividends)

    dividend_details = results.get("dividend_details", [])
    if dividend_details:
        _display_upcoming_dividends(dividend_details)

    _display_historical_trend()


def _display_summary_panel(
    total_value: float,
    total_cost: float,
    total_annual_div: float,
    previous_data: HistoricalData | None,
) -> None:
    """Display portfolio summary with change since last run."""
    portfolio_yield = (total_annual_div / total_value * 100) if total_value > 0 else 0

    value_change_str = ""
    div_change_str = ""

    if previous_data:
        prev_value = previous_data["total_value"]
        prev_annual_div = sum(previous_data["stock_annual_dividends"].values())

        if prev_value > 0:
            value_change = total_value - prev_value
            value_change_pct = (value_change / prev_value) * 100
            color = "green" if value_change >= 0 else "red"
            value_change_str = (
                f"  [{color}]({value_change:+,.0f} / {value_change_pct:+.1f}%)[/{color}]"
            )

        if prev_annual_div > 0:
            div_change = total_annual_div - prev_annual_div
            div_change_pct = (div_change / prev_annual_div) * 100
            color = "green" if div_change >= 0 else "red"
            div_change_str = f"  [{color}]({div_change:+,.0f} / {div_change_pct:+.1f}%)[/{color}]"

    lines = [
        f"[bold green]Portfolio Value:[/bold green]  ${total_value:,.2f}{value_change_str}",
        f"[bold yellow]Annual Dividends:[/bold yellow] ${total_annual_div:,.2f}{div_change_str}",
        f"[bold cyan]Yield:[/bold cyan]            {portfolio_yield:.2f}%",
    ]

    if total_cost > 0:
        total_gain = total_value - total_cost
        total_gain_pct = (total_gain / total_cost) * 100
        gain_color = "green" if total_gain >= 0 else "red"
        gain_line = (
            f"[bold {gain_color}]Total Gain/Loss:[/bold {gain_color}]  "
            f"${total_gain:,.2f} ({total_gain_pct:+.1f}%)"
        )
        lines.insert(1, gain_line)

    console.print()
    console.print(
        Panel(
            "\n".join(lines),
            title="Portfolio Summary",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )


def _display_positions_table(
    metrics: StockMetrics,
    stock_annual_dividends: dict[str, float],
) -> None:
    """Display stock positions table."""
    table = Table(title="Positions", box=box.ROUNDED, title_style="bold magenta")

    table.add_column("Symbol", style="cyan", justify="left")
    table.add_column("Shares", justify="right")
    table.add_column("Value", style="green", justify="right")
    table.add_column("Annual Div", style="yellow", justify="right")
    table.add_column("Yield", justify="right")

    sorted_symbols = sorted(
        metrics.keys(),
        key=lambda s: metrics[s].get("current_value", 0) or 0,
        reverse=True,
    )

    for symbol in sorted_symbols:
        data = metrics[symbol]
        shares = data.get("shares", 0) or 0
        current_value = data.get("current_value", 0) or 0
        annual_div = stock_annual_dividends.get(symbol, 0)
        div_yield = (annual_div / current_value * 100) if current_value > 0 else 0

        table.add_row(
            symbol,
            f"{shares:,.0f}",
            f"${current_value:,.0f}",
            f"${annual_div:,.0f}",
            f"{div_yield:.1f}%",
        )

    console.print()
    console.print(table)


def _display_upcoming_dividends(dividend_details: list[DividendDetail]) -> None:
    """Display upcoming dividends for the next month."""
    now = datetime.now()

    upcoming = [d for d in dividend_details if d["date"] > now]
    if not upcoming:
        return

    sorted_details = sorted(upcoming, key=lambda x: x["date"])
    first_month = sorted_details[0]["date"].strftime("%B %Y")

    month_dividends = [d for d in sorted_details if d["date"].strftime("%B %Y") == first_month]

    table = Table(
        title=f"Upcoming Dividends ({first_month})",
        box=box.ROUNDED,
        title_style="bold magenta",
    )

    table.add_column("Date", style="cyan", justify="left")
    table.add_column("Symbol", justify="left")
    table.add_column("Amount", style="green", justify="right")

    total = 0.0
    for d in month_dividends:
        date_str = d["date"].strftime("%m/%d")
        table.add_row(date_str, d["symbol"], f"${d['total']:.2f}")
        total += d["total"]

    table.add_row("", "[bold]Total[/bold]", f"[bold]${total:.2f}[/bold]")

    console.print()
    console.print(table)


def _display_historical_trend() -> None:
    """Display all historical data as a trend table."""
    dates = list_historical_dates()

    if len(dates) < 2:
        return

    table = Table(title="Historical Trend", box=box.ROUNDED, title_style="bold magenta")

    table.add_column("Date", style="cyan", justify="left")
    table.add_column("Value", style="green", justify="right")
    table.add_column("Annual Div", style="yellow", justify="right")
    table.add_column("Change", justify="right")

    prev_value: float | None = None

    for date in dates:
        data = load_historical(date)
        if not data:
            continue

        value = data["total_value"]
        annual_div = sum(data["stock_annual_dividends"].values())

        if prev_value is not None:
            change = value - prev_value
            change_pct = (change / prev_value * 100) if prev_value > 0 else 0
            color = "green" if change >= 0 else "red"
            change_str = f"[{color}]{change:+,.0f} ({change_pct:+.1f}%)[/{color}]"
        else:
            change_str = "[dim]—[/dim]"

        table.add_row(
            date.strftime("%Y-%m-%d"),
            f"${value:,.0f}",
            f"${annual_div:,.0f}",
            change_str,
        )

        prev_value = value

    console.print()
    console.print(table)


def get_previous_run_data() -> HistoricalData | None:
    """Get the most recent historical data for comparison."""
    dates = list_historical_dates()
    if not dates:
        return None
    return load_historical(dates[-1])
