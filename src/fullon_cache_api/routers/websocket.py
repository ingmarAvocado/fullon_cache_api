"""
WebSocket routes and infrastructure for fullon_cache_api.

Provides the foundational WebSocket endpoint and message dispatch loop using the
project's Pydantic message models. Handlers for domain operations are added in
subsequent issues; this module focuses on protocol, validation, and stability.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Awaitable, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fullon_log import get_component_logger  # type: ignore

from ..base import CacheHealthChecker
from ..models import (
    CacheRequest,
    create_error_response,
    create_success_response,
    ErrorCodes,
    ErrorMessage,
)


logger = get_component_logger("fullon.api.cache.websocket.gateway")

router = APIRouter()


async def _send_json(websocket: WebSocket, payload: dict[str, Any]) -> None:
    """Send a JSON payload safely over the WebSocket."""
    await websocket.send_text(json.dumps(payload))


async def _handle_ping(request: CacheRequest) -> dict[str, Any]:
    return create_success_response(
        request_id=request.request_id,
        result={"status": "ok"},
        latency_ms=0.0,
    ).dict()


async def _handle_health_check(request: CacheRequest) -> dict[str, Any]:
    checker = CacheHealthChecker()
    ws = await checker.check_websocket_connectivity()
    cache = await checker.check_cache_connectivity()
    result = {"websocket": ws, "cache": cache}
    return create_success_response(
        request_id=request.request_id, result=result
    ).dict()


async def _handle_not_implemented(request: CacheRequest) -> dict[str, Any]:
    err = create_error_response(
        request_id=request.request_id,
        error_code=ErrorCodes.INVALID_OPERATION,
        error_message=f"Operation '{request.operation}' not implemented",
    )
    return err.dict()


_DISPATCH: dict[str, Callable[[CacheRequest], Awaitable[dict[str, Any]]]] = {
    "ping": _handle_ping,
    "health_check": _handle_health_check,
}


@router.websocket("/ws")
async def websocket_gateway(websocket: WebSocket) -> None:
    """Accept WebSocket connections and process JSON messages.

    Protocol:
    - Receive text JSON; validate as CacheRequest
    - Dispatch non-stream operations immediately and respond with CacheResponse
    - For unsupported/stream operations, return standardized ErrorMessage
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    try:
        while True:
            raw = await websocket.receive_text()
            start = time.time()

            # Parse JSON
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                error = create_error_response(
                    request_id=None,
                    error_code=ErrorCodes.MALFORMED_MESSAGE,
                    error_message="Malformed JSON message",
                )
                await _send_json(websocket, error.dict())
                continue

            # Validate request model
            try:
                request = CacheRequest(**data)
            except Exception as exc:  # pydantic validation error
                error = create_error_response(
                    request_id=data.get("request_id"),
                    error_code=ErrorCodes.INVALID_OPERATION,
                    error_message=str(exc),
                )
                await _send_json(websocket, error.dict())
                continue

            # Dispatch
            handler = _DISPATCH.get(request.operation, _handle_not_implemented)
            try:
                response = await handler(request)
                # Inject latency when applicable
                if response.get("success"):
                    response["latency_ms"] = (time.time() - start) * 1000
                await _send_json(websocket, response)
            except Exception as exc:
                logger.error("Unhandled error in WS handler", error=str(exc))
                error = create_error_response(
                    request_id=request.request_id,
                    error_code=ErrorCodes.INTERNAL_ERROR,
                    error_message="Internal server error",
                )
                await _send_json(websocket, error.dict())

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

