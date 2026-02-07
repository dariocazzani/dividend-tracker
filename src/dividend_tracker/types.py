"""Centralized type definitions for the dividend tracker."""

from datetime import datetime
from typing import TypedDict


class PositionData(TypedDict):
    """Data for a single portfolio position."""

    shares: float | None
    cost_basis: float | None


Portfolio = dict[str, PositionData]


class DividendDetail(TypedDict):
    """Details of a single dividend payment."""

    symbol: str
    date: datetime
    amount_per_share: float
    shares: float
    total: float


MonthlyDividends = dict[str, float]


class StockMetric(TypedDict, total=False):
    """Metrics for a single stock position."""

    shares: float
    current_price: float | None
    current_value: float
    cost_basis: float | None
    gain_loss: float | None
    gain_loss_pct: float | None


StockMetrics = dict[str, StockMetric]


class CalculationResults(TypedDict, total=False):
    """Results from calculate_all function."""

    monthly_dividends: MonthlyDividends
    dividend_details: list[DividendDetail]
    stock_annual_dividends: dict[str, float]
    metrics: StockMetrics
    total_value: float
    total_cost: float


class HistoricalData(TypedDict):
    """Historical projection data stored as JSON."""

    date: str
    portfolio_file: str
    total_value: float
    total_cost: float
    monthly_dividends: MonthlyDividends
    stock_annual_dividends: dict[str, float]
    metrics: dict[str, dict[str, float]]
