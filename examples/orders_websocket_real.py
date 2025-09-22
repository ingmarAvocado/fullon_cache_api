"""Real Redis + WebSocket example for orders.

Seeds orders in Redis and demonstrates queue length queries and streaming.

Prereqs:
- `make dev` running (ws://127.0.0.1:8000)
- Redis configured via `.env`
"""

from __future__ import annotations

import asyncio
import json
import os
import time

import websockets


async def seed_orders(exchange: str = "binance", count: int = 3) -> None:
    from fullon_cache import OrdersCache  # type: ignore
    from fullon_orm.models import Order  # type: ignore

    async with OrdersCache() as cache:  # type: ignore[call-arg]
        for i in range(count):
            o = Order()  # type: ignore[call-arg]
            o.ex_order_id = f"ORD_DEMO_{i}"
            o.exchange = exchange
            o.symbol = "BTC/USDT"
            o.side = "buy"
            o.volume = 0.1
            o.price = 50000.0 + i
            o.status = "open"
            await cache.save_order_data(exchange, o)  # type: ignore[arg-type]


async def add_more_orders(exchange: str = "binance", count: int = 2) -> None:
    from fullon_cache import OrdersCache  # type: ignore
    from fullon_orm.models import Order  # type: ignore

    await asyncio.sleep(1.0)
    async with OrdersCache() as cache:  # type: ignore[call-arg]
        for i in range(count):
            o = Order()  # type: ignore[call-arg]
            o.ex_order_id = f"ORD_MORE_{int(time.time())}_{i}"
            o.exchange = exchange
            o.symbol = "BTC/USDT"
            o.side = "buy"
            o.volume = 0.1
            o.price = 50500.0 + i
            o.status = "open"
            await cache.save_order_data(exchange, o)  # type: ignore[arg-type]


async def main() -> None:
    exchange = os.environ.get("EX_EXCHANGE", "binance")
    client = os.environ.get("EX_CLIENT", "demo_orders")
    ws_url = os.environ.get("EX_WS_URL", "ws://127.0.0.1:8000/ws/orders/") + client

    print("📦 Seeding real orders in Redis…")
    await seed_orders(exchange, 3)

    async with websockets.connect(ws_url) as ws:
        print("✅ Connected:", ws_url)
        # get_queue_length
        req = {
            "action": "get_queue_length",
            "request_id": "ql1",
            "params": {"exchange": exchange},
        }
        await ws.send(json.dumps(req))
        resp = json.loads(await ws.recv())
        print("QUEUE LENGTH:", resp)

        # stream_order_queue
        req = {
            "action": "stream_order_queue",
            "request_id": "s1",
            "params": {"exchange": exchange},
        }
        await ws.send(json.dumps(req))
        conf = json.loads(await ws.recv())
        print("STREAM CONF:", conf)

        # Drive updates by adding more orders
        asyncio.create_task(add_more_orders(exchange, 2))

        got = 0
        while got < 2:
            upd = json.loads(await ws.recv())
            if upd.get("action") == "queue_update":
                print("UPDATE:", upd)
                got += 1


if __name__ == "__main__":
    asyncio.run(main())
