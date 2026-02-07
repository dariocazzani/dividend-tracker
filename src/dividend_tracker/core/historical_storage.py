"""Historical data storage module. Handles saving and loading historical projections."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dividend_tracker.constants import HISTORICAL_DIR
from dividend_tracker.exceptions import HistoricalDataCorruptError
from dividend_tracker.types import HistoricalData
from dividend_tracker.utils import get_logger

logger = get_logger("core.historical")


def ensure_historical_dir() -> None:
    """Create historical directory if it doesn't exist."""
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)


def get_historical_filename(run_date: datetime | None = None) -> Path:
    """Get filename for historical data."""
    if run_date is None:
        run_date = datetime.now()
    date_str = run_date.strftime("%Y-%m-%d")
    return HISTORICAL_DIR / f"projection_{date_str}.json"


def check_historical_exists(run_date: datetime | None = None) -> bool:
    """Check if historical data already exists for a date."""
    return get_historical_filename(run_date).exists()


def _serialize_metrics(metrics: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Convert metrics to JSON-serializable format."""
    serialized: dict[str, dict[str, float]] = {}
    for symbol, data in metrics.items():
        serialized[symbol] = {k: v for k, v in data.items() if v is not None}
    return serialized


def save_historical(
    results: dict[str, Any],
    portfolio_path: str | Path,
    run_date: datetime | None = None,
) -> Path:
    """
    Save calculation results to historical data.

    Args:
        results: Calculation results dictionary
        portfolio_path: Path to portfolio file used
        run_date: Date of the run

    Returns:
        Path to saved file
    """
    ensure_historical_dir()

    if run_date is None:
        run_date = datetime.now()

    filepath = get_historical_filename(run_date)

    if filepath.exists():
        logger.info(f"Historical data for {run_date.date()} already exists, overwriting")

    historical_data: HistoricalData = {
        "date": run_date.isoformat(),
        "portfolio_file": str(portfolio_path),
        "total_value": results.get("total_value", 0),
        "total_cost": results.get("total_cost", 0),
        "monthly_dividends": results.get("monthly_dividends", {}),
        "stock_annual_dividends": results.get("stock_annual_dividends", {}),
        "metrics": _serialize_metrics(results.get("metrics", {})),
    }

    with open(filepath, "w") as f:
        json.dump(historical_data, f, indent=2)

    logger.info(f"Saved historical data to {filepath}")
    return filepath


def load_historical(run_date: datetime | None = None) -> HistoricalData | None:
    """
    Load historical data for a specific date.

    Args:
        run_date: Date to load, defaults to today

    Returns:
        Historical data dictionary or None if not found
    """
    filepath = get_historical_filename(run_date)

    if not filepath.exists():
        logger.debug(f"No historical data found for {run_date.date() if run_date else 'today'}")
        return None

    try:
        with open(filepath) as f:
            data: HistoricalData = json.load(f)
        logger.info(f"Loaded historical data from {filepath}")
        return data
    except json.JSONDecodeError as e:
        raise HistoricalDataCorruptError(str(filepath), str(e)) from e
    except KeyError as e:
        raise HistoricalDataCorruptError(str(filepath), f"Missing key: {e}") from e


def list_historical_dates() -> list[datetime]:
    """List all dates with historical data, sorted chronologically."""
    if not HISTORICAL_DIR.exists():
        return []

    dates = []
    for file in HISTORICAL_DIR.glob("projection_*.json"):
        try:
            date_str = file.stem.replace("projection_", "")
            date = datetime.strptime(date_str, "%Y-%m-%d")
            dates.append(date)
        except ValueError:
            logger.warning(f"Invalid historical filename: {file}")
            continue

    return sorted(dates)


def get_historical_summary() -> dict[str, Any]:
    """Get summary statistics from all historical data."""
    dates = list_historical_dates()

    if not dates:
        return {"count": 0, "first_date": None, "last_date": None, "dates": []}

    return {"count": len(dates), "first_date": dates[0], "last_date": dates[-1], "dates": dates}
