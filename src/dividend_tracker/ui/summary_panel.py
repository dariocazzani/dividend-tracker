"""Shared summary panel rendering for portfolio displays."""

from rich import box
from rich.panel import Panel


def render_portfolio_summary_panel(
    total_value: float,
    total_cost: float,
    total_annual_div: float,
) -> Panel:
    """
    Render a portfolio summary panel.

    Args:
        total_value: Total portfolio value
        total_cost: Total cost basis
        total_annual_div: Total annual dividends

    Returns:
        Rich Panel object ready for display
    """
    portfolio_yield = (total_annual_div / total_value * 100) if total_value > 0 else 0

    summary_parts = [f"[bold green]Portfolio Value:[/bold green] ${total_value:,.2f}"]

    if total_cost > 0:
        total_gain = total_value - total_cost
        total_gain_pct = (total_gain / total_cost) * 100
        gain_color = "green" if total_gain >= 0 else "red"
        summary_parts.append(
            f"[bold cyan]Cost Basis:[/bold cyan] ${total_cost:,.2f}\n"
            f"[bold {gain_color}]Gain/Loss:[/bold {gain_color}] "
            f"${total_gain:,.2f} ({total_gain_pct:+.1f}%)"
        )

    summary_parts.append(
        f"[bold yellow]Annual Dividends:[/bold yellow] ${total_annual_div:,.2f}\n"
        f"[bold yellow]Portfolio Yield:[/bold yellow] {portfolio_yield:.2f}%"
    )

    return Panel(
        "\n".join(summary_parts),
        title="Portfolio Summary",
        border_style="green",
        box=box.ROUNDED,
    )
