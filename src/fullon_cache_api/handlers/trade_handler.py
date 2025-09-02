"""
Trade WebSocket handler implementing read-only trades operations.

Implements:
- get_trades: fetch recent trades for a symbol
- stream_trade_updates: start real-time trade updates via async polling/iterator

Design constraints:
- Read-only operations only
- Uses fullon_log for structured logging
- Uses fullon_cache TradesCache sessions with async context mgmt
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fullon_log import get_component_logger  # type: ignore

logger = get_component_logger("fullon.api.cache.trades")


def _normalize_symbol(symbol: str) -> str:
    """Normalize symbol to match TradesCache expectations (remove slash)."""
    return symbol.replace("/", "") if symbol else symbol


class TradesWebSocketHandler:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.streaming_tasks: dict[str, asyncio.Task[Any]] = {}

    async def handle_connection(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(
            "Trades WebSocket connected", connection_id=connection_id, handler="trades"
        )

        try:
            while True:
                message = await websocket.receive_text()
                await self.route_trade_message(websocket, message, connection_id)
        except WebSocketDisconnect:
            logger.info(
                "Trades WebSocket disconnected",
                connection_id=connection_id,
                handler="trades",
            )
        finally:
            await self.cleanup_connection(connection_id)

    async def route_trade_message(
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

        if action == "get_trades":
            await self.handle_get_trades(websocket, request_id, params, connection_id)
        elif action == "stream_trade_updates":
            await self.handle_stream_trade_updates(
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

    async def handle_get_trades(
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
            "Get trades operation started",
            exchange=exchange,
            symbol=symbol,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            from fullon_cache.trades_cache import TradesCache  # type: ignore

            items: list[dict[str, Any]] = []
            async with TradesCache() as cache:  # type: ignore[call-arg]
                # TradesCache expects normalized symbol (e.g., BTCUSDT)
                normalized = _normalize_symbol(str(symbol))
                trades = await cache.get_trades(normalized, exchange)

                for t in trades or []:
                    rec = {
                        "symbol": getattr(t, "symbol", symbol),
                        "exchange": exchange,
                        "side": getattr(t, "side", None),
                        "volume": float(getattr(t, "volume", 0.0)),
                        "price": float(getattr(t, "price", 0.0)),
                        "timestamp": float(
                            getattr(t, "time", getattr(t, "timestamp", 0.0))
                        ),
                        "trade_id": getattr(t, "trade_id", None),
                    }
                    items.append(rec)

            response = {
                "request_id": request_id,
                "action": "get_trades",
                "success": True,
                "result": {"exchange": exchange, "symbol": symbol, "trades": items},
            }
            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get trades operation failed",
                exchange=exchange,
                symbol=symbol,
                error=str(exc),
                request_id=request_id,
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve trades"
            )

    async def handle_stream_trade_updates(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        exchange = params.get("exchange")
        symbol = params.get("symbol")  # Optional filter
        if not exchange:
            await self.send_error(
                websocket, request_id, "INVALID_PARAMS", "exchange parameter required"
            )
            return

        stream_key = f"{connection_id}:{request_id}"
        try:
            task = asyncio.create_task(
                self._stream_trade_updates(
                    websocket, request_id, exchange, symbol, stream_key
                )
            )
            self.streaming_tasks[stream_key] = task

            confirmation = {
                "request_id": request_id,
                "action": "stream_trade_updates",
                "success": True,
                "message": (
                    f"Streaming started for {exchange}"
                    + (f" symbol={symbol}" if symbol else "")
                ),
                "stream_key": stream_key,
            }
            await websocket.send_text(json.dumps(confirmation))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Trade streaming initialization failed",
                exchange=exchange,
                error=str(exc),
                stream_key=stream_key,
            )
            await self.send_error(
                websocket,
                request_id,
                "INTERNAL_ERROR",
                "Failed to start trade streaming",
            )

    async def _stream_trade_updates(
        self,
        websocket: WebSocket,
        request_id: str,
        exchange: str,
        symbol: str | None,
        stream_key: str,
    ) -> None:
        last_seen_id: Any = None
        last_count: int | None = None
        try:
            from fullon_cache.trades_cache import TradesCache  # type: ignore

            async with TradesCache() as cache:  # type: ignore[call-arg]
                while True:
                    try:
                        if symbol:
                            normalized = _normalize_symbol(str(symbol))
                            trades = await cache.get_trades(normalized, exchange)
                        else:
                            # Without symbol filter, no direct API; keep empty
                            trades = []
                    except Exception:
                        trades = []

                    update_needed = False
                    current_count = len(trades or [])
                    if last_count is None or current_count > last_count:
                        update_needed = True
                    # Track last trade id if available
                    current_id = None
                    if trades:
                        last = trades[-1]
                        current_id = getattr(last, "trade_id", None)
                    if last_seen_id != current_id and current_id is not None:
                        update_needed = True

                    if update_needed and trades:
                        last = trades[-1]
                        msg = {
                            "request_id": request_id,
                            "action": "trade_update",
                            "result": {
                                "stream_key": stream_key,
                                "exchange": exchange,
                                "symbol": getattr(last, "symbol", symbol),
                                "side": getattr(last, "side", None),
                                "volume": float(getattr(last, "volume", 0.0)),
                                "price": float(getattr(last, "price", 0.0)),
                                "timestamp": float(
                                    getattr(
                                        last, "time", getattr(last, "timestamp", 0.0)
                                    )
                                ),
                                "trade_id": getattr(last, "trade_id", None),
                            },
                        }
                        await websocket.send_text(json.dumps(msg))
                        last_seen_id = current_id
                        last_count = current_count

                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:  # pragma: no cover - cancellation timing
            logger.info("Trade streaming cancelled", stream_key=stream_key)
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error("Trade streaming error", error=str(exc), stream_key=stream_key)

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
