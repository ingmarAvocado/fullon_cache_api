"""
OHLCV WebSocket handler implementing read-only OHLCV operations.

Implements:
- get_latest_ohlcv_bars: fetch latest N OHLCV bars
- stream_ohlcv: start real-time OHLCV updates via async iterator/polling

Design constraints:
- Read-only operations only
- Uses fullon_log for structured logging
- Uses fullon_cache OHLCVCache sessions with async context mgmt
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fullon_log import get_component_logger  # type: ignore

logger = get_component_logger("fullon.api.cache.ohlcv")


class OHLCVWebSocketHandler:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.streaming_tasks: dict[str, asyncio.Task[Any]] = {}

    async def handle_connection(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(
            "OHLCV WebSocket connected", connection_id=connection_id, handler="ohlcv"
        )

        try:
            while True:
                message = await websocket.receive_text()
                await self.route_ohlcv_message(websocket, message, connection_id)
        except WebSocketDisconnect:
            logger.info(
                "OHLCV WebSocket disconnected",
                connection_id=connection_id,
                handler="ohlcv",
            )
        finally:
            await self.cleanup_connection(connection_id)

    async def route_ohlcv_message(
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

        if action == "get_latest_ohlcv_bars":
            await self.handle_get_latest_ohlcv_bars(
                websocket, request_id, params, connection_id
            )
        elif action == "stream_ohlcv":
            await self.handle_stream_ohlcv(websocket, request_id, params, connection_id)
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

    async def handle_get_latest_ohlcv_bars(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        symbol = params.get("symbol")
        timeframe = params.get("timeframe")
        count = int(params.get("count", 10))

        if not symbol or not timeframe:
            await self.send_error(
                websocket,
                request_id,
                "INVALID_PARAMS",
                "symbol and timeframe parameters required",
            )
            return

        logger.info(
            "Get latest OHLCV operation started",
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            try:
                from fullon_cache import OHLCVCache  # type: ignore
            except Exception:  # pragma: no cover - import path variant
                from fullon_cache.ohlcv_cache import OHLCVCache  # type: ignore

            async with OHLCVCache() as cache:  # type: ignore[call-arg]
                bars: list[list[float]] | None = None

                getter = getattr(cache, "get_latest_ohlcv_bars", None)
                if callable(getter):
                    try:
                        bars = await getter(symbol, timeframe, count)  # type: ignore[misc]
                    except TypeError:
                        # Some implementations might use keywords
                        bars = await getter(symbol=symbol, timeframe=timeframe, count=count)  # type: ignore[misc]
                else:
                    # Fallback: try to get all and slice
                    get_all = getattr(cache, "get_ohlcv_bars", None)
                    if callable(get_all):
                        try:
                            all_bars = await get_all(symbol, timeframe)  # type: ignore[misc]
                        except TypeError:
                            all_bars = await get_all(symbol=symbol, timeframe=timeframe)  # type: ignore[misc]
                        bars = (all_bars or [])[-count:]

            if bars and len(bars) > 0:
                response = {
                    "request_id": request_id,
                    "action": "get_latest_ohlcv_bars",
                    "success": True,
                    "result": {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "bars": bars,
                    },
                }
                logger.info(
                    "Get latest OHLCV operation completed",
                    symbol=symbol,
                    timeframe=timeframe,
                    returned=len(bars),
                    request_id=request_id,
                )
            else:
                response = {
                    "request_id": request_id,
                    "action": "get_latest_ohlcv_bars",
                    "success": False,
                    "error_code": "OHLCV_NOT_FOUND",
                    "error": f"OHLCV data not found for {symbol} {timeframe}",
                }

            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get latest OHLCV operation failed",
                symbol=symbol,
                timeframe=timeframe,
                error=str(exc),
                request_id=request_id,
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve OHLCV data"
            )

    async def handle_stream_ohlcv(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        symbol = params.get("symbol")
        timeframe = params.get("timeframe")
        if not symbol or not timeframe:
            await self.send_error(
                websocket, request_id, "INVALID_PARAMS", "symbol and timeframe required"
            )
            return

        stream_key = f"{connection_id}:{request_id}"
        try:
            task = asyncio.create_task(
                self._stream_ohlcv_updates(
                    websocket, request_id, symbol, timeframe, stream_key
                )
            )
            self.streaming_tasks[stream_key] = task

            confirmation = {
                "request_id": request_id,
                "action": "stream_ohlcv",
                "success": True,
                "message": f"Streaming started for {symbol} {timeframe}",
                "stream_key": stream_key,
            }
            await websocket.send_text(json.dumps(confirmation))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "OHLCV streaming initialization failed",
                symbol=symbol,
                timeframe=timeframe,
                error=str(exc),
                stream_key=stream_key,
            )
            await self.send_error(
                websocket,
                request_id,
                "INTERNAL_ERROR",
                "Failed to start OHLCV streaming",
            )

    async def _stream_ohlcv_updates(
        self,
        websocket: WebSocket,
        request_id: str,
        symbol: str,
        timeframe: str,
        stream_key: str,
    ) -> None:
        last_ts: float | None = None
        try:
            try:
                from fullon_cache import OHLCVCache  # type: ignore
            except Exception:  # pragma: no cover - import path variant
                from fullon_cache.ohlcv_cache import OHLCVCache  # type: ignore

            async with OHLCVCache() as cache:  # type: ignore[call-arg]
                # Prefer a native iterator if available
                stream_iter = getattr(cache, "stream_ohlcv_updates", None)
                if callable(stream_iter):
                    async for bar in stream_iter(symbol, timeframe):  # type: ignore[misc]
                        # Expect bar format: [ts, o, h, l, c, v] or object with fields
                        if isinstance(bar, (list, tuple)) and len(bar) >= 6:
                            payload_bar = [
                                float(bar[0]),
                                float(bar[1]),
                                float(bar[2]),
                                float(bar[3]),
                                float(bar[4]),
                                float(bar[5]),
                            ]
                        else:
                            # Object-like
                            payload_bar = [
                                float(
                                    getattr(bar, "timestamp", getattr(bar, "time", 0.0))
                                ),
                                float(getattr(bar, "open", 0.0)),
                                float(getattr(bar, "high", 0.0)),
                                float(getattr(bar, "low", 0.0)),
                                float(getattr(bar, "close", 0.0)),
                                float(getattr(bar, "volume", 0.0)),
                            ]

                        msg = {
                            "request_id": request_id,
                            "action": "ohlcv_update",
                            "result": {
                                "stream_key": stream_key,
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "bar": payload_bar,
                            },
                        }
                        await websocket.send_text(json.dumps(msg))
                else:
                    # Fallback: lightweight polling of the latest bar
                    while True:
                        try:
                            getter = getattr(cache, "get_latest_ohlcv_bars", None)
                            latest: list[list[float]] | None
                            if callable(getter):
                                try:
                                    latest = await getter(symbol, timeframe, 1)  # type: ignore[misc]
                                except TypeError:
                                    latest = await getter(symbol=symbol, timeframe=timeframe, count=1)  # type: ignore[misc]
                            else:
                                get_all = getattr(cache, "get_ohlcv_bars", None)
                                if callable(get_all):
                                    try:
                                        all_bars = await get_all(symbol, timeframe)  # type: ignore[misc]
                                    except TypeError:
                                        all_bars = await get_all(symbol=symbol, timeframe=timeframe)  # type: ignore[misc]
                                    latest = (all_bars or [])[-1:]
                                else:
                                    latest = None
                        except Exception:
                            latest = None

                        if latest:
                            bar = latest[0]
                            ts = (
                                float(bar[0])
                                if isinstance(bar, (list, tuple))
                                else None
                            )
                            if ts is not None and ts != last_ts:
                                msg = {
                                    "request_id": request_id,
                                    "action": "ohlcv_update",
                                    "result": {
                                        "stream_key": stream_key,
                                        "symbol": symbol,
                                        "timeframe": timeframe,
                                        "bar": [
                                            float(bar[0]),
                                            float(bar[1]),
                                            float(bar[2]),
                                            float(bar[3]),
                                            float(bar[4]),
                                            float(bar[5]),
                                        ],
                                    },
                                }
                                await websocket.send_text(json.dumps(msg))
                                last_ts = ts

                        await asyncio.sleep(0.5)
        except asyncio.CancelledError:  # pragma: no cover - cancellation timing
            logger.info("OHLCV streaming cancelled", stream_key=stream_key)
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error("OHLCV streaming error", error=str(exc), stream_key=stream_key)

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
