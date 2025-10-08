"""
Export module.
Handles exporting dividend projections to CSV files.
"""

import csv
from datetime import datetime
from rich.console import Console

console = Console()

def export_to_csv(monthly_dividends, dividend_details, filename):
    """
    Export dividend projections to CSV files.
    Creates two files: monthly summary and detailed breakdown.
    """
    # Export monthly summary
    sorted_months = sorted(
        monthly_dividends.items(),
        key=lambda x: datetime.strptime(x[0], '%B %Y')
    )

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Month', 'Total'])

        for month, amount in sorted_months:
            writer.writerow([month, f"{amount:.2f}"])

    console.print(f"[green]✓ Exported monthly summary to {filename}[/green]")

    # Export detailed breakdown
    detail_filename = filename.replace('.csv', '_detailed.csv')

    with open(detail_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Symbol', 'Amount Per Share', 'Shares', 'Total'])

        for detail in sorted(dividend_details, key=lambda x: x['date']):
            writer.writerow([
                detail['date'].strftime('%Y-%m-%d'),
                detail['symbol'],
                f"{detail['amount_per_share']:.4f}",
                f"{detail['shares']:.0f}",
                f"{detail['total']:.2f}"
            ])

    console.print(f"[green]✓ Exported detailed breakdown to {detail_filename}[/green]")
