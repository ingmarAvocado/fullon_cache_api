"""
Pydantic data models for FastAPI WebSocket cache operation payloads.

This module defines typed data structures for all cache operations,
optimized for FastAPI WebSocket JSON serialization with fullon_log integration.
"""

import time
from decimal import Decimal
from typing import Any


def _safe_get_component_logger(name: str):
    try:
        from fullon_log import get_component_logger as _gcl  # type: ignore

        return _gcl(name)
    except Exception:  # pragma: no cover - environment dependent
        import logging

        class _KVLLoggerAdapter:
            def __init__(self, base):
                self._base = base

            def _fmt(self, msg: str, **kwargs):
                if kwargs:
                    kv = " ".join(f"{k}={v}" for k, v in kwargs.items())
                    return f"{msg} | {kv}"
                return msg

            def debug(self, msg, *args, **kwargs):
                self._base.debug(self._fmt(msg, **kwargs), *args)

            def info(self, msg, *args, **kwargs):
                self._base.info(self._fmt(msg, **kwargs), *args)

            def warning(self, msg, *args, **kwargs):
                self._base.warning(self._fmt(msg, **kwargs), *args)

            def error(self, msg, *args, **kwargs):
                self._base.error(self._fmt(msg, **kwargs), *args)

        return _KVLLoggerAdapter(logging.getLogger(name))


from pydantic import BaseModel, Field, validator

# Initialize component logger for data models
logger = _safe_get_component_logger("fullon.api.cache.models.data")


class TickerData(BaseModel):
    """Ticker data model for FastAPI WebSocket cache operations."""

    symbol: str = Field(..., description="Trading symbol (e.g., BTC/USDT)")
    exchange: str = Field(..., description="Exchange identifier")
    price: Decimal | None = Field(None, description="Current price")
    volume: Decimal | None = Field(None, description="24h volume")
    high: Decimal | None = Field(None, description="24h high price")
    low: Decimal | None = Field(None, description="24h low price")
    change: Decimal | None = Field(None, description="24h price change")
    change_percent: Decimal | None = Field(None, description="24h change percentage")
    timestamp: float = Field(default_factory=time.time, description="Data timestamp")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "Ticker data model created",
            symbol=self.symbol,
            exchange=self.exchange,
            has_price=self.price is not None,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        json_encoders = {Decimal: lambda v: float(v) if v is not None else None}
        schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "price": 45000.0,
                "volume": 1234.56,
                "high": 46000.0,
                "low": 44000.0,
                "change": 1000.0,
                "change_percent": 2.22,
                "timestamp": 1627846261.75,
            }
        }


class PositionData(BaseModel):
    """Position data model for FastAPI WebSocket cache operations."""

    user_id: int = Field(..., description="User identifier")
    exchange: str = Field(..., description="Exchange identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Position side (long/short)")
    size: Decimal = Field(..., description="Position size")
    entry_price: Decimal | None = Field(None, description="Average entry price")
    mark_price: Decimal | None = Field(None, description="Current mark price")
    unrealized_pnl: Decimal | None = Field(None, description="Unrealized PnL")
    realized_pnl: Decimal | None = Field(None, description="Realized PnL")
    timestamp: float = Field(default_factory=time.time, description="Data timestamp")

    @validator("side")
    def validate_side(cls, v: Any) -> Any:
        """Validate position side."""
        if v.lower() not in ["long", "short"]:
            logger.error("Invalid position side", side=v)
            raise ValueError(f"Invalid position side: {v}")
        return v.lower()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "Position data model created",
            user_id=self.user_id,
            exchange=self.exchange,
            symbol=self.symbol,
            side=self.side,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        json_encoders = {Decimal: lambda v: float(v) if v is not None else None}
        schema_extra = {
            "example": {
                "user_id": 1,
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "side": "long",
                "size": 0.1,
                "entry_price": 44000.0,
                "mark_price": 45000.0,
                "unrealized_pnl": 100.0,
                "realized_pnl": 0.0,
                "timestamp": 1627846261.75,
            }
        }


class BalanceData(BaseModel):
    """Balance data model for FastAPI WebSocket cache operations."""

    user_id: int = Field(..., description="User identifier")
    exchange: str = Field(..., description="Exchange identifier")
    asset: str = Field(..., description="Asset symbol (e.g., BTC, USDT)")
    available: Decimal = Field(..., description="Available balance")
    locked: Decimal = Field(default=Decimal("0"), description="Locked balance")
    total: Decimal | None = Field(None, description="Total balance")
    timestamp: float = Field(default_factory=time.time, description="Data timestamp")

    @validator("total", always=True)
    def calculate_total(cls, v: Any, values: dict[str, Any]) -> Any:
        """Calculate total balance if not provided."""
        if v is None and "available" in values and "locked" in values:
            return values["available"] + values["locked"]
        return v

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "Balance data model created",
            user_id=self.user_id,
            exchange=self.exchange,
            asset=self.asset,
            total=float(self.total) if self.total else None,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        json_encoders = {Decimal: lambda v: float(v) if v is not None else None}
        schema_extra = {
            "example": {
                "user_id": 1,
                "exchange": "binance",
                "asset": "USDT",
                "available": 1000.0,
                "locked": 100.0,
                "total": 1100.0,
                "timestamp": 1627846261.75,
            }
        }


class OrderData(BaseModel):
    """Order data model for FastAPI WebSocket cache operations."""

    order_id: str = Field(..., description="Unique order identifier")
    user_id: int = Field(..., description="User identifier")
    exchange: str = Field(..., description="Exchange identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Order side (buy/sell)")
    type: str = Field(..., description="Order type (market/limit/stop)")
    status: str = Field(..., description="Order status")
    quantity: Decimal = Field(..., description="Order quantity")
    filled_quantity: Decimal = Field(
        default=Decimal("0"), description="Filled quantity"
    )
    price: Decimal | None = Field(None, description="Order price")
    average_price: Decimal | None = Field(None, description="Average fill price")
    created_at: float = Field(
        default_factory=time.time, description="Order creation timestamp"
    )
    updated_at: float = Field(
        default_factory=time.time, description="Last update timestamp"
    )

    @validator("side")
    def validate_side(cls, v: Any) -> Any:
        """Validate order side."""
        if v.lower() not in ["buy", "sell"]:
            logger.error("Invalid order side", side=v)
            raise ValueError(f"Invalid order side: {v}")
        return v.lower()

    @validator("type")
    def validate_type(cls, v: Any) -> Any:
        """Validate order type."""
        allowed_types = ["market", "limit", "stop", "stop_limit"]
        if v.lower() not in allowed_types:
            logger.error("Invalid order type", type=v, allowed_types=allowed_types)
            raise ValueError(f"Invalid order type: {v}")
        return v.lower()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "Order data model created",
            order_id=self.order_id,
            user_id=self.user_id,
            exchange=self.exchange,
            symbol=self.symbol,
            status=self.status,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        json_encoders = {Decimal: lambda v: float(v) if v is not None else None}
        schema_extra = {
            "example": {
                "order_id": "order_123456",
                "user_id": 1,
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "side": "buy",
                "type": "limit",
                "status": "filled",
                "quantity": 0.1,
                "filled_quantity": 0.1,
                "price": 44000.0,
                "average_price": 44050.0,
                "created_at": 1627846261.75,
                "updated_at": 1627846261.85,
            }
        }


class TradeData(BaseModel):
    """Trade data model for FastAPI WebSocket cache operations."""

    trade_id: str = Field(..., description="Unique trade identifier")
    user_id: int | None = Field(None, description="User identifier (if user trade)")
    exchange: str = Field(..., description="Exchange identifier")
    symbol: str = Field(..., description="Trading symbol")
    side: str = Field(..., description="Trade side (buy/sell)")
    quantity: Decimal = Field(..., description="Trade quantity")
    price: Decimal = Field(..., description="Trade price")
    fee: Decimal | None = Field(None, description="Trade fee")
    fee_asset: str | None = Field(None, description="Fee asset")
    timestamp: float = Field(default_factory=time.time, description="Trade timestamp")

    @validator("side")
    def validate_side(cls, v: Any) -> Any:
        """Validate trade side."""
        if v.lower() not in ["buy", "sell"]:
            logger.error("Invalid trade side", side=v)
            raise ValueError(f"Invalid trade side: {v}")
        return v.lower()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "Trade data model created",
            trade_id=self.trade_id,
            exchange=self.exchange,
            symbol=self.symbol,
            side=self.side,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        json_encoders = {Decimal: lambda v: float(v) if v is not None else None}
        schema_extra = {
            "example": {
                "trade_id": "trade_123456",
                "user_id": 1,
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "side": "buy",
                "quantity": 0.1,
                "price": 45000.0,
                "fee": 4.5,
                "fee_asset": "USDT",
                "timestamp": 1627846261.75,
            }
        }


class OHLCVData(BaseModel):
    """OHLCV data model for FastAPI WebSocket cache operations."""

    symbol: str = Field(..., description="Trading symbol")
    exchange: str = Field(..., description="Exchange identifier")
    timeframe: str = Field(..., description="Timeframe (1m, 5m, 1h, 1d, etc.)")
    timestamp: float = Field(..., description="Candle timestamp")
    open: Decimal = Field(..., description="Opening price")
    high: Decimal = Field(..., description="Highest price")
    low: Decimal = Field(..., description="Lowest price")
    close: Decimal = Field(..., description="Closing price")
    volume: Decimal = Field(..., description="Trading volume")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "OHLCV data model created",
            symbol=self.symbol,
            exchange=self.exchange,
            timeframe=self.timeframe,
            timestamp=self.timestamp,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        json_encoders = {Decimal: lambda v: float(v) if v is not None else None}
        schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "timeframe": "1h",
                "timestamp": 1627846200.0,
                "open": 44000.0,
                "high": 45000.0,
                "low": 43500.0,
                "close": 44800.0,
                "volume": 123.45,
            }
        }


class ProcessData(BaseModel):
    """Process data model for FastAPI WebSocket cache operations."""

    process_id: str = Field(..., description="Process identifier")
    name: str = Field(..., description="Process name")
    status: str = Field(..., description="Process status")
    pid: int | None = Field(None, description="Process ID")
    cpu_percent: float | None = Field(None, description="CPU usage percentage")
    memory_percent: float | None = Field(None, description="Memory usage percentage")
    started_at: float | None = Field(None, description="Process start timestamp")
    last_seen: float = Field(
        default_factory=time.time, description="Last health check timestamp"
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "Process data model created",
            process_id=self.process_id,
            name=self.name,
            status=self.status,
            pid=self.pid,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        schema_extra = {
            "example": {
                "process_id": "fullon_bot_1",
                "name": "Trading Bot",
                "status": "running",
                "pid": 12345,
                "cpu_percent": 5.2,
                "memory_percent": 2.1,
                "started_at": 1627843661.75,
                "last_seen": 1627846261.75,
            }
        }


class BotData(BaseModel):
    """Bot data model for FastAPI WebSocket cache operations."""

    bot_id: str = Field(..., description="Bot identifier")
    user_id: int = Field(..., description="User identifier")
    exchange: str = Field(..., description="Exchange identifier")
    symbol: str | None = Field(None, description="Trading symbol")
    status: str = Field(..., description="Bot status")
    is_blocked: bool = Field(default=False, description="Bot blocking status")
    blocked_until: float | None = Field(None, description="Blocked until timestamp")
    last_activity: float = Field(
        default_factory=time.time, description="Last activity timestamp"
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "Bot data model created",
            bot_id=self.bot_id,
            user_id=self.user_id,
            exchange=self.exchange,
            status=self.status,
            is_blocked=self.is_blocked,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        schema_extra = {
            "example": {
                "bot_id": "bot_123",
                "user_id": 1,
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "status": "active",
                "is_blocked": False,
                "blocked_until": None,
                "last_activity": 1627846261.75,
            }
        }


class HealthData(BaseModel):
    """System health data model for FastAPI WebSocket cache operations."""

    status: str = Field(..., description="Overall system status")
    services: dict[str, str] = Field(..., description="Service statuses")
    timestamp: float = Field(
        default_factory=time.time, description="Health check timestamp"
    )
    uptime: float | None = Field(None, description="System uptime in seconds")
    version: str | None = Field(None, description="System version")

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        logger.debug(
            "Health data model created",
            status=self.status,
            services_count=len(self.services),
            uptime=self.uptime,
        )

    class Config:
        """Pydantic config for FastAPI integration."""

        schema_extra = {
            "example": {
                "status": "healthy",
                "services": {
                    "redis": "healthy",
                    "database": "healthy",
                    "cache": "healthy",
                },
                "timestamp": 1627846261.75,
                "uptime": 86400.0,
                "version": "1.0.0",
            }
        }
