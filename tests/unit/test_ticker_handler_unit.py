"""Unit tests for TickerWebSocketHandler without external cache dependency.

Covers validation errors, not-implemented routes, stream confirmation, and
cleanup behavior using a fake WebSocket and monkeypatched internals.
"""

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
    from src.fullon_cache_api.handlers.ticker_handler import TickerWebSocketHandler

    ws = FakeWS()
    h = TickerWebSocketHandler()
    await h.route_ticker_message(ws, "not-json", connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "MALFORMED_MESSAGE"


async def test_route_invalid_operation_not_implemented():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.ticker_handler import TickerWebSocketHandler

    ws = FakeWS()
    h = TickerWebSocketHandler()
    msg = {"action": "nope", "request_id": "r1", "params": {}}
    await h.route_ticker_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_OPERATION"


async def test_get_ticker_missing_params_invalid_params():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.ticker_handler import TickerWebSocketHandler

    ws = FakeWS()
    h = TickerWebSocketHandler()
    msg = {"action": "get_ticker", "request_id": "r1", "params": {}}
    await h.route_ticker_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_PARAMS"


async def test_get_all_tickers_missing_exchange_invalid_params():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.ticker_handler import TickerWebSocketHandler

    ws = FakeWS()
    h = TickerWebSocketHandler()
    msg = {"action": "get_all_tickers", "request_id": "r1", "params": {}}
    await h.route_ticker_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_PARAMS"


async def test_stream_tickers_confirmation_and_cleanup():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.ticker_handler import TickerWebSocketHandler

    ws = FakeWS()
    h = TickerWebSocketHandler()

    # Monkeypatch the internal streaming coroutine to a one-shot message
    async def fake_stream(ws, request_id, exchange, symbols, stream_key):  # type: ignore[no-untyped-def]
        msg = {
            "request_id": request_id,
            "action": "ticker_update",
            "result": {
                "stream_key": stream_key,
                "exchange": exchange,
                "symbol": (symbols or ["BTC/USDT"])[0],
                "price": 50000.0,
                "volume": 123.0,
                "timestamp": 1700000000.0,
                "bid": 49999.0,
                "ask": 50001.0,
                "change_24h": 2.5,
            },
        }
        await ws.send_text(json.dumps(msg))

    h._stream_ticker_updates = fake_stream  # type: ignore[attr-defined]

    msg = {
        "action": "stream_tickers",
        "request_id": "r1",
        "params": {"exchange": "binance", "symbols": ["BTC/USDT"]},
    }
    await h.route_ticker_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is True
    assert resp["action"] == "stream_tickers"
    key = resp["stream_key"]
    assert key in h.streaming_tasks

    # Verify cleanup cancels and removes tasks
    await h.cleanup_connection("c1")
    assert key not in h.streaming_tasks
