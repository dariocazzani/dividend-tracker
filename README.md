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

# Compare multiple portfolios
uv run dividend-tracker --compare data/portfolio_aggressive.csv data/portfolio_conservative.csv

# Save projection to historical data
uv run dividend-tracker --save-historical

# View historical tracking summary
uv run dividend-tracker --show-history

# Enable verbose logging
uv run dividend-tracker --verbose
```

## Options

- `--summary` - Show only monthly totals
- `--quiet` - Reduce verbosity during fetching
- `--months N` - Project N months (default: 12)
- `--no-cache` - Bypass cache, fetch fresh data
- `--export FILE` - Export to CSV
- `--no-metrics` - Skip portfolio metrics table
- `--verbose` - Enable verbose logging
- `--compare FILE [FILE ...]` - Compare multiple portfolio files
- `--save-historical` - Save results to historical data
- `--show-history` - Show historical tracking summary
- `--view-historical DATE` - View specific historical projection (YYYY-MM-DD or "latest")
- `--historical-trend` - Show portfolio value and dividend trends
- `--trend-days N` - Number of days for trend analysis (default: 90)

## Features

✅ **CSV Portfolio** - Easy to update holdings

✅ **Smart Caching** - Fast subsequent runs (24hr expiry)

✅ **Portfolio Metrics** - Current value, cost basis, gains/losses

✅ **Dividend Yield** - Per stock and overall portfolio

✅ **Monthly Projections** - Estimated dividend income by month

✅ **CSV Export** - Save results for spreadsheet analysis

✅ **Beautiful Output** - Rich terminal formatting with tables and colors

✅ **Comparison Mode** - Compare multiple portfolio scenarios side-by-side

✅ **Historical Tracking** - Save, view, and analyze projections over time

✅ **Type Safety** - Full type hints with mypy checking

✅ **Code Quality** - Ruff linting and formatting, pre-commit hooks

## Comparison Mode

Compare different portfolio strategies or scenarios:

```bash
uv run dividend-tracker --compare data/portfolio_aggressive.csv data/portfolio_conservative.csv
```

This displays:
- Side-by-side portfolio value and yield comparison
- Monthly dividend breakdown for each portfolio
- Total annual dividends and average monthly income

## Historical Tracking

Save and analyze your dividend projections over time.

### Save Current Projection

```bash
# Save today's projection to historical data
uv run dividend-tracker --save-historical
```

Running this daily builds a history of your portfolio's projected performance.

### View Historical Data

```bash
# View the most recent historical projection
uv run dividend-tracker --view-historical latest

# View projection from a specific date
uv run dividend-tracker --view-historical 2025-10-08

# Show summary of all historical runs
uv run dividend-tracker --show-history
```

### Analyze Trends

```bash
# Show portfolio trends over last 90 days (default)
uv run dividend-tracker --historical-trend

# Show trends over last 30 days
uv run dividend-tracker --historical-trend --trend-days 30

# Show trends over last 180 days
uv run dividend-tracker --historical-trend --trend-days 180
```

The trend analysis shows:

- Portfolio value changes over time
- Annual dividend income changes
- Portfolio yield trends
- Day-to-day percentage changes
- Period summary with total changes

### Historical Data Storage

- Historical data is stored in `data/historical/` as JSON files
- Files are named by date: `projection_YYYY-MM-DD.json`
- Running with `--save-historical` on the same day overwrites that day's data
- Historical data is NOT tracked in git (excluded via .gitignore)

## Module Responsibilities

- **__main__.py** - Main entry point, argument parsing
- **core/portfolio.py** - Loads and validates portfolio.csv
- **core/calculator.py** - All calculation logic (dividends, metrics)
- **core/comparison.py** - Portfolio comparison logic
- **core/historical.py** - Historical data storage and retrieval
- **api/dividend_api.py** - Fetches dividend data from yfinance, manages cache
- **ui/display.py** - All Rich console formatting and output
- **ui/export.py** - CSV export functionality
- **utils/logging_config.py** - Logging configuration

Each module is focused on a single responsibility for easy maintenance.

## Data Sources

- Stock prices: Yahoo Finance (via yfinance)
- Dividend data: Yahoo Finance historical dividends
- Cache: Local JSON files in `.cache/` directory

## Development

This project uses modern Python development tools for code quality:

### Tools

- **Ruff**: Fast Python linter and formatter
- **Mypy**: Static type checking
- **Pre-commit**: Automated git hooks for quality checks

### Make Commands

```bash
make help       # Show all available commands
make install    # Install dependencies with uv
make lint       # Run linting checks
make format     # Format code with ruff
make typecheck  # Run type checking with mypy
make check      # Run all checks (lint + typecheck)
make run        # Run the dividend tracker
make clean      # Clean cache and build artifacts
```

### Running Checks

Before committing:

```bash
make check
```

Pre-commit hooks will automatically run ruff and format checks on `git commit`.

### Type Hints

All modules use modern Python 3.13 type hints:
- Union types with `|` syntax
- Optional types with `| None`
- Type aliases for complex types
- Full function signatures

## Notes

- Cache expires after 24 hours
- Projections assume dividends remain constant
- Cost basis is optional but enables gain/loss tracking
- No API key required (uses yfinance)
- Historical data stored in `data/historical/` (gitignored)
