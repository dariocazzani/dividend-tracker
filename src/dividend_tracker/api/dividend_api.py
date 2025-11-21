"""
Dividend API module.
Handles fetching dividend data from yfinance with caching.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from ..utils import get_logger

logger = get_logger("api")

CACHE_DIR = Path("data/.cache")
CACHE_EXPIRY_HOURS = 24


def ensure_cache_dir() -> None:
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    gitignore = CACHE_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n")


def get_cache_path(symbol: str) -> Path:
    """Get cache file path for a symbol."""
    return CACHE_DIR / f"{symbol}_dividends.json"


def is_cache_valid(cache_path: Path) -> bool:
    """Check if cache file exists and is not expired."""
    if not cache_path.exists():
        return False

    try:
        with open(cache_path) as f:
            data = json.load(f)

        cached_time = datetime.fromisoformat(data["timestamp"])
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600

        return age_hours < CACHE_EXPIRY_HOURS
    except Exception as e:
        logger.debug(f"Cache validation failed for {cache_path}: {e}")
        return False


def save_to_cache(symbol: str, dividends: pd.Series) -> None:
    """Save dividend data to cache."""
    div_dict = {}
    for date, amount in dividends.items():
        date_str = date.isoformat() if hasattr(date, "isoformat") else str(date)  # type: ignore[union-attr]
        div_dict[date_str] = float(amount)

    cache_data = {"timestamp": datetime.now().isoformat(), "symbol": symbol, "dividends": div_dict}

    with open(get_cache_path(symbol), "w") as f:
        json.dump(cache_data, f)

    logger.debug(f"Saved {symbol} to cache")


def load_from_cache(symbol: str) -> pd.Series | None:
    """Load dividend data from cache, return as pandas Series."""
    try:
        with open(get_cache_path(symbol)) as f:
            data = json.load(f)

        dates = [datetime.fromisoformat(d) for d in data["dividends"]]
        values = list(data["dividends"].values())
        return pd.Series(values, index=dates)
    except Exception as e:
        logger.debug(f"Failed to load {symbol} from cache: {e}")
        return None


def get_dividend_data(symbol: str, use_cache: bool = True) -> pd.Series | None:
    """
    Fetch dividend data for a symbol.
    Returns pandas Series with 2 years of dividend history.
    """
    # Try cache first
    if use_cache and is_cache_valid(get_cache_path(symbol)):
        logger.debug(f"Using cached data for {symbol}")
        return load_from_cache(symbol)

    # Fetch from API
    try:
        logger.debug(f"Fetching {symbol} from yfinance")
        ticker = yf.Ticker(symbol)
        dividends = ticker.dividends

        if dividends.empty:
            logger.warning(f"No dividend history for {symbol}")
            return None

        # Filter to recent 2 years
        cutoff_date = datetime.now() - timedelta(days=365 * 2)
        dividends.index = dividends.index.tz_localize(None)
        dividends = dividends[dividends.index >= cutoff_date]

        # Save to cache
        if use_cache:
            save_to_cache(symbol, dividends)

        return dividends

    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return None


def get_current_price(symbol: str) -> float | None:
    """Get current stock price."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = (
            info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        )
        if price:
            logger.debug(f"Current price for {symbol}: ${price:.2f}")
        return price
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None
