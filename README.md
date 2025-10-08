# Dividend Tracker

Calculate projected monthly dividend income from your investment portfolio.

## Project Structure

```
dividend-tracker/
├── src/
│   └── dividend_tracker/
│       ├── __main__.py          # Main entry point
│       ├── core/
│       │   ├── portfolio.py     # Portfolio loading
│       │   └── calculator.py    # Calculation logic
│       ├── api/
│       │   └── dividend_api.py  # API calls & caching
│       └── ui/
│           ├── display.py       # Rich formatting
│           └── export.py        # CSV export
├── data/
│   └── portfolio.csv            # Your portfolio (required!)
├── pyproject.toml               # Project configuration
└── .cache/                      # API response cache (auto-created)
```

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Create your portfolio.csv in the data/ directory:**
   ```csv
   symbol,shares,cost_basis
   AAPL,50,150.00
   MSFT,30,280.00
   KO,100,55.00
   ```

   Note: `cost_basis` is optional (average cost per share)

3. **Run:**
   ```bash
   uv run dividend-tracker
   ```

## Usage

```bash
# Basic run (uses cache, shows metrics)
uv run dividend-tracker

# Summary only (no per-stock breakdown)
uv run dividend-tracker --summary

# Quiet mode (less verbose)
uv run dividend-tracker --quiet

# Project 24 months
uv run dividend-tracker --months 24

# Force fresh data (bypass cache)
uv run dividend-tracker --no-cache

# Export to CSV
uv run dividend-tracker --export dividends.csv

# Skip portfolio metrics
uv run dividend-tracker --no-metrics

# Combine options
uv run dividend-tracker --summary --quiet --export results.csv
```

## Options

- `--summary` - Show only monthly totals
- `--quiet` - Reduce verbosity during fetching
- `--months N` - Project N months (default: 12)
- `--no-cache` - Bypass cache, fetch fresh data
- `--export FILE` - Export to CSV
- `--no-metrics` - Skip portfolio metrics table

## Features

✅ **CSV Portfolio** - Easy to update holdings

✅ **Smart Caching** - Fast subsequent runs (24hr expiry)

✅ **Portfolio Metrics** - Current value, cost basis, gains/losses

✅ **Dividend Yield** - Per stock and overall portfolio

✅ **Monthly Projections** - Estimated dividend income by month

✅ **CSV Export** - Save results for spreadsheet analysis

✅ **Beautiful Output** - Rich terminal formatting with tables and colors

## Module Responsibilities

- **__main__.py** - Main entry point, argument parsing
- **core/portfolio.py** - Loads and validates portfolio.csv
- **api/dividend_api.py** - Fetches dividend data from yfinance, manages cache
- **core/calculator.py** - All calculation logic (dividends, metrics)
- **ui/display.py** - All Rich console formatting and output
- **ui/export.py** - CSV export functionality

Each module is focused on a single responsibility for easy maintenance.

## Data Sources

- Stock prices: Yahoo Finance (via yfinance)
- Dividend data: Yahoo Finance historical dividends
- Cache: Local JSON files in `.cache/` directory

## Notes

- Cache expires after 24 hours
- Projections assume dividends remain constant
- Cost basis is optional but enables gain/loss tracking
- No API key required (uses yfinance)
