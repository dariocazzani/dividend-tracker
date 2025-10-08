"""
Portfolio management module.
Handles loading portfolio from CSV file.
"""

import csv
import sys
from pathlib import Path
from rich.console import Console

PORTFOLIO_FILE = 'data/portfolio.csv'

console = Console()

def load_portfolio():
    """
    Load portfolio from CSV file.
    Expects columns: symbol, shares, cost_basis
    Exits if file doesn't exist.
    """
    portfolio_path = Path(PORTFOLIO_FILE)

    if not portfolio_path.exists():
        console.print(f"[red]Error: Portfolio file '{PORTFOLIO_FILE}' not found![/red]")
        console.print("\n[yellow]Please create a portfolio.csv file with the following format:[/yellow]")
        console.print("[dim]symbol,shares,cost_basis")
        console.print("AAPL,50,150.00")
        console.print("MSFT,30,280.00")
        console.print("KO,100,55.00[/dim]")
        console.print("\n[cyan]Note: cost_basis is optional (average cost per share)[/cyan]")
        sys.exit(1)

    portfolio = {}

    try:
        with open(portfolio_path, 'r') as f:
            reader = csv.DictReader(f)

            # Validate headers
            if 'symbol' not in reader.fieldnames or 'shares' not in reader.fieldnames:
                console.print("[red]Error: CSV must have 'symbol' and 'shares' columns[/red]")
                sys.exit(1)

            for row in reader:
                symbol = row['symbol'].strip().upper()

                if not symbol:
                    continue

                try:
                    shares = float(row['shares'])
                except ValueError:
                    console.print(f"[yellow]Warning: Invalid shares value for {symbol}, skipping[/yellow]")
                    continue

                # Parse cost basis (optional)
                cost_basis = None
                if 'cost_basis' in row and row['cost_basis'].strip():
                    try:
                        cost_basis = float(row['cost_basis'])
                    except ValueError:
                        console.print(f"[yellow]Warning: Invalid cost_basis for {symbol}[/yellow]")

                portfolio[symbol] = {
                    'shares': shares,
                    'cost_basis': cost_basis
                }

        if not portfolio:
            console.print(f"[red]Error: No valid entries found in {PORTFOLIO_FILE}[/red]")
            sys.exit(1)

        console.print(f"[green]✓ Loaded {len(portfolio)} positions from {PORTFOLIO_FILE}[/green]")
        return portfolio

    except Exception as e:
        console.print(f"[red]Error reading portfolio file: {e}[/red]")
        sys.exit(1)
