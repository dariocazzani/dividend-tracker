"""Dividend API module. Handles fetching dividend data from yfinance with caching."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from dividend_tracker.constants import (
    CACHE_DIR,
    CACHE_EXPIRY_HOURS,
    DIVIDEND_HISTORY_YEARS,
    PRICE_CACHE_EXPIRY_MINUTES,
)
from dividend_tracker.utils import get_logger

logger = get_logger("api")


def ensure_cache_dir() -> None:
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    gitignore = CACHE_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n")


def _get_dividend_cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol}_dividends.json"


def _get_price_cache_path(symbol: str) -> Path:
    return CACHE_DIR / f"{symbol}_price.json"


def _is_cache_valid(cache_path: Path, expiry_hours: float) -> bool:
    """Check if cache file exists and is not expired."""
    if not cache_path.exists():
        return False
    try:
        with open(cache_path) as f:
            data = json.load(f)
        cached_time = datetime.fromisoformat(data["timestamp"])
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600
        return age_hours < expiry_hours
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.debug(f"Cache validation failed for {cache_path}: {e}")
        return False


def _save_dividends_to_cache(symbol: str, dividends: pd.Series) -> None:  # type: ignore[type-arg]
    """Save dividend data to cache."""
    ensure_cache_dir()
    div_dict: dict[str, float] = {}
    for idx, amount in zip(dividends.index, dividends.values, strict=False):
        date_obj = pd.Timestamp(idx).to_pydatetime()
        div_dict[date_obj.isoformat()] = float(amount)

    cache_data = {"timestamp": datetime.now().isoformat(), "symbol": symbol, "dividends": div_dict}

    with open(_get_dividend_cache_path(symbol), "w") as f:
        json.dump(cache_data, f)
    logger.debug(f"Saved {symbol} dividends to cache")


def _load_dividends_from_cache(symbol: str) -> pd.Series | None:  # type: ignore[type-arg]
    """Load dividend data from cache."""
    try:
        with open(_get_dividend_cache_path(symbol)) as f:
            data = json.load(f)
        dates = [datetime.fromisoformat(d) for d in data["dividends"]]
        values = list(data["dividends"].values())
        return pd.Series(values, index=dates)
    except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError) as e:
        logger.debug(f"Failed to load {symbol} from cache: {e}")
        return None


def _save_price_to_cache(symbol: str, price: float) -> None:
    """Save price data to cache."""
    ensure_cache_dir()
    cache_data = {"timestamp": datetime.now().isoformat(), "symbol": symbol, "price": price}
    with open(_get_price_cache_path(symbol), "w") as f:
        json.dump(cache_data, f)
    logger.debug(f"Saved {symbol} price to cache")


def _load_price_from_cache(symbol: str) -> float | None:
    """Load price from cache if valid."""
    cache_path = _get_price_cache_path(symbol)
    expiry_hours = PRICE_CACHE_EXPIRY_MINUTES / 60

    if not _is_cache_valid(cache_path, expiry_hours):
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)
        return float(data["price"])
    except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError) as e:
        logger.debug(f"Failed to load {symbol} price from cache: {e}")
        return None


def get_dividend_data(symbol: str, use_cache: bool = True) -> pd.Series | None:  # type: ignore[type-arg]
    """Fetch dividend data for a symbol. Returns 2 years of dividend history."""
    cache_path = _get_dividend_cache_path(symbol)

    if use_cache and _is_cache_valid(cache_path, CACHE_EXPIRY_HOURS):
        logger.debug(f"Using cached data for {symbol}")
        return _load_dividends_from_cache(symbol)

    try:
        logger.debug(f"Fetching {symbol} from yfinance")
        ticker = yf.Ticker(symbol)
        dividends = ticker.dividends

        if dividends.empty:
            logger.warning(f"No dividend history for {symbol}")
            return None

        cutoff_date = datetime.now() - timedelta(days=365 * DIVIDEND_HISTORY_YEARS)
        dividends.index = dividends.index.tz_localize(None)
        dividends = dividends[dividends.index >= cutoff_date]

        if use_cache:
            _save_dividends_to_cache(symbol, dividends)

        return dividends

    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return None


def get_current_price(symbol: str, use_cache: bool = True) -> float | None:
    """Get current stock price with caching."""
    if use_cache:
        cached_price = _load_price_from_cache(symbol)
        if cached_price is not None:
            logger.debug(f"Using cached price for {symbol}: ${cached_price:.2f}")
            return cached_price

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = (
            info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        )
        if price:
            logger.debug(f"Current price for {symbol}: ${price:.2f}")
            if use_cache:
                _save_price_to_cache(symbol, price)
        return price
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None
