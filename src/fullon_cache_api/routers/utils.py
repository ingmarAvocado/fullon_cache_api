"""
Router utility functions and enums for cache operations.

This module provides utility functions and enumerations used across
all cache router implementations for consistency and maintainability.
"""

from enum import Enum


class CacheOperation(Enum):
    """Enumeration of cache operations for consistent operation tracking."""

    GET_TICKER = "get_ticker"
    GET_ORDERS = "get_orders"
    GET_BOT_STATUS = "get_bot_status"
    GET_TRADES = "get_trades"
    GET_POSITIONS = "get_positions"
    GET_OHLCV = "get_ohlcv"
    GET_HEALTH = "get_health"
    STREAM_TICKERS = "stream_tickers"
    STREAM_ORDERS = "stream_orders"
    STREAM_TRADES = "stream_trades"
    STREAM_POSITIONS = "stream_positions"


def format_cache_key(exchange: str, symbol: str) -> str:
    """
    Format consistent cache keys for Redis operations.

    Args:
        exchange: Exchange name (e.g., 'binance')
        symbol: Trading pair symbol (e.g., 'BTC/USDT')

    Returns:
        Formatted cache key string (e.g., 'binance:BTC/USDT')
    """
    return f"{exchange}:{symbol}"


def normalize_exchange_name(exchange: str) -> str:
    """
    Normalize exchange name for consistent cache key format.

    Args:
        exchange: Raw exchange name

    Returns:
        Normalized exchange name (lowercase, trimmed)
    """
    return exchange.strip().lower()


def normalize_symbol_format(symbol: str) -> str:
    """
    Normalize symbol format for consistent cache operations.

    Args:
        symbol: Raw symbol string

    Returns:
        Normalized symbol format (uppercase, trimmed)
    """
    return symbol.strip().upper()


def build_cache_key_with_prefix(prefix: str, exchange: str, symbol: str) -> str:
    """
    Build cache key with operation prefix for Redis namespacing.

    Args:
        prefix: Operation prefix (e.g., 'ticker', 'orders')
        exchange: Exchange name
        symbol: Trading pair symbol

    Returns:
        Prefixed cache key (e.g., 'ticker:binance:BTC/USDT')
    """
    base_key = format_cache_key(exchange, symbol)
    return f"{prefix}:{base_key}"


def extract_base_quote_from_symbol(symbol: str) -> tuple[str, str]:
    """
    Extract base and quote currencies from trading pair symbol.

    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')

    Returns:
        Tuple of (base_currency, quote_currency)

    Raises:
        ValueError: If symbol format is invalid
    """
    if "/" not in symbol:
        raise ValueError(f"Invalid symbol format: {symbol}")

    parts = symbol.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid symbol format: {symbol}")

    base, quote = parts
    return base.strip(), quote.strip()
