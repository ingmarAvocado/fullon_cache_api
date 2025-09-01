"""Ticker factory for REAL Redis testing (NO MOCKS)."""

import time
from decimal import Decimal

try:
    from fullon_orm.models import Tick  # type: ignore
except Exception:  # pragma: no cover - optional at import time
    Tick = None  # type: ignore


class TickerFactory:
    """Create realistic ticker data for REAL Redis cache testing."""

    def __init__(self) -> None:
        self.counter = 0

    def create(
        self,
        symbol: str = "BTC/USDT",
        exchange: str = "binance",
        price: float = 50000.0,
        volume: float = 1234.56,
        **kwargs,
    ):
        self.counter += 1
        spread = price * 0.0001
        bid = kwargs.get("bid", price - spread)
        ask = kwargs.get("ask", price + spread)

        if Tick is None:
            # Minimal stand-in dict for environments without fullon_orm
            return {
                "symbol": symbol,
                "exchange": exchange,
                "price": price,
                "volume": volume,
                "time": kwargs.get("time", time.time()),
                "bid": bid,
                "ask": ask,
                "last": price,
            }

        # Create ORM Tick using supported constructor args (no extra kwargs)
        return Tick(
            symbol=symbol,
            exchange=exchange,
            price=float(price),
            volume=float(volume),
            time=kwargs.get("time", time.time()),
            bid=float(bid),
            ask=float(ask),
            last=float(price),
        )

    def create_batch(
        self,
        count: int = 5,
        exchange: str = "binance",
        base_prices: list[float] | None = None,
        **kwargs,
    ):
        symbols = [
            "BTC/USDT",
            "ETH/USDT",
            "BNB/USDT",
            "ADA/USDT",
            "XRP/USDT",
            "DOT/USDT",
            "LINK/USDT",
            "LTC/USDT",
            "BCH/USDT",
            "UNI/USDT",
        ]

        if not base_prices:
            base_prices = [50000, 3000, 500, 1, 0.5, 25, 15, 150, 300, 8]

        items = []
        for i in range(count):
            symbol = symbols[i % len(symbols)]
            price = base_prices[i % len(base_prices)]
            items.append(
                self.create(
                    symbol=symbol,
                    exchange=exchange,
                    price=price,
                    volume=1000 + (i * 100),
                    **kwargs,
                )
            )
        return items
