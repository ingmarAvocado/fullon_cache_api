"""Order factory for REAL Redis testing (NO MOCKS)."""

import time
import uuid
from decimal import Decimal

try:  # type: ignore
    from fullon_orm.models import Order  # type: ignore
except Exception:  # pragma: no cover - test env dependent
    Order = object  # type: ignore


class OrderFactory:
    """Create realistic order data for REAL Redis cache testing."""

    def __init__(self) -> None:
        self.counter = 0

    def create(
        self,
        symbol: str = "BTC/USDT",
        exchange: str = "binance",
        side: str = "buy",
        amount: float = 1.0,
        price: float = 50000.0,
        **kwargs,
    ):
        """Create realistic order with proper calculations."""
        self.counter += 1
        order_id = kwargs.get("order_id", f"ORD_{uuid.uuid4().hex[:8]}")
        filled = kwargs.get("filled", 0.0)
        remaining = amount - float(filled)

        if Order is object:  # pragma: no cover - missing ORM
            # Fallback minimal structure for environments without fullon_orm
            return {
                "ex_order_id": order_id,
                "symbol": symbol,
                "exchange": exchange,
                "side": side,
                "volume": float(amount),
                "price": float(price),
                "final_volume": float(filled) if filled else None,
                "remaining": float(remaining),
                "status": kwargs.get("status", "open"),
                "order_type": kwargs.get("order_type", "limit"),
                "timestamp": kwargs.get("timestamp", time.time()),
            }

        o = Order()  # type: ignore[call-arg]
        # Common/exchange identifiers
        setattr(o, "ex_order_id", order_id)
        setattr(o, "exchange", exchange)
        # Core order data
        setattr(o, "symbol", symbol)
        setattr(o, "side", side)
        setattr(o, "volume", float(amount))
        setattr(o, "price", float(price))
        setattr(o, "final_volume", float(filled) if filled else None)
        setattr(o, "status", kwargs.get("status", "open"))
        setattr(o, "order_type", kwargs.get("order_type", "limit"))
        setattr(o, "timestamp", kwargs.get("timestamp", time.time()))
        return o

