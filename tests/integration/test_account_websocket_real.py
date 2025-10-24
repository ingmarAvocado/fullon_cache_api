"""Integration tests for account WebSocket with REAL Redis (no mocks)."""

import asyncio
import json

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.redis]


def test_get_balance_real_redis():
    try:
        from fullon_cache import AccountCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)

    # Seed balance via AccountCache
    async def _seed():
        cache = AccountCache()
        try:
            await cache.upsert_user_account(
                123, {"USDT": {"balance": 10000.0, "available": 8500.0}}
            )
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    # Request via WebSocket
    with client.websocket_connect("/ws/accounts/bal_test") as ws:
        request = {
            "action": "get_balance",
            "request_id": "bal1",
            "params": {"user_id": 123, "currency": "USDT"},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["result"]["user_id"] == 123
        assert response["result"]["currency"] == "USDT"
        assert response["result"]["total_balance"] == 10000.0
        assert response["result"]["available_balance"] == 8500.0
        assert response["result"]["reserved_balance"] == 1500.0


def test_get_positions_real_redis():
    try:
        from fullon_cache import AccountCache  # type: ignore
        from fullon_orm.models import Position  # type: ignore
    except Exception:
        pytest.skip("fullon_cache or fullon_orm not available")

    app = create_app()
    client = TestClient(app)

    # Seed positions
    async def _seed():
        cache = AccountCache()
        try:
            positions = [
                Position(
                    symbol="BTC/USDT",
                    volume=0.2,
                    price=50000.0,
                    cost=10000.0,
                    fee=5.0,
                    ex_id="1",
                ),
                Position(
                    symbol="ETH/USDT",
                    volume=1.0,
                    price=3000.0,
                    cost=3000.0,
                    fee=3.0,
                    ex_id="1",
                ),
            ]
            # Store positions by exchange_id (1), not user_id
            await cache.upsert_positions(1, positions)
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/accounts/pos_test") as ws:
        request = {
            "action": "get_positions",
            "request_id": "pos1",
            "params": {"exchange": "1"},  # Request positions by exchange, not user_id
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert (
            response["result"]["user_id"] is None
        )  # No user_id in exchange-centric approach
        assert response["result"]["count"] >= 2
        symbols = {p["symbol"] for p in response["result"]["positions"]}
        assert {"BTC/USDT", "ETH/USDT"}.issubset(symbols)


def test_stream_positions_real_redis():
    try:
        from fullon_cache import AccountCache  # type: ignore
        from fullon_orm.models import Position  # type: ignore
    except Exception:
        pytest.skip("fullon_cache or fullon_orm not available")

    app = create_app()
    client = TestClient(app)

    user_id = 789

    async def _seed_initial():
        cache = AccountCache()
        try:
            # Store positions by exchange_id (1), not user_id
            await cache.upsert_positions(
                1,  # exchange_id
                [
                    Position(
                        symbol="BTC/USDT",
                        volume=0.1,
                        price=50000.0,
                        cost=5000.0,
                        fee=5.0,
                        ex_id="1",
                    )
                ],
            )
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed_initial())

    with client.websocket_connect("/ws/accounts/stream_test") as ws:
        # Start stream
        request = {
            "action": "stream_positions",
            "request_id": "stream1",
            "params": {"exchange": "1"},  # Stream positions by exchange, not user_id
        }
        ws.send_text(json.dumps(request))

        # Expect confirmation first
        conf = json.loads(ws.receive_text())
        assert conf["success"] is True
        assert conf["action"] == "stream_positions"

        # Modify position after stream starts to generate an update
        async def _update():
            cache = AccountCache()
            try:
                await asyncio.sleep(0.6)
                # Update positions by exchange_id (1)
                await cache.upsert_positions(
                    1,  # exchange_id
                    [
                        Position(
                            symbol="BTC/USDT",
                            volume=0.2,
                            price=50010.0,
                            cost=10002.0,
                            fee=5.0,
                            ex_id="1",
                        )
                    ],
                )
            finally:
                await cache._cache.close()

        loop = asyncio.get_event_loop()
        loop.create_task(_update())

        updates = []
        for _ in range(5):
            msg = json.loads(ws.receive_text())
            if msg.get("action") == "position_update":
                updates.append(msg)
                break

        assert len(updates) >= 1
        # In exchange-centric approach, user_id is not relevant for position updates
        assert updates[0]["result"]["user_id"] is None
        assert updates[0]["result"]["exchange"] == "1"
        assert updates[0]["result"]["symbol"] == "BTC/USDT"
