"""Trade factory for REAL Redis testing (NO MOCKS)."""

from __future__ import annotations

import time
from typing import Any

try:  # type: ignore
    from fullon_orm.models import Trade  # type: ignore
except Exception:  # pragma: no cover - test env dependent
    Trade = None  # type: ignore


class TradeFactory:
    """Create realistic trade data for REAL Redis cache testing.

    Produces fullon_orm Trade models when available; tests that depend on
    fullon_orm will skip if the dependency is missing in the environment.
    """

    def create(
        self,
        symbol: str = "BTC/USDT",
        exchange: str = "binance",
        side: str = "buy",
        volume: float = 0.1,
        price: float = 50000.0,
        trade_id: int | None = None,
        uid: int | None = 1,
        ex_id: int | None = 1,
        **kwargs: Any,
    ):
        """Create a realistic trade model instance.

        Returns a Trade model from fullon_orm when available.
        """
        if Trade is None:  # pragma: no cover - missing ORM
            # Minimal structure only if ORM is missing; pushing to cache requires ORM
            return {
                "trade_id": trade_id or int(time.time() * 1000) % 1000000,
                "symbol": symbol,
                "exchange": exchange,
                "side": side,
                "volume": float(volume),
                "price": float(price),
                "time": kwargs.get("time", time.time()),
                "uid": uid or 1,
                "ex_id": ex_id or 1,
            }

        # Create ORM Trade instance
        t = Trade()  # type: ignore[call-arg]
        t.trade_id = trade_id or int(time.time() * 1000) % 1000000
        t.symbol = symbol
        t.side = side
        t.volume = float(volume)
        t.price = float(price)
        t.uid = uid or 1
        t.ex_id = ex_id or 1
        t.time = kwargs.get("time", time.time())
        # Optional analytics fields
        t.cost = kwargs.get("cost", float(volume) * float(price))
        t.fee = kwargs.get("fee", 0.0)
        return t
