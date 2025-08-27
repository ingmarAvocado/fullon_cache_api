"""
Request models for fullon_cache_api.

Comprehensive Pydantic models for all API request types with validation,
custom validators, and proper error handling.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseRequest(BaseModel):
    """Base request model for all API requests."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)


class CacheQueryRequest(BaseRequest):
    """Base cache query request."""

    timeout: int | None = Field(
        default=5, ge=1, le=60, description="Query timeout in seconds"
    )


class TickerRequest(CacheQueryRequest):
    """Ticker data request model."""

    exchange: str = Field(..., min_length=2, max_length=50, description="Exchange name")
    symbol: str = Field(..., min_length=3, max_length=20, description="Trading symbol")

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Exchange name must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        if "/" not in v and "-" not in v:
            raise ValueError("Symbol must contain / or - separator")
        return v.upper()


class AllTickersRequest(CacheQueryRequest):
    """All tickers request model."""

    exchange: str = Field(..., min_length=2, max_length=50, description="Exchange name")

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Exchange name must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()


class AccountRequest(CacheQueryRequest):
    """Account data request model."""

    user_id: int = Field(..., gt=0, description="User identifier")
    exchange: str | None = Field(
        None, min_length=2, max_length=50, description="Filter by exchange"
    )

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str | None) -> str | None:
        """Validate exchange name format if provided."""
        if v is not None:
            if not v.replace("_", "").replace("-", "").isalnum():
                raise ValueError(
                    "Exchange name must be alphanumeric with optional hyphens/underscores"
                )
            return v.lower()
        return v


class BalanceRequest(CacheQueryRequest):
    """Account balance request model."""

    user_id: int = Field(..., gt=0, description="User identifier")
    exchange: str = Field(..., min_length=2, max_length=50, description="Exchange name")

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Exchange name must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()


class OrderRequest(CacheQueryRequest):
    """Order data request model."""

    order_id: str = Field(
        ..., min_length=1, max_length=100, description="Order identifier"
    )


class QueueLengthRequest(CacheQueryRequest):
    """Queue length request model."""

    exchange: str = Field(..., min_length=2, max_length=50, description="Exchange name")

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Exchange name must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()


class BotRequest(CacheQueryRequest):
    """Bot data request model."""

    bot_id: int = Field(..., gt=0, description="Bot identifier")


class BlockedStatusRequest(CacheQueryRequest):
    """Exchange blocking status request model."""

    exchange: str = Field(..., min_length=2, max_length=50, description="Exchange name")
    symbol: str = Field(..., min_length=3, max_length=20, description="Trading symbol")

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Exchange name must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        if "/" not in v and "-" not in v:
            raise ValueError("Symbol must contain / or - separator")
        return v.upper()


class TradesRequest(CacheQueryRequest):
    """Trades data request model."""

    symbol: str = Field(..., min_length=3, max_length=20, description="Trading symbol")
    exchange: str = Field(..., min_length=2, max_length=50, description="Exchange name")
    limit: int | None = Field(
        default=100, ge=1, le=1000, description="Number of trades to return"
    )

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Exchange name must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        if "/" not in v and "-" not in v:
            raise ValueError("Symbol must contain / or - separator")
        return v.upper()


class TradeStatusRequest(CacheQueryRequest):
    """Trade status request model."""

    trade_key: str = Field(
        ..., min_length=1, max_length=100, description="Trade identifier key"
    )


class TradeQueueRequest(CacheQueryRequest):
    """Trade queue request model."""

    exchange: str = Field(..., min_length=2, max_length=50, description="Exchange name")
    queue_name: str | None = Field(
        None, max_length=50, description="Specific queue name"
    )

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Exchange name must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()


class OHLCVRequest(CacheQueryRequest):
    """OHLCV data request model."""

    symbol: str = Field(..., min_length=3, max_length=20, description="Trading symbol")
    timeframe: str = Field(
        ..., description="Timeframe", pattern=r"^(1m|5m|15m|30m|1h|4h|1d|1w|1M)$"
    )
    exchange: str = Field(..., min_length=2, max_length=50, description="Exchange name")
    limit: int | None = Field(
        default=100, ge=1, le=1000, description="Data points limit"
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        if "/" not in v and "-" not in v:
            raise ValueError("Symbol must contain / or - separator")
        return v.upper()

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: str) -> str:
        """Validate exchange name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Exchange name must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()


class ProcessRequest(CacheQueryRequest):
    """Process monitoring request model."""

    process_name: str = Field(
        ..., min_length=1, max_length=100, description="Process identifier"
    )


class TimeRangeRequest(BaseRequest):
    """Time range filter request."""

    start_time: datetime | None = Field(None, description="Start time filter")
    end_time: datetime | None = Field(None, description="End time filter")

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: datetime | None, info: Any) -> datetime | None:
        """Validate that end_time is after start_time."""
        if v and info.data and "start_time" in info.data and info.data["start_time"]:
            if v <= info.data["start_time"]:
                raise ValueError("end_time must be after start_time")
        return v


class PaginationRequest(BaseRequest):
    """Pagination request model."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    limit: int = Field(default=100, ge=1, le=1000, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.limit


class SortRequest(BaseRequest):
    """Sort request model."""

    sort_by: str = Field(
        ..., min_length=1, max_length=50, description="Field to sort by"
    )
    sort_order: str = Field(
        default="asc", pattern=r"^(asc|desc)$", description="Sort order"
    )

    @field_validator("sort_by")
    @classmethod
    def validate_sort_field(cls, v: str) -> str:
        """Validate sort field contains only valid characters."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Sort field must be alphanumeric with optional hyphens/underscores"
            )
        return v.lower()


class FilterRequest(BaseRequest):
    """Generic filter request model."""

    filters: dict[str, Any] = Field(default_factory=dict, description="Filter criteria")

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate filter dictionary structure."""
        if not isinstance(v, dict):
            raise ValueError("Filters must be a dictionary")

        # Validate filter keys
        for key in v.keys():
            if (
                not isinstance(key, str)
                or not key.replace("_", "").replace("-", "").isalnum()
            ):
                raise ValueError(
                    "Filter keys must be alphanumeric strings with optional hyphens/underscores"
                )

        return v
