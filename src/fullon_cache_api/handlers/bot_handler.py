"""
Bot WebSocket handler implementing read-only bot coordination/status operations.

Implements:
- get_bot_status: fetch a bot status snapshot
- is_blocked: check if an exchange/symbol is blocked and by whom
- get_bots: fetch all bots status
- stream_bot_status: real-time bot status updates (polling, async only)

Design constraints:
- Read-only operations only
- Uses fullon_log for structured logging
- Uses fullon_cache BotCache sessions with async context mgmt
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fullon_log import get_component_logger  # type: ignore

logger = get_component_logger("fullon.api.cache.bots")


class BotWebSocketHandler:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.streaming_tasks: dict[str, asyncio.Task[Any]] = {}

    async def handle_connection(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(
            "Bot WebSocket connected", connection_id=connection_id, handler="bots"
        )

        try:
            while True:
                message = await websocket.receive_text()
                await self.route_bot_message(websocket, message, connection_id)
        except WebSocketDisconnect:
            logger.info(
                "Bot WebSocket disconnected",
                connection_id=connection_id,
                handler="bots",
            )
        finally:
            await self.cleanup_connection(connection_id)

    async def route_bot_message(
        self, websocket: WebSocket, message: str, connection_id: str
    ) -> None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            await self.send_error(
                websocket, None, "MALFORMED_MESSAGE", "Malformed JSON message"
            )
            return

        action = data.get("action")
        request_id = data.get("request_id")
        params = data.get("params", {}) or {}

        if action == "get_bot_status":
            await self.handle_get_bot_status(
                websocket, request_id, params, connection_id
            )
        elif action == "is_blocked":
            await self.handle_is_blocked(websocket, request_id, params, connection_id)
        elif action == "get_bots":
            await self.handle_get_bots(websocket, request_id, params, connection_id)
        elif action == "stream_bot_status":
            await self.handle_stream_bot_status(
                websocket, request_id, params, connection_id
            )
        else:
            await self.send_error(
                websocket,
                request_id,
                "INVALID_OPERATION",
                f"Operation '{action}' not implemented",
            )

    async def send_error(
        self, websocket: WebSocket, request_id: str | None, code: str, message: str
    ) -> None:
        payload = {
            "request_id": request_id,
            "success": False,
            "error_code": code,
            "error": message,
        }
        await websocket.send_text(json.dumps(payload))

    async def handle_get_bot_status(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        bot_id = params.get("bot_id")
        if not bot_id:
            await self.send_error(
                websocket, request_id, "INVALID_PARAMS", "bot_id parameter required"
            )
            return

        logger.info(
            "Get bot status started",
            bot_id=bot_id,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            from fullon_cache import BotCache  # type: ignore

            async with BotCache() as cache:  # type: ignore[call-arg]
                bots = await cache.get_bots()
                data = bots.get(str(bot_id), None) if bots else None

            if data:
                # Attempt to normalize a few top-level fields if present
                # Derive status from first feed if not explicitly set
                status = None
                if isinstance(data, dict):
                    # Look for nested feed dicts
                    for feed in data.values():
                        if isinstance(feed, dict) and "status" in feed:
                            status = feed.get("status")
                            break
                result = {
                    "bot_id": str(bot_id),
                    "status": status or "unknown",
                    "data": data,
                    "timestamp": time.time(),
                }
                response = {
                    "request_id": request_id,
                    "action": "get_bot_status",
                    "success": True,
                    "result": result,
                }
            else:
                response = {
                    "request_id": request_id,
                    "action": "get_bot_status",
                    "success": False,
                    "error_code": "BOT_NOT_FOUND",
                    "error": f"Bot {bot_id} not found",
                }

            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error("Get bot status failed", bot_id=bot_id, error=str(exc))
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve bot status"
            )

    async def handle_is_blocked(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        exchange = params.get("exchange")
        symbol = params.get("symbol")
        if not exchange or not symbol:
            await self.send_error(
                websocket,
                request_id,
                "INVALID_PARAMS",
                "exchange and symbol parameters required",
            )
            return

        logger.info(
            "Is blocked check started",
            exchange=exchange,
            symbol=symbol,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            from fullon_cache import BotCache  # type: ignore

            async with BotCache() as cache:  # type: ignore[call-arg]
                blocked_by = await cache.is_blocked(str(exchange), str(symbol))
            is_blocked = bool(blocked_by)
            response = {
                "request_id": request_id,
                "action": "is_blocked",
                "success": True,
                "result": {
                    "exchange": str(exchange),
                    "symbol": str(symbol),
                    "is_blocked": is_blocked,
                    "blocked_by": blocked_by or None,
                    "timestamp": time.time(),
                },
            }
            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Is blocked check failed",
                exchange=exchange,
                symbol=symbol,
                error=str(exc),
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to query blocking status"
            )

    async def handle_get_bots(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        logger.info(
            "Get bots started", request_id=request_id, connection_id=connection_id
        )
        try:
            from fullon_cache import BotCache  # type: ignore

            async with BotCache() as cache:  # type: ignore[call-arg]
                bots = await cache.get_bots()

            response = {
                "request_id": request_id,
                "action": "get_bots",
                "success": True,
                "result": {"bots": bots or {}},
            }
            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error("Get bots failed", error=str(exc))
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve bots"
            )

    async def handle_stream_bot_status(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        # Optional filter: single bot_id
        bot_id = params.get("bot_id")
        stream_key = f"{connection_id}:{request_id}"
        try:
            task = asyncio.create_task(
                self._stream_bot_updates(websocket, request_id, bot_id, stream_key)
            )
            self.streaming_tasks[stream_key] = task

            confirmation = {
                "request_id": request_id,
                "action": "stream_bot_status",
                "success": True,
                "message": (
                    f"Streaming started for bot {bot_id}"
                    if bot_id
                    else "Streaming started"
                ),
                "stream_key": stream_key,
            }
            await websocket.send_text(json.dumps(confirmation))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Bot streaming initialization failed",
                error=str(exc),
                stream_key=stream_key,
            )
            await self.send_error(
                websocket, request_id, "INTERNAL_ERROR", "Failed to start bot streaming"
            )

    async def _stream_bot_updates(
        self, websocket: WebSocket, request_id: str, bot_id: str | None, stream_key: str
    ) -> None:
        last_snapshot: dict[str, Any] | None = None
        try:
            from fullon_cache import BotCache  # type: ignore

            async with BotCache() as cache:  # type: ignore[call-arg]
                while True:
                    try:
                        bots = await cache.get_bots()
                        snapshot = bots or {}
                        if bot_id:
                            snapshot = (
                                {bot_id: snapshot.get(bot_id)}
                                if bot_id in snapshot
                                else {}
                            )
                    except Exception:
                        snapshot = last_snapshot or {}

                    if snapshot != last_snapshot:
                        last_snapshot = snapshot
                        msg = {
                            "request_id": request_id,
                            "action": "bot_update",
                            "result": {
                                "stream_key": stream_key,
                                "bots": snapshot,
                                "timestamp": time.time(),
                            },
                        }
                        await websocket.send_text(json.dumps(msg))

                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:  # pragma: no cover - cancellation timing
            logger.info("Bot streaming cancelled", stream_key=stream_key)
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error("Bot streaming error", error=str(exc), stream_key=stream_key)

    async def cleanup_connection(self, connection_id: str) -> None:
        # Cancel and remove all streaming tasks for this connection
        to_cancel = [
            k for k in self.streaming_tasks.keys() if k.startswith(f"{connection_id}:")
        ]
        for key in to_cancel:
            task = self.streaming_tasks.pop(key, None)
            if task and not task.done():
                task.cancel()
        self.active_connections.pop(connection_id, None)
