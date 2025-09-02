"""Unit tests for OHLCVWebSocketHandler without external cache dependency."""

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
    from src.fullon_cache_api.handlers.ohlcv_handler import OHLCVWebSocketHandler

    ws = FakeWS()
    h = OHLCVWebSocketHandler()
    await h.route_ohlcv_message(ws, "not-json", connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "MALFORMED_MESSAGE"


async def test_route_invalid_operation_not_implemented():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.ohlcv_handler import OHLCVWebSocketHandler

    ws = FakeWS()
    h = OHLCVWebSocketHandler()
    msg = {"action": "nope", "request_id": "r1", "params": {}}
    await h.route_ohlcv_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_OPERATION"


async def test_get_latest_ohlcv_bars_missing_params_invalid_params():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.ohlcv_handler import OHLCVWebSocketHandler

    ws = FakeWS()
    h = OHLCVWebSocketHandler()
    msg = {"action": "get_latest_ohlcv_bars", "request_id": "r1", "params": {}}
    await h.route_ohlcv_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_PARAMS"


async def test_stream_ohlcv_confirmation_and_cleanup():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.ohlcv_handler import OHLCVWebSocketHandler

    ws = FakeWS()
    h = OHLCVWebSocketHandler()

    async def fake_stream(ws, request_id, symbol, timeframe, stream_key):  # type: ignore[no-untyped-def]
        msg = {
            "request_id": request_id,
            "action": "ohlcv_update",
            "result": {
                "stream_key": stream_key,
                "symbol": symbol,
                "timeframe": timeframe,
                "bar": [1700000000.0, 1.0, 2.0, 0.9, 1.5, 100.0],
            },
        }
        await ws.send_text(json.dumps(msg))

    h._stream_ohlcv_updates = fake_stream  # type: ignore[attr-defined]

    msg = {
        "action": "stream_ohlcv",
        "request_id": "r1",
        "params": {"symbol": "BTC/USDT", "timeframe": "1m"},
    }
    await h.route_ohlcv_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is True
    assert resp["action"] == "stream_ohlcv"
    key = resp["stream_key"]
    assert key in h.streaming_tasks

    await h.cleanup_connection("c1")
    assert key not in h.streaming_tasks
