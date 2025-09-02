"""WebSocket test utilities for REAL Redis integration tests.

This module provides small helpers to streamline request/response handling
when using `starlette.testclient.TestClient` WebSocket connections.

Constraints:
- NO MOCKS: Tests interact with real Redis via cache layers.
- Deterministic: Keep messages small and responses validated explicitly.
"""

from __future__ import annotations

import json
from typing import Any, Dict


def send_json(ws, message: Dict[str, Any]) -> None:
    """Send a JSON message over a TestClient WebSocket.

    Example:
        send_json(ws, {"action": "get_ticker", "request_id": "r1", "params": {...}})
    """

    ws.send_text(json.dumps(message))


def receive_json(ws) -> Dict[str, Any]:
    """Receive a JSON message from a TestClient WebSocket."""

    return json.loads(ws.receive_text())


def send_and_receive(ws, message: Dict[str, Any]) -> Dict[str, Any]:
    """Send a JSON message and return the parsed JSON response."""

    send_json(ws, message)
    return receive_json(ws)

