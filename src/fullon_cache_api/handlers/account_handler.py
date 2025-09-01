"""
Account WebSocket handler implementing read-only account operations.

Implements:
- get_balance: fetch a user's balance for a currency
- get_positions: fetch a user's positions (optionally filter by exchange/ex_id)
- stream_positions: start real-time position streaming via async iterator (no callbacks)

Design constraints:
- Read-only operations only
- Uses fullon_log for structured logging
- Integrates with fullon_cache AccountCache using async context mgmt
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fullon_log import get_component_logger  # type: ignore


logger = get_component_logger("fullon.api.cache.accounts")


class AccountWebSocketHandler:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.streaming_tasks: dict[str, asyncio.Task[Any]] = {}

    async def handle_connection(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(
            "Account WebSocket connected",
            connection_id=connection_id,
            handler="accounts",
        )

        try:
            while True:
                message = await websocket.receive_text()
                await self.route_account_message(websocket, message, connection_id)
        except WebSocketDisconnect:
            logger.info(
                "Account WebSocket disconnected",
                connection_id=connection_id,
                handler="accounts",
            )
        finally:
            await self.cleanup_connection(connection_id)

    async def route_account_message(
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

        if action == "get_balance":
            await self.handle_get_balance(websocket, request_id, params, connection_id)
        elif action == "get_positions":
            await self.handle_get_positions(
                websocket, request_id, params, connection_id
            )
        elif action == "stream_positions":
            await self.handle_stream_positions(
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

    async def handle_get_balance(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        user_id = params.get("user_id")
        # Accept both "currency" (preferred) and legacy "exchange" for compatibility
        currency = params.get("currency") or params.get("exchange")

        if user_id is None or not currency:
            await self.send_error(
                websocket,
                request_id,
                "INVALID_PARAMS",
                "user_id and currency parameters required",
            )
            return

        logger.info(
            "Get balance operation started",
            user_id=user_id,
            currency=currency,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            from fullon_cache import AccountCache  # type: ignore

            async with AccountCache() as cache:  # type: ignore[call-arg]
                data = await cache.get_full_account(int(user_id), str(currency))

            if data:
                total = float(data.get("balance") or data.get("total", 0.0))
                available = float(data.get("available", 0.0))
                reserved = max(total - available, 0.0)
                result = {
                    "user_id": int(user_id),
                    "currency": str(currency),
                    "total_balance": total,
                    "available_balance": available,
                    "reserved_balance": reserved,
                    "timestamp": time.time(),
                }
                response = {
                    "request_id": request_id,
                    "action": "get_balance",
                    "success": True,
                    "result": result,
                }
                logger.info(
                    "Get balance completed",
                    user_id=user_id,
                    currency=currency,
                    total_balance=total,
                    request_id=request_id,
                )
            else:
                response = {
                    "request_id": request_id,
                    "action": "get_balance",
                    "success": False,
                    "error_code": "BALANCE_NOT_FOUND",
                    "error": f"Balance not found for user {user_id} {currency}",
                }

            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get balance operation failed",
                user_id=user_id,
                currency=currency,
                error=str(exc),
                request_id=request_id,
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve balance data"
            )

    async def handle_get_positions(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        user_id = params.get("user_id")
        ex_filter = params.get("exchange")

        if user_id is None:
            await self.send_error(
                websocket, request_id, "INVALID_PARAMS", "user_id parameter required"
            )
            return

        logger.info(
            "Get positions operation started",
            user_id=user_id,
            exchange=ex_filter,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            from fullon_cache import AccountCache  # type: ignore

            async with AccountCache() as cache:  # type: ignore[call-arg]
                positions = await cache.get_positions(int(user_id))

            items: list[dict[str, Any]] = []
            for p in positions or []:
                # Optional exchange filtering using Position.ex_id
                ex_id = getattr(p, "ex_id", None)
                if ex_filter is not None and str(ex_id) != str(ex_filter):
                    continue

                volume = float(getattr(p, "volume", 0.0))
                side = "long" if volume >= 0 else "short"
                items.append(
                    {
                        "symbol": getattr(p, "symbol", None),
                        "exchange": ex_id,
                        "side": side,
                        "size": abs(volume),
                        "entry_price": float(getattr(p, "price", 0.0)),
                        "mark_price": float(getattr(p, "price", 0.0)),
                        "pnl": float(getattr(p, "pnl", 0.0)),
                        "pnl_percent": float(getattr(p, "pnl_percent", 0.0)),
                        "timestamp": float(getattr(p, "timestamp", 0.0))
                        if hasattr(p, "timestamp")
                        else time.time(),
                    }
                )

            response = {
                "request_id": request_id,
                "action": "get_positions",
                "success": True,
                "result": {
                    "user_id": int(user_id),
                    "exchange": ex_filter,
                    "positions": items,
                    "count": len(items),
                },
            }
            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get positions failed",
                user_id=user_id,
                error=str(exc),
                request_id=request_id,
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve positions"
            )

    async def handle_stream_positions(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        user_id = params.get("user_id")
        ex_filter = params.get("exchange")
        if user_id is None:
            await self.send_error(
                websocket, request_id, "INVALID_PARAMS", "user_id parameter required"
            )
            return

        stream_key = f"{connection_id}:{request_id}"
        try:
            task = asyncio.create_task(
                self._stream_position_updates(
                    websocket, request_id, int(user_id), ex_filter, stream_key
                )
            )
            self.streaming_tasks[stream_key] = task

            confirmation = {
                "request_id": request_id,
                "action": "stream_positions",
                "success": True,
                "message": f"Streaming started for user {user_id}",
                "stream_key": stream_key,
            }
            await websocket.send_text(json.dumps(confirmation))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Position streaming initialization failed",
                user_id=user_id,
                error=str(exc),
                stream_key=stream_key,
            )
            await self.send_error(
                websocket,
                request_id,
                "INTERNAL_ERROR",
                "Failed to start position streaming",
            )

    async def _stream_position_updates(
        self,
        websocket: WebSocket,
        request_id: str,
        user_id: int,
        ex_filter: str | int | None,
        stream_key: str,
    ) -> None:
        """Poll positions periodically and emit updates (async iterator style)."""
        last_snapshot: dict[str, float] = {}
        try:
            from fullon_cache import AccountCache  # type: ignore

            async with AccountCache() as cache:  # type: ignore[call-arg]
                # Initial snapshot
                positions = await cache.get_positions(user_id)
                await self._emit_position_list(
                    websocket, request_id, stream_key, positions, ex_filter
                )
                last_snapshot = {
                    f"{getattr(p,'symbol',None)}:{getattr(p,'ex_id',None)}": float(
                        getattr(p, "volume", 0.0)
                    )
                    for p in positions or []
                }

                # Polling loop
                while True:
                    positions = await cache.get_positions(user_id)
                    current = {
                        f"{getattr(p,'symbol',None)}:{getattr(p,'ex_id',None)}": float(
                            getattr(p, "volume", 0.0)
                        )
                        for p in positions or []
                    }

                    if current != last_snapshot:
                        await self._emit_position_list(
                            websocket, request_id, stream_key, positions, ex_filter
                        )
                        last_snapshot = current

                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:  # pragma: no cover - cancellation timing
            logger.info("Position streaming cancelled", stream_key=stream_key)
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Position streaming error", error=str(exc), stream_key=stream_key
            )

    async def _emit_position_list(
        self,
        websocket: WebSocket,
        request_id: str,
        stream_key: str,
        positions: list[Any] | None,
        ex_filter: str | int | None,
    ) -> None:
        for p in positions or []:
            ex_id = getattr(p, "ex_id", None)
            if ex_filter is not None and str(ex_id) != str(ex_filter):
                continue

            volume = float(getattr(p, "volume", 0.0))
            side = "long" if volume >= 0 else "short"
            msg = {
                "request_id": request_id,
                "action": "position_update",
                "result": {
                    "stream_key": stream_key,
                    "user_id": getattr(p, "user_id", None) or None,
                    "exchange": ex_id,
                    "symbol": getattr(p, "symbol", None),
                    "side": side,
                    "size": abs(volume),
                    "entry_price": float(getattr(p, "price", 0.0)),
                    "mark_price": float(getattr(p, "price", 0.0)),
                    "pnl": float(getattr(p, "pnl", 0.0)),
                    "pnl_percent": float(getattr(p, "pnl_percent", 0.0)),
                    "timestamp": float(getattr(p, "timestamp", 0.0))
                    if hasattr(p, "timestamp")
                    else time.time(),
                },
            }
            await websocket.send_text(json.dumps(msg))

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
