"""Display module. Handles all rich console formatting and output."""

from datetime import datetime

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dividend_tracker.types import DividendDetail, MonthlyDividends, StockMetric, StockMetrics
from dividend_tracker.ui.summary_panel import render_portfolio_summary_panel

console = Console()


def display_portfolio_header() -> None:
    """Display application header."""
    console.print()
    console.print(
        Panel.fit("[bold cyan]Portfolio Dividend Calculator[/bold cyan]", border_style="cyan")
    )


def display_portfolio_metrics(
    metrics: StockMetrics,
    total_value: float,
    total_cost: float,
    stock_annual_dividends: dict[str, float],
) -> None:
    """Display portfolio value and metrics table."""
    table = Table(title="Portfolio Metrics", box=box.ROUNDED, title_style="bold magenta")

    table.add_column("Symbol", style="cyan", justify="left")
    table.add_column("Shares", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Value", style="green", justify="right")
    table.add_column("Cost Basis", justify="right")
    table.add_column("Gain/Loss", justify="right")
    table.add_column("Annual Div", style="yellow", justify="right")
    table.add_column("Yield", style="yellow", justify="right")

    for symbol, data in metrics.items():
        row = _format_metrics_row(symbol, data, stock_annual_dividends)
        table.add_row(*row)

    console.print()
    console.print(table)

    total_annual_div = sum(stock_annual_dividends.values())
    panel = render_portfolio_summary_panel(total_value, total_cost, total_annual_div)
    console.print()
    console.print(panel)


def _format_metrics_row(
    symbol: str,
    data: StockMetric,
    stock_annual_dividends: dict[str, float],
) -> tuple[str, str, str, str, str, str, str, str]:
    """Format a single row for the metrics table."""
    shares = data.get("shares", 0) or 0
    current_price = data.get("current_price")
    current_value = data.get("current_value", 0) or 0

    shares_str = f"{shares:.0f}"
    price_str = f"${current_price:.2f}" if current_price else "N/A"
    value_str = f"${current_value:.2f}"

    cost_basis = data.get("cost_basis")
    gain_loss = data.get("gain_loss")
    gain_loss_pct = data.get("gain_loss_pct")

    if cost_basis is not None and gain_loss is not None and gain_loss_pct is not None:
        cost_str = f"${cost_basis:.2f}"
        gain_str = f"${gain_loss:.2f}"
        if gain_loss >= 0:
            gain_str = f"[green]{gain_str} ({gain_loss_pct:.1f}%)[/green]"
        else:
            gain_str = f"[red]{gain_str} ({gain_loss_pct:.1f}%)[/red]"
    else:
        cost_str = "N/A"
        gain_str = "N/A"

    annual_div = stock_annual_dividends.get(symbol, 0)
    annual_div_str = f"${annual_div:.2f}"

    div_yield = (annual_div / current_value * 100) if current_value > 0 else 0.0
    yield_str = f"{div_yield:.2f}%"

    return (symbol, shares_str, price_str, value_str, cost_str, gain_str, annual_div_str, yield_str)


def display_dividend_projections(
    monthly_dividends: MonthlyDividends,
    dividend_details: list[DividendDetail],
    show_details: bool = True,
) -> None:
    """Display monthly dividend projections."""
    if not monthly_dividends:
        console.print("\n[yellow]No upcoming dividends found.[/yellow]")
        return

    sorted_months = sorted(
        monthly_dividends.items(), key=lambda x: datetime.strptime(x[0], "%B %Y")
    )

    table = Table(
        title="Projected Monthly Dividend Income", box=box.ROUNDED, title_style="bold magenta"
    )

    table.add_column("Month", style="cyan", justify="left")
    table.add_column("Total", style="green bold", justify="right")

    if show_details:
        table.add_column("Details", style="dim", justify="left")

    total_annual = 0.0
    for month, amount in sorted_months:
        total_annual += amount

        if show_details:
            details_str = _format_month_details(month, dividend_details)
            table.add_row(month, f"${amount:.2f}", details_str)
        else:
            table.add_row(month, f"${amount:.2f}")

    console.print()
    console.print(table)

    avg_monthly = total_annual / len(sorted_months) if sorted_months else 0
    summary = (
        f"[bold green]Total Annual:[/bold green] ${total_annual:.2f}\n"
        f"[bold cyan]Average Monthly:[/bold cyan] ${avg_monthly:.2f}\n"
        f"[dim]Based on {len(sorted_months)} months[/dim]"
    )

    console.print()
    console.print(Panel(summary, title="Dividend Summary", border_style="green", box=box.ROUNDED))


def _format_month_details(month: str, dividend_details: list[DividendDetail]) -> str:
    """Format dividend details for a specific month."""
    month_details = [d for d in dividend_details if d["date"].strftime("%B %Y") == month]

    sorted_details = sorted(month_details, key=lambda x: x["date"])

    lines = []
    for d in sorted_details:
        date_str = d["date"].strftime("%m/%d")
        line = (
            f"{d['symbol']}: {date_str} - "
            f"${d['amount_per_share']:.4f} × {d['shares']:.0f} = ${d['total']:.2f}"
        )
        lines.append(line)

    return "\n".join(lines)
