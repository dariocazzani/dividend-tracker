"""
Comparison module.
Compare dividend projections across multiple portfolios.
"""

from datetime import datetime
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table

from ..utils import get_logger
from .calculator import calculate_all
from .portfolio import load_portfolio

logger = get_logger("core.comparison")
console = Console()


def compare_portfolios(
    portfolio_files: list[str | Path], months_ahead: int = 12, use_cache: bool = True
) -> dict[str, dict]:
    """
    Compare multiple portfolios.

    Args:
        portfolio_files: List of portfolio CSV file paths
        months_ahead: Number of months to project
        use_cache: Whether to use cached data

    Returns:
        Dictionary mapping portfolio name to calculation results
    """
    logger.info(f"Comparing {len(portfolio_files)} portfolios")

    results = {}

    for portfolio_file in portfolio_files:
        path = Path(portfolio_file)
        portfolio_name = path.stem  # Filename without extension

        logger.info(f"Processing portfolio: {portfolio_name}")
        console.print(f"\n[cyan]Loading portfolio: {portfolio_name}[/cyan]")

        try:
            portfolio = load_portfolio(path)
            portfolio_results = calculate_all(
                portfolio=portfolio,
                months_ahead=months_ahead,
                verbose=False,  # Quiet mode for comparisons
                use_cache=use_cache,
                show_metrics=True,
            )

            results[portfolio_name] = portfolio_results

        except SystemExit:
            # Portfolio file not found or invalid - error already printed by load_portfolio
            logger.error(f"Failed to process {portfolio_name}: file not found or invalid")
            continue
        except Exception as e:
            logger.error(f"Failed to process {portfolio_name}: {e}")
            console.print(f"[red]Failed to load {portfolio_name}[/red]")
            continue

    return results


def display_comparison(results: dict[str, dict]) -> None:
    """
    Display comparison table for multiple portfolios.

    Args:
        results: Dictionary mapping portfolio name to calculation results
    """
    if not results:
        console.print("[yellow]No portfolios to compare[/yellow]")
        return

    # Summary comparison table
    table = Table(title="Portfolio Comparison", box=box.ROUNDED, title_style="bold magenta")

    table.add_column("Portfolio", style="cyan", justify="left")
    table.add_column("Total Value", style="green", justify="right")
    table.add_column("Annual Dividends", style="yellow", justify="right")
    table.add_column("Portfolio Yield", style="yellow", justify="right")
    table.add_column("Avg Monthly", style="blue", justify="right")

    for portfolio_name, data in results.items():
        total_value = data.get("total_value", 0)
        stock_annual = data.get("stock_annual_dividends", {})
        total_annual_div = sum(stock_annual.values())
        portfolio_yield = (total_annual_div / total_value * 100) if total_value > 0 else 0
        avg_monthly = total_annual_div / 12

        table.add_row(
            portfolio_name,
            f"${total_value:,.2f}",
            f"${total_annual_div:,.2f}",
            f"{portfolio_yield:.2f}%",
            f"${avg_monthly:.2f}",
        )

    console.print()
    console.print(table)

    # Monthly breakdown comparison
    console.print("\n[bold]Monthly Dividend Comparison:[/bold]")

    # Get all unique months across portfolios
    all_months = set()
    for data in results.values():
        all_months.update(data.get("monthly_dividends", {}).keys())

    sorted_months = sorted(all_months, key=lambda x: datetime.strptime(x, "%B %Y"))

    month_table = Table(box=box.ROUNDED)
    month_table.add_column("Month", style="cyan")

    for portfolio_name in results:
        month_table.add_column(portfolio_name, justify="right", style="green")

    for month in sorted_months:
        row = [month]
        for portfolio_name in results:
            monthly_divs = results[portfolio_name].get("monthly_dividends", {})
            amount = monthly_divs.get(month, 0)
            row.append(f"${amount:.2f}")

        month_table.add_row(*row)

    console.print()
    console.print(month_table)
