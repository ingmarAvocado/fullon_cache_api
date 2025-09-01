"""Integration tests for orders WebSocket with REAL Redis (no mocks)."""

import asyncio
import json
import uuid

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.redis]


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
        # Best effort cleanup; tests still run if flush not possible
        pass


def test_get_order_status_not_found_real_redis():
    app = create_app()
    client = TestClient(app)
    _flush_db()

    with client.websocket_connect("/ws/orders/not_found") as ws:
        request = {
            "action": "get_order_status",
            "request_id": "not_found",
            "params": {
                "exchange": "binance",
                "order_id": f"ORD_{uuid.uuid4().hex[:6]}",
            },
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is False
        assert response["error_code"] == "ORDER_NOT_FOUND"


def test_get_order_status_real_redis():
    try:
        from fullon_cache import OrdersCache  # type: ignore
        from tests.factories.order import OrderFactory
    except Exception as e:
        pytest.skip(f"Dependencies not available: {e}")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    exchange = "binance"
    order_id = f"ORD_{uuid.uuid4().hex[:6]}"
    factory = OrderFactory()

    async def _seed():
        cache = OrdersCache()
        try:
            order = factory.create(order_id=order_id, exchange=exchange)
            await cache.save_order_data(exchange, order)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/orders/test_client") as ws:
        request = {
            "action": "get_order_status",
            "request_id": "req1",
            "params": {"exchange": exchange, "order_id": order_id},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["order_id"] == order_id
        assert response["result"]["exchange"] == exchange
        assert response["result"]["symbol"] is not None


def test_get_queue_length_real_redis():
    try:
        from fullon_cache import OrdersCache  # type: ignore
        from tests.factories.order import OrderFactory
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    exchange = "kraken"
    factory = OrderFactory()

    async def _seed(n: int = 3):
        cache = OrdersCache()
        try:
            for _ in range(n):
                order = factory.create(exchange=exchange)
                await cache.save_order_data(exchange, order)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed(3))

    with client.websocket_connect("/ws/orders/q_test") as ws:
        request = {
            "action": "get_queue_length",
            "request_id": "ql1",
            "params": {"exchange": exchange},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["exchange"] == exchange
        assert isinstance(response["result"]["queue_length"], int)
        assert response["result"]["queue_length"] >= 3


def test_stream_order_queue_real_redis():
    try:
        from fullon_cache import OrdersCache  # type: ignore
        from tests.factories.order import OrderFactory
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    exchange = "binance"
    factory = OrderFactory()

    with client.websocket_connect("/ws/orders/stream_test") as ws:
        # Start stream
        request = {
            "action": "stream_order_queue",
            "request_id": "stream1",
            "params": {"exchange": exchange},
        }
        ws.send_text(json.dumps(request))

        # Expect confirmation first
        conf = json.loads(ws.receive_text())
        assert conf["success"] is True
        assert conf["action"] == "stream_order_queue"

        # Mutate data to trigger queue length change
        async def _update():
            cache = OrdersCache()
            try:
                await asyncio.sleep(0.6)
                # Insert a few orders to increase count
                for _ in range(2):
                    order = factory.create(exchange=exchange)
                    await cache.save_order_data(exchange, order)
            finally:
                await cache._cache.close()

        loop = asyncio.get_event_loop()
        loop.create_task(_update())

        updates = []
        # Read up to 5 messages looking for a queue_update
        for _ in range(5):
            msg = json.loads(ws.receive_text())
            if msg.get("action") == "queue_update":
                updates.append(msg)
                break

        assert len(updates) >= 1
        assert updates[0]["result"]["exchange"] == exchange
        assert isinstance(updates[0]["result"]["queue_length"], int)

