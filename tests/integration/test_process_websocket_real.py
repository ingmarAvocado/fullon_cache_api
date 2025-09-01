"""Integration tests for Process WebSocket with REAL Redis (no mocks)."""

from __future__ import annotations

import asyncio
import json

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
        # Best effort cleanup; tests still run if flush not possible
        pass


def test_get_system_health_real_redis() -> None:
    try:
        from fullon_cache import ProcessCache  # type: ignore  # noqa: F401
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    with client.websocket_connect("/ws/process/integration") as ws:
        request = {
            "action": "get_system_health",
            "request_id": "req1",
            "params": {},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["action"] == "get_system_health"
        assert isinstance(response.get("result"), dict)


def test_stream_process_health_real_redis() -> None:
    try:
        from fullon_cache import ProcessCache  # type: ignore  # noqa: F401
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    with client.websocket_connect("/ws/process/stream_integration") as ws:
        # Start stream
        request = {
            "action": "stream_process_health",
            "request_id": "s1",
            "params": {},
        }
        ws.send_text(json.dumps(request))

        # Expect confirmation
        conf = json.loads(ws.receive_text())
        assert conf["success"] is True
        assert conf["action"] == "stream_process_health"

        # Keep this integration test light: only validate stream setup

