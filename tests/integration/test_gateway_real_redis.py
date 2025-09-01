"""Complete gateway integration tests with REAL Redis (NO MOCKS).

This test exercises multiple WebSocket endpoints sequentially to validate the
FastAPI WebSocket gateway wiring, routing, and handler behaviors using a real
Redis backend. It seeds data via fullon_cache caches and local factories.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.redis]


def _flush_db() -> None:
    try:
        from fullon_cache import BaseCache  # type: ignore

        async def _do() -> None:
            cache = BaseCache()
            async with cache._redis_context() as redis:
                await redis.flushdb()
            await cache.close()

        asyncio.get_event_loop().run_until_complete(_do())
    except Exception:
        # Best effort cleanup
        pass


def test_gateway_multi_endpoints_real_redis() -> None:
    try:
        from fullon_cache import (
            AccountCache,  # type: ignore
            OrdersCache,  # type: ignore
            OHLCVCache,  # type: ignore
        )
        from fullon_cache.tick_cache import TickCache  # type: ignore
        from tests.factories.ticker import TickerFactory
    except Exception as e:
        pytest.skip(f"Dependencies not available: {e}")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    # --- Seed TickCache ---
    async def _seed_ticker() -> None:
        cache = TickCache()
        try:
            tick = TickerFactory().create(symbol="BTC/USDT", exchange="binance", price=50123.45)
            await cache.set_ticker(tick)  # type: ignore[arg-type]
        finally:
            await cache._cache.close()

    # --- Seed AccountCache ---
    async def _seed_account() -> None:
        cache = AccountCache()
        try:
            await cache.upsert_user_account(
                123, {"USDT": {"balance": 10000.0, "available": 8500.0}}
            )
        finally:
            await cache._cache.close()

    # --- Seed OrdersCache ---
    async def _seed_orders(n: int = 2) -> None:
        cache = OrdersCache()
        try:
            for _ in range(n):
                order_id = f"ORD_{uuid.uuid4().hex[:6]}"
                # Save minimal order representation using cache helper
                await cache.save_order_data(
                    "binance",
                    {
                        "ex_order_id": order_id,
                        "symbol": "BTC/USDT",
                        "side": "buy",
                        "price": 50000.0,
                        "volume": 0.1,
                        "status": "open",
                        "timestamp": time.time(),
                    },
                )
        finally:
            await cache._cache.close()

    # --- Seed OHLCVCache ---
    async def _seed_ohlcv() -> None:
        cache = OHLCVCache()
        try:
            start = int(time.time()) - 60 * 10
            bars: list[list[float]] = []
            ts = start
            price = 100.0
            for i in range(15):
                o = price
                h = o * 1.01
                l = o * 0.99
                c = o * 1.002
                v = 100 + i
                bars.append([float(ts), float(o), float(h), float(l), float(c), float(v)])
                ts += 60
                price = c
            await cache.update_ohlcv_bars("BTC/USDT", "1m", bars)
        finally:
            await cache._cache.close()

    # Perform seeding
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_seed_ticker())
    loop.run_until_complete(_seed_account())
    loop.run_until_complete(_seed_orders(2))
    loop.run_until_complete(_seed_ohlcv())

    # --- Tickers endpoint ---
    with client.websocket_connect("/ws/tickers/gateway") as ws:
        req = {
            "action": "get_ticker",
            "request_id": "t1",
            "params": {"exchange": "binance", "symbol": "BTC/USDT"},
        }
        ws.send_text(json.dumps(req))
        resp = json.loads(ws.receive_text())
        assert resp["success"] is True
        assert resp["action"] == "get_ticker"
        assert resp["result"]["symbol"] == "BTC/USDT"

    # --- Accounts endpoint (balance) ---
    with client.websocket_connect("/ws/accounts/gateway") as ws:
        req = {
            "action": "get_balance",
            "request_id": "a1",
            "params": {"user_id": 123, "currency": "USDT"},
        }
        ws.send_text(json.dumps(req))
        resp = json.loads(ws.receive_text())
        assert resp["success"] is True
        assert resp["result"]["user_id"] == 123
        assert resp["result"]["currency"] == "USDT"

    # --- Orders endpoint (queue length) ---
    with client.websocket_connect("/ws/orders/gateway") as ws:
        req = {
            "action": "get_queue_length",
            "request_id": "o1",
            "params": {"exchange": "binance"},
        }
        ws.send_text(json.dumps(req))
        resp = json.loads(ws.receive_text())
        assert resp["success"] is True
        assert isinstance(resp["result"]["queue_length"], int)
        assert resp["result"]["queue_length"] >= 2

    # --- OHLCV endpoint (latest bars) ---
    with client.websocket_connect("/ws/ohlcv/gateway") as ws:
        req = {
            "action": "get_latest_ohlcv_bars",
            "request_id": "h1",
            "params": {"symbol": "BTC/USDT", "timeframe": "1m", "count": 5},
        }
        ws.send_text(json.dumps(req))
        resp = json.loads(ws.receive_text())
        assert resp["success"] is True
        assert len(resp["result"]["bars"]) == 5

    # --- Process endpoint (system health) ---
    with client.websocket_connect("/ws/process/gateway") as ws:
        req = {
            "action": "get_system_health",
            "request_id": "p1",
            "params": {},
        }
        ws.send_text(json.dumps(req))
        resp = json.loads(ws.receive_text())
        assert resp["success"] is True
        assert isinstance(resp.get("result"), dict)

