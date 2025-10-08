"""
Dividend API module.
Handles fetching dividend data from yfinance with caching.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import pandas as pd
from rich.console import Console

CACHE_DIR = Path('data/.cache')
CACHE_EXPIRY_HOURS = 24

console = Console()

def ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    gitignore = CACHE_DIR / '.gitignore'
    if not gitignore.exists():
        gitignore.write_text('*\n')

def get_cache_path(symbol):
    """Get cache file path for a symbol."""
    return CACHE_DIR / f"{symbol}_dividends.json"

def is_cache_valid(cache_path):
    """Check if cache file exists and is not expired."""
    if not cache_path.exists():
        return False

    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)

        cached_time = datetime.fromisoformat(data['timestamp'])
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600

        return age_hours < CACHE_EXPIRY_HOURS
    except:
        return False

def save_to_cache(symbol, dividends):
    """Save dividend data to cache."""
    div_dict = {date.isoformat(): float(amount)
                for date, amount in dividends.items()}

    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'dividends': div_dict
    }

    with open(get_cache_path(symbol), 'w') as f:
        json.dump(cache_data, f)

def load_from_cache(symbol):
    """Load dividend data from cache, return as pandas Series."""
    try:
        with open(get_cache_path(symbol), 'r') as f:
            data = json.load(f)

        dates = [datetime.fromisoformat(d) for d in data['dividends'].keys()]
        values = list(data['dividends'].values())
        return pd.Series(values, index=dates)
    except:
        return None

def get_dividend_data(symbol, use_cache=True):
    """
    Fetch dividend data for a symbol.
    Returns pandas Series with 2 years of dividend history.
    """
    # Try cache first
    if use_cache and is_cache_valid(get_cache_path(symbol)):
        console.print(f"  [dim]Using cached data for {symbol}[/dim]")
        return load_from_cache(symbol)

    # Fetch from API
    try:
        ticker = yf.Ticker(symbol)
        dividends = ticker.dividends

        if dividends.empty:
            console.print(f"  [yellow]No dividend history for {symbol}[/yellow]")
            return None

        # Filter to recent 2 years
        cutoff_date = datetime.now() - timedelta(days=365*2)
        dividends.index = dividends.index.tz_localize(None)
        dividends = dividends[dividends.index >= cutoff_date]

        # Save to cache
        if use_cache:
            save_to_cache(symbol, dividends)

        return dividends

    except Exception as e:
        console.print(f"  [red]Error fetching {symbol}: {e}[/red]")
        return None

def get_current_price(symbol):
    """Get current stock price."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
    except:
        return None
