"""Constants for the dividend tracker."""

from pathlib import Path

# Base data directory (relative to project root)
DATA_DIR = Path("data")
CACHE_DIR = DATA_DIR / ".cache"
HISTORICAL_DIR = DATA_DIR / "historical"
DEFAULT_PORTFOLIO_FILE = DATA_DIR / "portfolio.csv"

# Dividend frequency detection thresholds (days between payments)
MONTHLY_INTERVAL_MAX = 40
QUARTERLY_INTERVAL_MAX = 100
SEMI_ANNUAL_INTERVAL_MAX = 200

# Projection limits
MAX_PROJECTED_DIVIDENDS = 20
DIVIDEND_HISTORY_YEARS = 2
DEFAULT_PROJECTION_MONTHS = 12

# Cache settings
CACHE_EXPIRY_HOURS = 24
PRICE_CACHE_EXPIRY_MINUTES = 15

# Historical analysis defaults
DEFAULT_TREND_DAYS = 90
