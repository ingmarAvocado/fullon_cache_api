"""Unit-ish tests for Process handler over WebSocket (real Redis)."""

from __future__ import annotations

import asyncio
import json

import pytest
from fullon_cache_api.main import create_app
from starlette.testclient import TestClient

pytestmark = [pytest.mark.redis]


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


def test_get_system_health_unit_real_redis() -> None:
    try:
        from fullon_cache import ProcessCache  # type: ignore  # noqa: F401
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    with client.websocket_connect("/ws/process/unit") as ws:
        request = {
            "action": "get_system_health",
            "request_id": "syshealth1",
            "params": {},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["action"] == "get_system_health"
        assert isinstance(response.get("result"), dict)


def test_get_active_processes_unit_real_redis() -> None:
    try:
        from fullon_cache import ProcessCache  # type: ignore
        from fullon_cache.process_cache import ProcessType  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    async def _seed() -> None:
        cache = ProcessCache()
        try:
            # Use supported signature with Enum process type
            await cache.register_process(
                process_type=ProcessType.BOT, component="Worker A"
            )
            await cache.register_process(
                process_type=ProcessType.BOT, component="Worker B"
            )
        finally:
            await cache._cache.close()

    asyncio.get_event_loop().run_until_complete(_seed())

    with client.websocket_connect("/ws/process/unit2") as ws:
        request = {
            "action": "get_active_processes",
            "request_id": "proc1",
            "params": {},
        }
        ws.send_text(json.dumps(request))
        response = json.loads(ws.receive_text())

        assert response["success"] is True
        assert response["action"] == "get_active_processes"
        items = response["result"].get("processes")
        assert isinstance(items, list)
        assert len(items) >= 2


def test_stream_process_health_unit_real_redis() -> None:
    try:
        from fullon_cache import ProcessCache  # type: ignore
    except Exception:
        pytest.skip("fullon_cache not available in environment")

    app = create_app()
    client = TestClient(app)
    _flush_db()

    with client.websocket_connect("/ws/process/stream_unit") as ws:
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

        # Mutate data to trigger an update: register a new process
        async def _mutate() -> None:
            cache = ProcessCache()
            try:
                await asyncio.sleep(0.6)
                await cache.register_process(
                    process_type=ProcessType.BOT, component="Worker C"
                )
            finally:
                await cache._cache.close()

        loop = asyncio.get_event_loop()
        task = loop.create_task(_mutate())

        updates: list[dict] = []
        for _ in range(6):
            msg = json.loads(ws.receive_text())
            if msg.get("action") == "process_health_update":
                updates.append(msg)
                break

        assert len(updates) >= 1
        # Ensure background mutation task is finalized to avoid warnings
        try:
            loop.run_until_complete(task)
        except Exception:
            pass
        upd = updates[0]["result"]
        assert isinstance(upd.get("active_processes"), int)
        assert "timestamp" in upd
