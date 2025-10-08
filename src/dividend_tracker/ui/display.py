"""
Display module.
Handles all rich console formatting and output.
"""

from datetime import datetime

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

StockMetrics = dict[str, dict[str, float | None]]
MonthlyDividends = dict[str, float]
DividendDetail = dict[str, datetime | str | float]


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
        shares_str = f"{data['shares']:.0f}"
        price_str = f"${data['current_price']:.2f}" if data["current_price"] else "N/A"
        value_str = f"${data['current_value']:.2f}"

        # Format cost basis and gain/loss
        if data["cost_basis"]:
            cost_str = f"${data['cost_basis']:.2f}"
            gain_str = f"${data['gain_loss']:.2f}"
            if data["gain_loss"] >= 0:
                gain_str = f"[green]{gain_str} ({data['gain_loss_pct']:.1f}%)[/green]"
            else:
                gain_str = f"[red]{gain_str} ({data['gain_loss_pct']:.1f}%)[/red]"
        else:
            cost_str = "N/A"
            gain_str = "N/A"

        # Calculate dividend yield
        annual_div = stock_annual_dividends.get(symbol, 0)
        annual_div_str = f"${annual_div:.2f}"

        div_yield = (annual_div / data["current_value"]) * 100 if data["current_value"] > 0 else 0
        yield_str = f"{div_yield:.2f}%"

        table.add_row(
            symbol, shares_str, price_str, value_str, cost_str, gain_str, annual_div_str, yield_str
        )

    console.print()
    console.print(table)

    # Summary panel
    total_annual_div = sum(stock_annual_dividends.values())
    portfolio_yield = (total_annual_div / total_value * 100) if total_value > 0 else 0

    summary_parts = [f"[bold green]Total Portfolio Value:[/bold green] ${total_value:,.2f}"]

    if total_cost > 0:
        total_gain = total_value - total_cost
        total_gain_pct = (total_gain / total_cost) * 100
        gain_color = "green" if total_gain >= 0 else "red"
        summary_parts.append(
            f"[bold cyan]Total Cost Basis:[/bold cyan] ${total_cost:,.2f}\n"
            f"[bold {gain_color}]Total Gain/Loss:[/bold {gain_color}] "
            f"${total_gain:,.2f} ({total_gain_pct:.1f}%)"
        )

    summary_parts.append(
        f"[bold yellow]Annual Dividends:[/bold yellow] ${total_annual_div:,.2f}\n"
        f"[bold yellow]Portfolio Yield:[/bold yellow] {portfolio_yield:.2f}%"
    )

    console.print()
    console.print(
        Panel(
            "\n".join(summary_parts),
            title="Portfolio Summary",
            border_style="green",
            box=box.ROUNDED,
        )
    )


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

    total_annual = 0
    for month, amount in sorted_months:
        total_annual += amount

        if show_details:
            month_details = [d for d in dividend_details if d["date"].strftime("%B %Y") == month]

            details_lines = [
                f"{d['symbol']}: {d['date'].strftime('%m/%d')} - "
                f"${d['amount_per_share']:.4f} × {d['shares']:.0f} = ${d['total']:.2f}"
                for d in sorted(month_details, key=lambda x: x["date"])
            ]

            table.add_row(month, f"${amount:.2f}", "\n".join(details_lines))
        else:
            table.add_row(month, f"${amount:.2f}")

    console.print()
    console.print(table)

    # Summary
    avg_monthly = total_annual / len(sorted_months) if sorted_months else 0
    summary = (
        f"[bold green]Total Annual:[/bold green] ${total_annual:.2f}\n"
        f"[bold cyan]Average Monthly:[/bold cyan] ${avg_monthly:.2f}\n"
        f"[dim]Based on {len(sorted_months)} months[/dim]"
    )

    console.print()
    console.print(Panel(summary, title="Dividend Summary", border_style="green", box=box.ROUNDED))
