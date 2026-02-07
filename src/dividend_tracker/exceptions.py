"""Custom exceptions for the dividend tracker."""


class DividendTrackerError(Exception):
    """Base exception for dividend tracker errors."""


class PortfolioError(DividendTrackerError):
    """Base exception for portfolio-related errors."""


class PortfolioFileNotFoundError(PortfolioError):
    """Raised when portfolio file doesn't exist."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Portfolio file '{path}' not found")


class PortfolioInvalidFormatError(PortfolioError):
    """Raised when portfolio CSV has invalid format."""


class PortfolioEmptyError(PortfolioError):
    """Raised when portfolio has no valid entries."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"No valid entries found in {path}")


class HistoricalDataError(DividendTrackerError):
    """Base exception for historical data errors."""


class HistoricalDataNotFoundError(HistoricalDataError):
    """Raised when historical data for a date doesn't exist."""

    def __init__(self, date_str: str):
        self.date_str = date_str
        super().__init__(f"No historical data found for {date_str}")


class HistoricalDataCorruptError(HistoricalDataError):
    """Raised when historical data file is corrupted."""

    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"Corrupted historical data at {path}: {reason}")
