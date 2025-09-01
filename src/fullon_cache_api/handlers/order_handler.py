"""
Orders WebSocket handler implementing read-only order status and queue operations.

Implements:
- get_order_status: fetch a single order status snapshot
- get_queue_length: current number of orders for an exchange (proxy via cache)
- stream_order_queue: real-time queue length updates (async, no callbacks)

Design constraints:
- Read-only operations only
- Uses fullon_log for structured logging
- Uses fullon_cache OrdersCache sessions with async context mgmt
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fullon_log import get_component_logger  # type: ignore


logger = get_component_logger("fullon.api.cache.orders")


class OrdersWebSocketHandler:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.streaming_tasks: dict[str, asyncio.Task[Any]] = {}

    async def handle_connection(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(
            "Orders WebSocket connected", connection_id=connection_id, handler="orders"
        )

        try:
            while True:
                message = await websocket.receive_text()
                await self.route_order_message(websocket, message, connection_id)
        except WebSocketDisconnect:
            logger.info(
                "Orders WebSocket disconnected",
                connection_id=connection_id,
                handler="orders",
            )
        finally:
            await self.cleanup_connection(connection_id)

    async def route_order_message(
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

        if action == "get_order_status":
            await self.handle_get_order_status(
                websocket, request_id, params, connection_id
            )
        elif action == "get_queue_length":
            await self.handle_get_queue_length(websocket, request_id, params, connection_id)
        elif action == "stream_order_queue":
            await self.handle_stream_order_queue(
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

    async def handle_get_order_status(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        order_id = params.get("order_id")
        exchange = params.get("exchange")

        if not order_id or not exchange:
            await self.send_error(
                websocket,
                request_id,
                "INVALID_PARAMS",
                "exchange and order_id parameters required",
            )
            return

        logger.info(
            "Get order status started",
            exchange=exchange,
            order_id=order_id,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            # Lazy import to avoid hard dependency at import time
            from fullon_cache import OrdersCache  # type: ignore

            async with OrdersCache() as cache:  # type: ignore[call-arg]
                order = await cache.get_order_status(str(exchange), str(order_id))

            if order:
                volume = float(getattr(order, "volume", 0.0))
                final_volume = getattr(order, "final_volume", None)
                try:
                    filled = float(final_volume) if final_volume is not None else 0.0
                except Exception:
                    filled = 0.0
                remaining = max(volume - filled, 0.0)

                # Normalize timestamp to float seconds when possible
                ts_val = getattr(order, "timestamp", None)
                if isinstance(ts_val, (int, float)):
                    ts = float(ts_val)
                else:
                    try:
                        # datetime -> seconds
                        ts = float(getattr(ts_val, "timestamp", lambda: 0.0)())
                    except Exception:
                        ts = time.time()

                result = {
                    "order_id": getattr(order, "ex_order_id", str(order_id)),
                    "symbol": getattr(order, "symbol", None),
                    "exchange": str(exchange),
                    "side": getattr(order, "side", None),
                    "amount": volume,
                    "price": float(getattr(order, "price", 0.0)),
                    "filled": filled,
                    "remaining": remaining,
                    "status": getattr(order, "status", None),
                    "order_type": getattr(order, "order_type", None),
                    "timestamp": ts,
                    "last_update": ts,
                }
                response = {
                    "request_id": request_id,
                    "action": "get_order_status",
                    "success": True,
                    "result": result,
                }
            else:
                response = {
                    "request_id": request_id,
                    "action": "get_order_status",
                    "success": False,
                    "error_code": "ORDER_NOT_FOUND",
                    "error": f"Order {order_id} not found",
                }

            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get order status failed",
                exchange=exchange,
                order_id=order_id,
                error=str(exc),
                request_id=request_id,
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve order status"
            )

    async def handle_get_queue_length(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        exchange = params.get("exchange")
        if not exchange:
            await self.send_error(
                websocket, request_id, "INVALID_PARAMS", "exchange parameter required"
            )
            return

        logger.info(
            "Get queue length started",
            exchange=exchange,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            from fullon_cache import OrdersCache  # type: ignore

            async with OrdersCache() as cache:  # type: ignore[call-arg]
                # Use number of orders for the exchange as a proxy for queue length
                orders = await cache.get_orders(str(exchange))
                queue_length = len(orders or [])

            response = {
                "request_id": request_id,
                "action": "get_queue_length",
                "success": True,
                "result": {
                    "exchange": str(exchange),
                    "queue_length": queue_length,
                    "timestamp": time.time(),
                },
            }
            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get queue length failed", exchange=exchange, error=str(exc)
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve queue length"
            )

    async def handle_stream_order_queue(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        exchange = params.get("exchange")
        if not exchange:
            await self.send_error(
                websocket, request_id, "INVALID_PARAMS", "exchange parameter required"
            )
            return

        stream_key = f"{connection_id}:{request_id}"
        try:
            task = asyncio.create_task(
                self._stream_queue_length(websocket, request_id, str(exchange), stream_key)
            )
            self.streaming_tasks[stream_key] = task

            confirmation = {
                "request_id": request_id,
                "action": "stream_order_queue",
                "success": True,
                "message": f"Streaming started for {exchange}",
                "stream_key": stream_key,
            }
            await websocket.send_text(json.dumps(confirmation))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Order queue streaming initialization failed",
                exchange=exchange,
                error=str(exc),
                stream_key=stream_key,
            )
            await self.send_error(
                websocket, request_id, "INTERNAL_ERROR", "Failed to start queue stream"
            )

    async def _stream_queue_length(
        self, websocket: WebSocket, request_id: str, exchange: str, stream_key: str
    ) -> None:
        last_len: int | None = None
        try:
            from fullon_cache import OrdersCache  # type: ignore

            async with OrdersCache() as cache:  # type: ignore[call-arg]
                while True:
                    try:
                        orders = await cache.get_orders(exchange)
                        qlen = len(orders or [])
                    except Exception:
                        qlen = last_len if last_len is not None else 0

                    if qlen != last_len:
                        last_len = qlen
                        msg = {
                            "request_id": request_id,
                            "action": "queue_update",
                            "result": {
                                "stream_key": stream_key,
                                "exchange": exchange,
                                "queue_length": qlen,
                                "timestamp": time.time(),
                            },
                        }
                        await websocket.send_text(json.dumps(msg))

                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:  # pragma: no cover - cancellation timing
            logger.info("Order queue streaming cancelled", stream_key=stream_key)
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error("Order queue streaming error", error=str(exc), stream_key=stream_key)

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

