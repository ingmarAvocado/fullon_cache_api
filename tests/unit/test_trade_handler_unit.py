"""Unit tests for TradesWebSocketHandler without external cache dependency."""

from __future__ import annotations

import asyncio
import json
import sys
import types
from typing import Any, List
import pytest


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
        self._sent_event = asyncio.Event()

    async def send_text(self, text: str) -> None:
        self.sent.append(text)
        self._sent_event.set()


def _last_json(ws: FakeWS) -> dict[str, Any]:
    assert ws.sent, "no messages sent"
    return json.loads(ws.sent[-1])


async def _wait_for_sent(ws: FakeWS, timeout: float = 1.0) -> None:
    await asyncio.wait_for(ws._sent_event.wait(), timeout=timeout)


async def test_route_invalid_json_malformed_message():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.trade_handler import TradesWebSocketHandler

    ws = FakeWS()
    h = TradesWebSocketHandler()
    await h.route_trade_message(ws, "not-json", connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "MALFORMED_MESSAGE"


async def test_route_invalid_operation_not_implemented():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.trade_handler import TradesWebSocketHandler

    ws = FakeWS()
    h = TradesWebSocketHandler()
    msg = {"action": "nope", "request_id": "r1", "params": {}}
    await h.route_trade_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_OPERATION"


async def test_get_trades_missing_params_invalid_params():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.trade_handler import TradesWebSocketHandler

    ws = FakeWS()
    h = TradesWebSocketHandler()
    msg = {"action": "get_trades", "request_id": "r1", "params": {}}
    await h.route_trade_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "INVALID_PARAMS"


async def test_stream_trade_updates_confirmation_and_cleanup():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.trade_handler import TradesWebSocketHandler

    ws = FakeWS()
    h = TradesWebSocketHandler()

    async def fake_stream(*args, **kwargs):  # type: ignore
        await asyncio.sleep(0)

    h._stream_trade_updates = fake_stream  # type: ignore[attr-defined]

    msg = {
        "action": "stream_trade_updates",
        "request_id": "r1",
        "params": {"exchange": "binance", "symbol": "BTC/USDT"},
    }
    await h.route_trade_message(ws, json.dumps(msg), connection_id="c1")
    resp = _last_json(ws)
    assert resp["success"] is True
    assert resp["action"] == "stream_trade_updates"
    key = resp["stream_key"]
    assert key in h.streaming_tasks

    await h.cleanup_connection("c1")
    assert key not in h.streaming_tasks


def _install_fake_fullon_cache_trades(trades_behavior: str = "ok") -> tuple[str | None, str | None]:
    """Install a fake fullon_cache.trades_cache module with TradesCache.

    trades_behavior:
      - "ok": get_trades returns a static list
      - "error": get_trades raises an Exception
      - "stream_once": get_trades returns one trade once, then repeats
    """
    pkg_name = "fullon_cache"
    mod_name = "fullon_cache.trades_cache"
    existing_pkg = sys.modules.get(pkg_name)
    pkg = existing_pkg or types.ModuleType(pkg_name)
    sub = types.ModuleType("trades_cache")

    class _Trade:
        def __init__(self, trade_id: str, symbol: str = "BTCUSDT") -> None:
            self.trade_id = trade_id
            self.symbol = symbol
            self.side = "buy"
            self.volume = 0.1
            self.price = 50000.0
            self.time = 1700000000.0

    class TradesCache:
        def __init__(self) -> None:
            self._calls = 0

        async def __aenter__(self) -> "TradesCache":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            return None

        async def get_trades(self, normalized_symbol: str, exchange: str):  # type: ignore[no-untyped-def]
            self._calls += 1
            if trades_behavior == "error":
                raise RuntimeError("boom")
            if trades_behavior == "stream_once":
                # First call yields one trade, subsequent calls same last trade
                return [_Trade("t1", symbol=normalized_symbol)]
            # Default: a couple of trades
            return [_Trade("t1", symbol=normalized_symbol), _Trade("t2", symbol=normalized_symbol)]

    sub.TradesCache = TradesCache  # type: ignore[attr-defined]
    # register package and submodule
    sys.modules[pkg_name] = pkg
    setattr(pkg, "trades_cache", sub)
    sys.modules[mod_name] = sub
    # Return keys so callers can clean up
    return (pkg_name if existing_pkg is None else None, mod_name)


@pytest.mark.asyncio
async def test_get_trades_success_with_fake_cache():
    _install_fake_fullon_log()
    created_pkg, submod = _install_fake_fullon_cache_trades("ok")
    from src.fullon_cache_api.handlers.trade_handler import TradesWebSocketHandler

    ws = FakeWS()
    h = TradesWebSocketHandler()
    msg = {
        "action": "get_trades",
        "request_id": "r1",
        "params": {"exchange": "binance", "symbol": "BTC/USDT"},
    }
    try:
        await h.route_trade_message(ws, json.dumps(msg), connection_id="c1")
    finally:
        # Cleanup fake modules
        if submod in sys.modules:
            del sys.modules[submod]
        if created_pkg is not None and created_pkg in sys.modules:
            del sys.modules[created_pkg]
    resp = _last_json(ws)
    assert resp["success"] is True
    assert resp["result"]["exchange"] == "binance"
    assert resp["result"]["symbol"] == "BTC/USDT"
    assert isinstance(resp["result"]["trades"], list)
    assert len(resp["result"]["trades"]) >= 1


@pytest.mark.asyncio
async def test_get_trades_error_sends_cache_error():
    _install_fake_fullon_log()
    created_pkg, submod = _install_fake_fullon_cache_trades("error")
    from src.fullon_cache_api.handlers.trade_handler import TradesWebSocketHandler

    ws = FakeWS()
    h = TradesWebSocketHandler()
    msg = {
        "action": "get_trades",
        "request_id": "r1",
        "params": {"exchange": "binance", "symbol": "BTC/USDT"},
    }
    try:
        await h.route_trade_message(ws, json.dumps(msg), connection_id="c1")
    finally:
        if submod in sys.modules:
            del sys.modules[submod]
        if created_pkg is not None and created_pkg in sys.modules:
            del sys.modules[created_pkg]
    resp = _last_json(ws)
    assert resp["success"] is False
    assert resp["error_code"] == "CACHE_ERROR"


@pytest.mark.asyncio
async def test_stream_trade_updates_emits_update_with_fake_cache():
    _install_fake_fullon_log()
    from src.fullon_cache_api.handlers.trade_handler import TradesWebSocketHandler

    ws = FakeWS()
    h = TradesWebSocketHandler()

    # Monkeypatch the streaming coroutine to a deterministic one-shot update
    async def one_shot_stream(websocket, request_id, exchange, symbol, stream_key):  # type: ignore[no-untyped-def]
        msg = {
            "request_id": request_id,
            "action": "trade_update",
            "result": {
                "stream_key": stream_key,
                "exchange": exchange,
                "symbol": symbol,
                "side": "buy",
                "volume": 0.1,
                "price": 50000.0,
                "timestamp": 1700000000.0,
                "trade_id": "t1",
            },
        }
        await websocket.send_text(json.dumps(msg))

    h._stream_trade_updates = one_shot_stream  # type: ignore[attr-defined]

    await h._stream_trade_updates(ws, "r1", "binance", "BTC/USDT", "c1:r1")
    await _wait_for_sent(ws, timeout=1.0)
    payload = _last_json(ws)
    assert payload["action"] == "trade_update"
    assert payload["result"]["exchange"] == "binance"
    assert payload["result"]["symbol"] == "BTC/USDT"
