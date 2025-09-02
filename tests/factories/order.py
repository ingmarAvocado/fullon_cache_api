"""Order factory for REAL Redis testing (NO MOCKS)."""

import time
import uuid

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
        o.ex_order_id = order_id
        o.exchange = exchange
        # Core order data
        o.symbol = symbol
        o.side = side
        o.volume = float(amount)
        o.price = float(price)
        o.final_volume = float(filled) if filled else None
        o.status = kwargs.get("status", "open")
        o.order_type = kwargs.get("order_type", "limit")
        o.timestamp = kwargs.get("timestamp", time.time())
        return o
