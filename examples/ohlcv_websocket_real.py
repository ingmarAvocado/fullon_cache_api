"""Real Redis + WebSocket example for OHLCV.

Seeds OHLCV bars and demonstrates latest-bars query and streaming updates.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import List

import websockets


def make_bars(start_ts: int, count: int = 5, base: float = 100.0) -> List[List[float]]:
    bars: List[List[float]] = []
    ts = start_ts
    price = base
    for i in range(count):
        o = price
        h = o * 1.01
        l = o * 0.99
        c = o * 1.002
        v = 100 + i
        bars.append([float(ts), float(o), float(h), float(l), float(c), float(v)])
        ts += 60
        price = c
    return bars


async def seed_ohlcv(symbol: str, timeframe: str) -> None:
    try:
        from fullon_cache import OHLCVCache  # type: ignore
    except Exception:
        from fullon_cache.ohlcv_cache import OHLCVCache  # type: ignore

    async with OHLCVCache() as cache:  # type: ignore[call-arg]
        start = int(time.time()) - 60 * 10
        bars = make_bars(start, count=10, base=100.0)
        await cache.update_ohlcv_bars(symbol, timeframe, bars)


async def append_bar(symbol: str, timeframe: str) -> None:
    await asyncio.sleep(1.0)
    try:
        from fullon_cache import OHLCVCache  # type: ignore
    except Exception:
        from fullon_cache.ohlcv_cache import OHLCVCache  # type: ignore

    async with OHLCVCache() as cache:  # type: ignore[call-arg]
        bars = make_bars(int(time.time()), count=1, base=101.0)
        await cache.update_ohlcv_bars(symbol, timeframe, bars)


async def main() -> None:
    symbol = os.environ.get("EX_SYMBOL", "BTC/USDT")
    timeframe = os.environ.get("EX_TIMEFRAME", "1m")
    client = os.environ.get("EX_CLIENT", "demo_ohlcv")
    ws_url = os.environ.get("EX_WS_URL", "ws://127.0.0.1:8000/ws/ohlcv/") + client

    print("📈 Seeding OHLCV bars…")
    await seed_ohlcv(symbol, timeframe)

    async with websockets.connect(ws_url) as ws:
        print("✅ Connected:", ws_url)
        # get_latest_ohlcv_bars
        req = {
            "action": "get_latest_ohlcv_bars",
            "request_id": "h1",
            "params": {"symbol": symbol, "timeframe": timeframe, "count": 5},
        }
        await ws.send(json.dumps(req))
        resp = json.loads(await ws.recv())
        print("LATEST BARS:", resp)

        # stream_ohlcv
        req = {
            "action": "stream_ohlcv",
            "request_id": "s1",
            "params": {"symbol": symbol, "timeframe": timeframe},
        }
        await ws.send(json.dumps(req))
        conf = json.loads(await ws.recv())
        print("STREAM CONF:", conf)

        # Trigger an update
        asyncio.create_task(append_bar(symbol, timeframe))

        got = 0
        while got < 1:
            upd = json.loads(await ws.recv())
            if upd.get("action") == "ohlcv_update":
                print("UPDATE:", upd)
                got += 1


if __name__ == "__main__":
    asyncio.run(main())

