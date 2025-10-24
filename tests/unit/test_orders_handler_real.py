"""Unit-ish tests for orders handler over WebSocket (real Redis)."""

import asyncio
import json
import uuid

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.redis]


def test_get_order_status_unit_real_redis():
    try:
        from fullon_cache import OrdersCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    exchange = "binance"
    order_id = f"ORD_{uuid.uuid4().hex[:6]}"

    async def _seed():
        cache = OrdersCache()
        try:
            # Minimal order dict accepted by OrdersCache
            from fullon_orm.models import Order  # type: ignore

            order = Order(
                ex_order_id=order_id,
                symbol="BTC/USDT",
                side="buy",
                order_type="limit",
                volume=0.1,
                price=50000.0,
                status="open",
                ex_id=exchange,
            )
            await cache.save_order_data(exchange, order)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/orders/unit") as ws:
        request = {
            "action": "get_order_status",
            "request_id": "u1",
            "params": {"exchange": exchange, "order_id": order_id},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["order_id"] == order_id
        assert response["result"]["exchange"] == exchange


def test_get_queue_length_unit_real_redis():
    try:
        from fullon_cache import OrdersCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    exchange = "kraken"

    async def _seed(n: int = 2):
        cache = OrdersCache()
        try:
            from fullon_orm.models import Order  # type: ignore

            for i in range(n):
                order = Order(
                    ex_order_id=f"ORD_{i}",
                    symbol="ETH/USDT",
                    side="sell",
                    order_type="limit",
                    volume=0.2,
                    price=3000.0 + i,
                    status="open",
                    ex_id=exchange,
                )
                await cache.save_order_data(exchange, order)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed(3))

    with client.websocket_connect("/ws/orders/unitq") as ws:
        request = {
            "action": "get_queue_length",
            "request_id": "u2",
            "params": {"exchange": exchange},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["exchange"] == exchange
        assert isinstance(response["result"]["queue_length"], int)
        assert response["result"]["queue_length"] >= 2
