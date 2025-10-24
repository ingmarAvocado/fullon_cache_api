"""Unit-ish tests for bots handler over WebSocket (real Redis)."""

import asyncio
import json

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.redis]


def test_get_bots_unit_real_redis():
    try:
        from fullon_cache import BotCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    async def _seed():
        cache = BotCache()
        try:
            await cache.update_bot("BOT_X", {"feed": {"status": "running"}})
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/bots/unit") as ws:
        request = {"action": "get_bots", "request_id": "ub1", "params": {}}
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert "BOT_X" in response["result"]["bots"]


def test_is_blocked_unit_real_redis():
    try:
        from fullon_cache import BotCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    async def _seed():
        cache = BotCache()
        try:
            await cache.block_exchange("binance", "BTC/USDT", "BOT_X")
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/bots/unitblk") as ws:
        request = {
            "action": "is_blocked",
            "request_id": "ub2",
            "params": {"exchange": "binance", "symbol": "BTC/USDT"},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["is_blocked"] is True
        assert response["result"]["blocked_by"] == "BOT_X"
