"""Account factories for REAL Redis testing (NO MOCKS)."""

import time
from decimal import Decimal

from fullon_orm.models import Position  # type: ignore


class AccountFactory:
    """Create realistic account balance payloads."""

    def create_balance(
        self,
        user_id: int,
        currency: str = "USDT",
        total_balance: float = 10000.0,
        available_balance: float | None = None,
        *,
        timestamp: float | None = None,
    ) -> dict:
        if available_balance is None:
            available_balance = total_balance * 0.85
        reserved = total_balance - available_balance
        return {
            "user_id": user_id,
            "currency": currency,
            "balance": float(total_balance),
            "available": float(available_balance),
            "reserved": float(reserved),
            "timestamp": timestamp or time.time(),
        }


class PositionFactory:
    """Create realistic positions for AccountCache tests."""

    def create(
        self,
        user_id: int,
        symbol: str = "BTC/USDT",
        *,
        volume: float = 0.1,
        price: float = 50000.0,
        ex_id: str | int = "1",
        timestamp: float | None = None,
    ) -> Position:
        return Position(
            symbol=symbol,
            volume=Decimal(str(volume)),
            price=Decimal(str(price)),
            cost=Decimal(str(price * abs(volume))),
            fee=Decimal("0"),
            timestamp=timestamp or time.time(),
            ex_id=str(ex_id),
        )

    def create_batch(
        self,
        *,
        count: int = 3,
        user_id: int = 1,
        symbols: list[str] | None = None,
        price: float = 50000.0,
        ex_id: str | int = "1",
    ) -> list[Position]:
        symbols = symbols or ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
        out: list[Position] = []
        for i in range(count):
            out.append(
                self.create(
                    user_id=user_id,
                    symbol=symbols[i % len(symbols)],
                    volume=0.1 + i * 0.05,
                    price=price + i * 10,
                    ex_id=ex_id,
                )
            )
        return out
