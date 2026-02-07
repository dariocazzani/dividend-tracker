# Dividend Tracker

Track your portfolio value and dividends over time.

## Quick Start

```bash
# Install
uv sync

# Run
uv run dividend-tracker
```

That's it. The tool will:
- Load your portfolio from `data/portfolio.csv`
- Fetch current prices and dividend data
- Show your portfolio summary, positions, upcoming dividends, and historical trend
- Auto-save today's snapshot for tracking over time

## Portfolio File

Create `data/portfolio.csv`:

```csv
symbol,shares,cost_basis
AAPL,50,150.00
VTI,100,200.00
SCHD,200,75.50
```

- `symbol` - Ticker symbol (or full name with ticker in parentheses like `VANGUARD (XNAS:VTI)`)
- `shares` - Number of shares
- `cost_basis` - Optional: your cost per share for gain/loss tracking

## What You'll See

```
╭────────────────────── Portfolio Summary ──────────────────────╮
│ Portfolio Value:  $125,430.00  (+1,250 / +1.0%)               │
│ Total Gain/Loss:  $15,430.00 (+14.0%)                         │
│ Annual Dividends: $3,150.00  (+25 / +0.8%)                    │
│ Yield:            2.51%                                       │
╰───────────────────────────────────────────────────────────────╯

             Positions
╭────────┬────────┬─────────┬─────╮
│ Symbol │ Shares │   Value │ ... │
├────────┼────────┼─────────┼─────┤
│ VTI    │    100 │  $34k   │     │
│ SCHD   │    200 │  $18k   │     │
│ ...    │        │         │     │
╰────────┴────────┴─────────┴─────╯

       Upcoming Dividends (Feb)
╭───────┬────────┬─────────╮
│ Date  │ Symbol │ Amount  │
├───────┼────────┼─────────┤
│ 02/15 │ SCHD   │ $125    │
│ 02/20 │ VTI    │ $85     │
│       │ Total  │ $210    │
╰───────┴────────┴─────────╯

        Historical Trend
╭────────────┬─────────┬─────────╮
│ Date       │   Value │ Change  │
├────────────┼─────────┼─────────┤
│ 2026-01-21 │ $125k   │ +1.0%   │
│ 2026-01-07 │ $124k   │ -0.2%   │
│ ...        │         │         │
╰────────────┴─────────┴─────────╯
```

## Options

```bash
uv run dividend-tracker              # Normal run (auto-saves)
uv run dividend-tracker --no-save    # Don't save to history
uv run dividend-tracker --no-cache   # Force fresh data fetch
uv run dividend-tracker --verbose    # Debug logging
```

## How It Works

- **Data Source**: Yahoo Finance (no API key needed)
- **Caching**: Prices cached 15 min, dividends cached 24 hours
- **History**: Auto-saves daily snapshots to `data/historical/`
- **Ticker Extraction**: Handles formats like `VANGUARD (XNAS:VTI)` → `VTI`

## Development

```bash
make check    # Run linting + type checks
make format   # Auto-format code
```
