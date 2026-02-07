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
- Show your portfolio summary, positions, upcoming dividends, and historical trend
- Auto-save today's snapshot for tracking over time

## Portfolio File

Drop your **Fidelity CSV export** directly into `data/portfolio.csv` - it works automatically.

Or use a simple format:

```csv
symbol,shares,cost_basis
AAPL,50,150.00
VTI,100,200.00
```

### Supported Formats

| Format              | How to get it                                    |
|---------------------|--------------------------------------------------|
| **Fidelity export** | Fidelity.com → Positions → Download              |
| **Simple CSV**      | Create with `symbol,shares,cost_basis` columns   |

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
╰────────┴────────┴─────────┴─────╯

       Upcoming Dividends (Feb)
╭───────┬────────┬─────────╮
│ Date  │ Symbol │ Amount  │
├───────┼────────┼─────────┤
│ 02/15 │ SCHD   │ $125    │
│ 02/20 │ VTI    │ $85     │
│       │ Total  │ $210    │
╰───────┴────────┴─────────╯
```

## Options

```bash
uv run dividend-tracker              # Normal run (uses Fidelity prices)
uv run dividend-tracker --live       # Fetch live prices from Yahoo
uv run dividend-tracker --no-save    # Don't save to history
uv run dividend-tracker --no-cache   # Force fresh dividend data fetch
uv run dividend-tracker --verbose    # Debug logging
```

## How It Works

- **Prices**: Uses values from Fidelity export (or Yahoo with `--live`)
- **Dividends**: Fetched from Yahoo Finance (cached 24 hours)
- **History**: Auto-saves daily snapshots to `data/historical/`
- **Ticker Extraction**: Handles formats like `VANGUARD (XNAS:VTI)` → `VTI`

## Development

```bash
make check    # Run linting + type checks
make format   # Auto-format code
```
