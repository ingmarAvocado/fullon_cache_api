"""Real Redis + WebSocket example for tickers.

Prereqs:
- Run the FastAPI app: `make dev` (ws://127.0.0.1:8000)
- Configure Redis via `.env` (REDIS_* or CACHE_* vars)

What it does:
- Seeds a real ticker in Redis via fullon_cache.TickCache
- Connects to `/ws/tickers/{client}` and runs:
  - get_ticker
  - stream_tickers (while updating Redis to trigger updates)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from decimal import Decimal

import websockets


async def seed_ticker(
    symbol: str = "BTC/USDT", exchange: str = "binance", price: float = 50000.0
) -> None:
    from fullon_cache import TickCache  # type: ignore
    from fullon_orm.models import Tick  # type: ignore

    async with TickCache() as cache:  # type: ignore[call-arg]
        tick = Tick(
            symbol=symbol,
            exchange=exchange,
            price=Decimal(str(price)),
            volume=Decimal("1234.56"),
            time=time.time(),
            bid=Decimal(str(price - 1)),
            ask=Decimal(str(price + 1)),
            last=Decimal(str(price)),
            change_24h=Decimal("2.5"),
        )
        await cache.set_ticker(tick)  # type: ignore[arg-type]


async def update_prices(symbol: str, exchange: str, prices: list[float]) -> None:
    from fullon_cache import TickCache  # type: ignore
    from fullon_orm.models import Tick  # type: ignore

    for p in prices:
        async with TickCache() as cache:  # type: ignore[call-arg]
            from decimal import Decimal as D

            tick = Tick(
                symbol=symbol,
                exchange=exchange,
                price=D(str(p)),
                volume=D("1250.0"),
                time=time.time(),
                bid=D(str(p - 0.5)),
                ask=D(str(p + 0.5)),
                last=D(str(p)),
            )
            await cache.set_ticker(tick)  # type: ignore[arg-type]
        await asyncio.sleep(1.0)


async def main() -> None:
    symbol = os.environ.get("EX_SYMBOL", "BTC/USDT")
    exchange = os.environ.get("EX_EXCHANGE", "binance")
    client = os.environ.get("EX_CLIENT", "demo_client")
    ws_url = os.environ.get("EX_WS_URL", "ws://127.0.0.1:8000/ws/tickers/") + client

    print("📊 Seeding real ticker in Redis…")
    await seed_ticker(symbol, exchange)

    async with websockets.connect(ws_url) as ws:
        print("✅ Connected:", ws_url)
        # get_ticker
        req = {
            "action": "get_ticker",
            "request_id": "get1",
            "params": {"exchange": exchange, "symbol": symbol},
        }
        await ws.send(json.dumps(req))
        resp = json.loads(await ws.recv())
        print("GET TICKER:", resp)

        # stream_tickers
        req = {
            "action": "stream_tickers",
            "request_id": "s1",
            "params": {"exchange": exchange, "symbols": [symbol]},
        }
        await ws.send(json.dumps(req))
        conf = json.loads(await ws.recv())
        print("STREAM CONF:", conf)

        # Drive updates in the background
        asyncio.create_task(
            update_prices(symbol, exchange, [50050.0, 50075.5, 50110.0])
        )

        # Read a few updates
        got = 0
        while got < 3:
            upd = json.loads(await ws.recv())
            if upd.get("action") == "ticker_update":
                print("UPDATE:", upd)
                got += 1


if __name__ == "__main__":
    asyncio.run(main())
