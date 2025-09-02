"""Unit tests for OrdersWebSocketHandler without external cache dependency."""

from __future__ import annotations

import asyncio
import json
import sys
import types
from typing import Any, List


def _install_fake_fullon_log() -> None:
    if "fullon_log" in sys.modules:
        return
    m = types.ModuleType("fullon_log")

    class _Dummy:
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return None

            return _noop

    def get_component_logger(name: str) -> _Dummy:  # type: ignore
        return _Dummy()

    m.get_component_logger = get_component_logger  # type: ignore[attr-defined]
    sys.modules["fullon_log"] = m


class FakeWS:
    def __init__(self) -> None:
        self.sent: List[str] = []

    async def send_text(self, text: str) -> None:
        self.sent.append(text)


def _last_json(ws: FakeWS) -> dict[str, Any]:
    assert ws.sent, "no messages sent"
    return json.loads(ws.sent[-1])


async def test_route_invalid_json_malformed_message():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.order_handler import OrdersWebSocketHandler

    ws = FakeWS()
    h = OrdersWebSocketHandler()
    await h.route_order_message(ws, "not-json", connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "MALFORMED_MESSAGE"


async def test_route_invalid_operation_not_implemented():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.order_handler import OrdersWebSocketHandler

    ws = FakeWS()
    h = OrdersWebSocketHandler()
    msg = {"action": "nope", "request_id": "r1", "params": {}}
    await h.route_order_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_OPERATION"


async def test_get_order_status_missing_params_invalid_params():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.order_handler import OrdersWebSocketHandler

    ws = FakeWS()
    h = OrdersWebSocketHandler()
    msg = {"action": "get_order_status", "request_id": "r1", "params": {}}
    await h.route_order_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_PARAMS"


async def test_get_queue_length_missing_params_invalid_params():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.order_handler import OrdersWebSocketHandler

    ws = FakeWS()
    h = OrdersWebSocketHandler()
    msg = {"action": "get_queue_length", "request_id": "r1", "params": {}}
    await h.route_order_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_PARAMS"


async def test_stream_order_queue_confirmation_and_cleanup():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.order_handler import OrdersWebSocketHandler

    ws = FakeWS()
    h = OrdersWebSocketHandler()

    async def fake_stream(ws, request_id, exchange, stream_key):  # type: ignore[no-untyped-def]
        msg = {
            "request_id": request_id,
            "action": "queue_update",
            "result": {
                "stream_key": stream_key,
                "exchange": exchange,
                "queue_length": 1,
                "timestamp": 1700000000.0,
            },
        }
        await ws.send_text(json.dumps(msg))

    h._stream_queue_length = fake_stream  # type: ignore[attr-defined]

    msg = {
        "action": "stream_order_queue",
        "request_id": "r1",
        "params": {"exchange": "binance"},
    }
    await h.route_order_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is True
    assert resp["action"] == "stream_order_queue"
    key = resp["stream_key"]
    assert key in h.streaming_tasks

    await h.cleanup_connection("c1")
    assert key not in h.streaming_tasks
