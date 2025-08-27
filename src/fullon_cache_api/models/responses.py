"""
Response models for fullon_cache_api.

Comprehensive Pydantic models for all API response types with proper validation,
documentation, and OpenAPI support.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseResponse(BaseModel):
    """Base response model for all API responses."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    success: bool = Field(..., description="Operation success status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class HealthResponse(BaseResponse):
    """Health check response model."""

    service: str = Field(..., description="Service name", example="fullon_cache_api")
    status: str = Field(..., description="Service status", example="healthy")
    version: str = Field(..., description="API version", example="0.1.0")
    cache_status: dict[str, str] = Field(..., description="Cache service status")


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for programmatic handling")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class TickerResponse(BaseResponse):
    """Ticker data response model."""

    exchange: str = Field(..., description="Exchange name", example="binance")
    symbol: str = Field(..., description="Trading symbol", example="BTC/USDT")
    ticker_data: dict[str, Any] = Field(
        ..., description="Ticker information from cache"
    )
    cached_at: datetime = Field(..., description="When data was cached")
    cache_hit: bool = Field(..., description="Whether data was found in cache")
    stale: bool = Field(default=False, description="Whether the cached data is stale")


class AllTickersResponse(BaseResponse):
    """All tickers response model."""

    exchange: str = Field(..., description="Exchange name", example="binance")
    tickers: list[dict[str, Any]] = Field(
        ..., description="List of ticker data from cache"
    )
    count: int = Field(..., description="Number of tickers returned")
    cached_at: datetime = Field(..., description="When data was cached")


class Position(BaseModel):
    """Position data model."""
    
    symbol: str = Field(..., description="Trading symbol", example="BTC/USDT")
    exchange: str = Field(..., description="Exchange name", example="binance")
    side: str = Field(..., description="Position side", example="long")
    size: float = Field(..., description="Position size", example=0.5)
    entry_price: float = Field(..., description="Entry price", example=45000.0)
    current_price: float = Field(..., description="Current price", example=45500.0)
    unrealized_pnl: float = Field(..., description="Unrealized P&L", example=250.0)
    margin_used: float = Field(..., description="Margin used", example=2250.0)


class Balance(BaseModel):
    """Balance data model."""
    
    currency: str = Field(..., description="Currency code", example="USDT")
    available: float = Field(..., description="Available balance", example=10000.0)
    used: float = Field(..., description="Used balance", example=2250.0)
    total: float = Field(..., description="Total balance", example=12250.0)


class AccountPositionsResponse(BaseResponse):
    """Account positions response model."""

    user_id: str = Field(..., description="User identifier", example="user123")
    positions: list[Position] = Field(..., description="List of user positions")
    total_positions: int = Field(..., description="Total number of positions")
    cached_at: datetime = Field(..., description="When data was cached")


class AccountBalancesResponse(BaseResponse):
    """Account balances response model."""

    user_id: str = Field(..., description="User identifier", example="user123")
    balances: list[Balance] = Field(..., description="List of currency balances")
    total_balance_usd: float = Field(..., description="Total balance in USD", example=35500.0)
    cached_at: datetime = Field(..., description="When data was cached")


class AccountStatusResponse(BaseResponse):
    """Account status response model."""

    user_id: str = Field(..., description="User identifier", example="user123")
    status: str = Field(..., description="Account status", example="active")
    last_activity: datetime | None = Field(None, description="Last account activity")
    total_positions: int = Field(..., description="Total number of positions")
    total_balance_usd: float = Field(..., description="Total balance in USD")
    margin_level: float | None = Field(None, description="Margin level percentage")
    cached_at: datetime = Field(..., description="When data was cached")


class AccountSummaryResponse(BaseResponse):
    """Account summary response model."""

    total_users: int = Field(..., description="Total number of users", example=150)
    active_users: int = Field(..., description="Number of active users", example=120)
    total_positions: int = Field(..., description="Total positions across all users", example=450)
    total_balance_usd: float = Field(..., description="Total balance across all users", example=2500000.0)
    cache_health: str = Field(..., description="Cache health status", example="healthy")
    last_updated: datetime = Field(..., description="Last update timestamp")


# Legacy models for backward compatibility
class AccountBalanceResponse(BaseResponse):
    """Account balance response model (legacy)."""

    user_id: int = Field(..., description="User identifier")
    exchange: str = Field(..., description="Exchange name")
    balances: dict[str, float] = Field(..., description="Currency balances")
    cached_at: datetime = Field(..., description="When data was cached")


class PositionsResponse(BaseResponse):
    """Account positions response model (legacy)."""

    user_id: int = Field(..., description="User identifier")
    exchange: str | None = Field(None, description="Exchange filter if applied")
    positions: list[dict[str, Any]] = Field(..., description="List of positions")
    total_positions: int = Field(..., description="Total number of positions")
    cached_at: datetime = Field(..., description="When data was cached")


class OrderStatusResponse(BaseResponse):
    """Order status response model."""

    order_id: str = Field(..., description="Order identifier")
    status: str = Field(..., description="Order status", example="filled")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Order side (buy/sell)")
    amount: float = Field(..., description="Order amount")
    price: float | None = Field(None, description="Order price")
    cached_at: datetime = Field(..., description="When status was cached")


class QueueLengthResponse(BaseResponse):
    """Order queue length response model."""

    exchange: str = Field(..., description="Exchange name")
    queue_length: int = Field(..., description="Current queue length")
    cached_at: datetime = Field(..., description="When length was cached")


class BotStatusResponse(BaseResponse):
    """Bot status response model."""

    bot_id: int = Field(..., description="Bot identifier")
    name: str = Field(..., description="Bot name")
    status: str = Field(..., description="Bot status", example="active")
    last_activity: datetime | None = Field(None, description="Last bot activity")
    cached_at: datetime = Field(..., description="When status was cached")


class AllBotsResponse(BaseResponse):
    """All bots status response model."""

    bots: list[dict[str, Any]] = Field(..., description="List of bot statuses")
    total_bots: int = Field(..., description="Total number of bots")
    active_bots: int = Field(..., description="Number of active bots")
    cached_at: datetime = Field(..., description="When data was cached")


class BlockedStatusResponse(BaseResponse):
    """Exchange blocking status response model."""

    exchange: str = Field(..., description="Exchange name")
    symbol: str = Field(..., description="Trading symbol")
    is_blocked: bool = Field(..., description="Whether exchange/symbol is blocked")
    blocking_bot_id: int | None = Field(
        None, description="Bot ID causing block if applicable"
    )
    cached_at: datetime = Field(..., description="When status was cached")


class TradesResponse(BaseResponse):
    """Trades data response model."""

    symbol: str = Field(..., description="Trading symbol")
    exchange: str = Field(..., description="Exchange name")
    trades: list[dict[str, Any]] = Field(..., description="List of trade data")
    count: int = Field(..., description="Number of trades returned")
    cached_at: datetime = Field(..., description="When data was cached")


class TradeStatusResponse(BaseResponse):
    """Trade status response model."""

    trade_key: str = Field(..., description="Trade identifier key")
    status: str = Field(..., description="Trade processing status")
    details: dict[str, Any] = Field(..., description="Trade details")
    cached_at: datetime = Field(..., description="When status was cached")


class TradeQueueResponse(BaseResponse):
    """Trade queue status response model."""

    exchange: str = Field(..., description="Exchange name")
    queue_name: str = Field(..., description="Queue identifier")
    size: int = Field(..., description="Current queue size")
    processing_rate: float = Field(..., description="Items processed per minute")
    last_processed: datetime | None = Field(None, description="Last processing time")
    cached_at: datetime = Field(..., description="When data was cached")


class OHLCVResponse(BaseResponse):
    """OHLCV data response model."""

    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe (1m, 5m, 1h, etc.)")
    exchange: str = Field(..., description="Exchange name")
    data: list[list[float | int]] = Field(..., description="OHLCV data points")
    count: int = Field(..., description="Number of data points")
    cached_at: datetime = Field(..., description="When data was cached")


class SystemHealthResponse(BaseResponse):
    """System health monitoring response model."""

    overall_status: str = Field(..., description="Overall system status")
    services: dict[str, dict[str, Any]] = Field(
        ..., description="Individual service statuses"
    )
    uptime: float = Field(..., description="System uptime in seconds")
    last_check: datetime = Field(..., description="Last health check time")


class ProcessStatusResponse(BaseResponse):
    """Process monitoring response model."""

    process_name: str = Field(..., description="Process identifier")
    status: str = Field(..., description="Process status")
    cpu_usage: float | None = Field(None, description="CPU usage percentage")
    memory_usage: float | None = Field(None, description="Memory usage in MB")
    last_check: datetime = Field(..., description="Last monitoring check")


class ActiveProcessesResponse(BaseResponse):
    """Active processes monitoring response model."""

    processes: list[dict[str, Any]] = Field(..., description="List of active processes")
    total_processes: int = Field(..., description="Total number of active processes")
    system_load: dict[str, float] = Field(..., description="System load metrics")
    cached_at: datetime = Field(..., description="When data was cached")
