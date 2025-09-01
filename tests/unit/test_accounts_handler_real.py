"""Unit-ish tests for accounts handler over WebSocket (real Redis)."""

import asyncio
import json

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.redis]


def _flush_db():
    try:
        from fullon_cache import BaseCache  # type: ignore

        async def _do():
            cache = BaseCache()
            async with cache._redis_context() as redis:
                await redis.flushdb()
            await cache.close()

        asyncio.get_event_loop().run_until_complete(_do())
    except Exception:
        pass


def test_get_balance_unit_real_redis():
    try:
        from fullon_cache import AccountCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    async def _seed():
        cache = AccountCache()
        try:
            await cache.upsert_user_account(111, {"USDT": {"balance": 200.0, "available": 150.0}})
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/accounts/unit") as ws:
        request = {
            "action": "get_balance",
            "request_id": "ab1",
            "params": {"user_id": 111, "currency": "USDT"},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["user_id"] == 111
        assert response["result"]["currency"] == "USDT"
        assert response["result"]["total_balance"] == 200.0
        assert response["result"]["available_balance"] == 150.0
        assert response["result"]["reserved_balance"] == 50.0


def test_get_positions_unit_real_redis():
    try:
        from fullon_cache import AccountCache  # type: ignore
        from fullon_orm.models import Position  # type: ignore
    except Exception:
        pytest.skip("fullon_cache or fullon_orm not available")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    async def _seed():
        cache = AccountCache()
        try:
            positions = [
                Position(symbol="BTC/USDT", volume=0.3, price=50000.0, ex_id="1", side="long"),
                # ORM disallows negative volume; use side='short' with positive volume
                Position(symbol="ETH/USDT", volume=1.2, price=3000.0, ex_id="1", side="short"),
            ]
            # Store positions by exchange_id (1), not user_id
            await cache.upsert_positions(1, positions)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/accounts/unitpos") as ws:
        request = {
            "action": "get_positions",
            "request_id": "ap1",
            "params": {"exchange": "1"},  # Request positions by exchange, not user_id
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["exchange"] == "1"
        assert response["result"]["count"] >= 2
        symbols = {p["symbol"] for p in response["result"]["positions"]}
        assert {"BTC/USDT", "ETH/USDT"}.issubset(symbols)
