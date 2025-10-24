"""Integration tests for bots WebSocket with REAL Redis (no mocks)."""

import asyncio
import json

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.redis]


def test_get_bot_status_real_redis():
    try:
        from fullon_cache import BotCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    async def _seed():
        cache = BotCache()
        try:
            # Bot status is stored via update_bot(bot_id, data)
            await cache.update_bot(
                "BOT_001", {"feed_1": {"status": "active", "symbol": "BTC/USDT"}}
            )
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/bots/test") as ws:
        request = {
            "action": "get_bot_status",
            "request_id": "bot1",
            "params": {"bot_id": "BOT_001"},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["bot_id"] == "BOT_001"
        assert response["result"]["status"] in ("active", "unknown")
        assert "data" in response["result"]


def test_is_blocked_real_redis():
    try:
        from fullon_cache import BotCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    async def _seed():
        cache = BotCache()
        try:
            await cache.block_exchange("binance", "BTC/USDT", "BOT_001")
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/bots/blk") as ws:
        request = {
            "action": "is_blocked",
            "request_id": "blk1",
            "params": {"exchange": "binance", "symbol": "BTC/USDT"},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["exchange"] == "binance"
        assert response["result"]["symbol"] == "BTC/USDT"
        assert response["result"]["is_blocked"] is True
        assert response["result"]["blocked_by"] == "BOT_001"


def test_get_bots_real_redis():
    try:
        from fullon_cache import BotCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    async def _seed():
        cache = BotCache()
        try:
            await cache.update_bot("BOT_A", {"feed": {"status": "running"}})
            await cache.update_bot("BOT_B", {"feed": {"status": "stopped"}})
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/bots/get") as ws:
        request = {"action": "get_bots", "request_id": "gb1", "params": {}}
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        bots = response["result"]["bots"]
        assert isinstance(bots, dict)
        assert "BOT_A" in bots and "BOT_B" in bots


def test_stream_bot_status_real_redis():
    try:
        from fullon_cache import BotCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    async def _seed():
        cache = BotCache()
        try:
            await cache.update_bot("BOT_S", {"feed": {"status": "idle"}})
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/bots/stream") as ws:
        # Start stream for specific bot
        request = {
            "action": "stream_bot_status",
            "request_id": "s1",
            "params": {"bot_id": "BOT_S"},
        }
        ws.send_text(json.dumps(request))

        # Expect confirmation
        conf = json.loads(ws.receive_text())
        assert conf["success"] is True
        assert conf["action"] == "stream_bot_status"

        # Modify bot to trigger update
        async def _update():
            cache = BotCache()
            try:
                await asyncio.sleep(0.6)
                await cache.update_bot("BOT_S", {"feed": {"status": "active"}})
            finally:
                await cache._cache.close()

        loop = asyncio.get_event_loop()
        loop.create_task(_update())

        # Read a few messages to find an update
        updates = []
        for _ in range(5):
            msg = json.loads(ws.receive_text())
            if msg.get("action") == "bot_update":
                bots = msg["result"]["bots"]
                if "BOT_S" in bots:
                    updates.append(msg)
                    break

        assert len(updates) >= 1
