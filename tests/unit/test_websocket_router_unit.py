"""Unit-style tests for the WebSocket gateway protocol.

Covers protocol-level behaviors: JSON parsing errors, validation errors,
implemented operations (ping, health_check), and not-implemented operations
that are still allowed by the request model.
"""

from __future__ import annotations

import json

import pytest
from starlette.testclient import TestClient
import sys
import types


pytestmark: list = []


def _install_fake_fullon_log() -> None:
    """Install a minimal fake `fullon_log` to avoid multiprocessing issues in tests."""
    if "fullon_log" in sys.modules:
        return
    m = types.ModuleType("fullon_log")

    class _Dummy:
        def __getattr__(self, name):  # noqa: D401
            def _noop(*args, **kwargs):
                return None

            return _noop

    def get_component_logger(name: str) -> _Dummy:  # type: ignore
        return _Dummy()

    m.get_component_logger = get_component_logger  # type: ignore[attr-defined]
    sys.modules["fullon_log"] = m


def _ws(client: TestClient):
    return client.websocket_connect("/ws")


def test_ws_malformed_json_returns_error() -> None:
    _install_fake_fullon_log()
    from src.fullon_cache_api.main import create_app
    from src.fullon_cache_api.models.messages import ErrorCodes

    client = TestClient(create_app())
    with _ws(client) as ws:
        ws.send_text("not-json")
        resp = json.loads(ws.receive_text())
        assert resp["error_code"] == ErrorCodes.MALFORMED_MESSAGE
        assert "Malformed JSON" in resp["error"]


def test_ws_invalid_operation_validation_error() -> None:
    _install_fake_fullon_log()
    from src.fullon_cache_api.main import create_app
    from src.fullon_cache_api.models.messages import ErrorCodes

    client = TestClient(create_app())
    with _ws(client) as ws:
        # Operation not in ALLOWED_OPERATIONS -> pydantic validation error
        msg = {"request_id": "r1", "operation": "does_not_exist", "params": {}}
        ws.send_text(json.dumps(msg))
        resp = json.loads(ws.receive_text())
        assert resp["error_code"] == ErrorCodes.INVALID_OPERATION
        assert "Invalid FastAPI WebSocket operation" in resp["error"]


def test_ws_ping_success_includes_latency() -> None:
    _install_fake_fullon_log()
    from src.fullon_cache_api.main import create_app
    from src.fullon_cache_api.models.messages import ErrorCodes

    client = TestClient(create_app())
    with _ws(client) as ws:
        msg = {"request_id": "ping-1", "operation": "ping", "params": {}}
        ws.send_text(json.dumps(msg))
        resp = json.loads(ws.receive_text())
        assert resp["success"] is True
        assert resp["result"]["status"] == "ok"
        # Latency injected by gateway
        assert isinstance(resp.get("latency_ms"), (int, float))
        assert resp["latency_ms"] >= 0.0


def test_ws_health_check_success_shape() -> None:
    _install_fake_fullon_log()
    from src.fullon_cache_api.main import create_app
    from src.fullon_cache_api.models.messages import ErrorCodes

    client = TestClient(create_app())
    with _ws(client) as ws:
        msg = {"request_id": "health-1", "operation": "health_check", "params": {}}
        ws.send_text(json.dumps(msg))
        resp = json.loads(ws.receive_text())
        assert resp["success"] is True
        result = resp["result"]
        assert set(result.keys()) == {"websocket", "cache"}
        assert result["websocket"]["status"] == "healthy"
        assert result["cache"]["status"] == "healthy"


def test_ws_allowed_but_not_implemented_returns_error() -> None:
    _install_fake_fullon_log()
    from src.fullon_cache_api.main import create_app
    from src.fullon_cache_api.models.messages import ErrorCodes

    client = TestClient(create_app())
    with _ws(client) as ws:
        # "get_ticker" is allowed by the model but not mapped in the router
        msg = {
            "request_id": "u1",
            "operation": "get_ticker",
            "params": {"exchange": "binance", "symbol": "BTC/USDT"},
        }
        ws.send_text(json.dumps(msg))
        resp = json.loads(ws.receive_text())
        assert resp["error_code"] == ErrorCodes.INVALID_OPERATION
        assert "not implemented" in resp["error"].lower()


def test_ws_handler_internal_error_returns_500_like_error() -> None:
    _install_fake_fullon_log()
    from src.fullon_cache_api.main import create_app
    from src.fullon_cache_api.models.messages import ErrorCodes
    from src.fullon_cache_api.routers import websocket as wsmod

    # Temporarily replace the 'ping' handler to raise
    original = wsmod._DISPATCH.get("ping")

    async def boom(_request):  # type: ignore
        raise RuntimeError("boom")

    wsmod._DISPATCH["ping"] = boom  # type: ignore
    try:
        client = TestClient(create_app())
        with _ws(client) as ws:
            msg = {"request_id": "r1", "operation": "ping", "params": {}}
            ws.send_text(json.dumps(msg))
            resp = json.loads(ws.receive_text())
            assert resp["error_code"] == ErrorCodes.INTERNAL_ERROR
            assert "Internal server error" in resp["error"]
    finally:
        if original is not None:
            wsmod._DISPATCH["ping"] = original  # type: ignore
