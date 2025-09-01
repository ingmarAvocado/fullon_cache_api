"""
Ticker WebSocket handler implementing read-only ticker operations.

Implements:
- get_ticker: fetch a single ticker snapshot
- get_all_tickers: fetch all tickers for an exchange
- stream_tickers: start real-time streaming via async iterator (no callbacks)

Design constraints:
- Read-only operations only
- Uses fullon_log for structured logging
- Uses fullon_cache TickCache sessions with async context mgmt
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


def _safe_get_component_logger(name: str):
    try:
        from fullon_log import get_component_logger as _gcl  # type: ignore

        return _gcl(name)
    except Exception:  # pragma: no cover - environment dependent
        import logging

        class _KVLLoggerAdapter:
            def __init__(self, base):
                self._base = base

            def _fmt(self, msg: str, **kwargs):
                if kwargs:
                    kv = " ".join(f"{k}={v}" for k, v in kwargs.items())
                    return f"{msg} | {kv}"
                return msg

            def debug(self, msg, *args, **kwargs):
                self._base.debug(self._fmt(msg, **kwargs), *args)

            def info(self, msg, *args, **kwargs):
                self._base.info(self._fmt(msg, **kwargs), *args)

            def warning(self, msg, *args, **kwargs):
                self._base.warning(self._fmt(msg, **kwargs), *args)

            def error(self, msg, *args, **kwargs):
                self._base.error(self._fmt(msg, **kwargs), *args)

        return _KVLLoggerAdapter(logging.getLogger(name))


logger = _safe_get_component_logger("fullon.api.cache.tickers")


class TickerWebSocketHandler:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.streaming_tasks: dict[str, asyncio.Task[Any]] = {}

    async def handle_connection(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(
            "Ticker WebSocket connected", connection_id=connection_id, handler="tickers"
        )

        try:
            while True:
                message = await websocket.receive_text()
                await self.route_ticker_message(websocket, message, connection_id)
        except WebSocketDisconnect:
            logger.info(
                "Ticker WebSocket disconnected",
                connection_id=connection_id,
                handler="tickers",
            )
        finally:
            await self.cleanup_connection(connection_id)

    async def route_ticker_message(
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

        if action == "get_ticker":
            await self.handle_get_ticker(websocket, request_id, params, connection_id)
        elif action == "get_all_tickers":
            await self.handle_get_all_tickers(
                websocket, request_id, params, connection_id
            )
        elif action == "stream_tickers":
            await self.handle_stream_tickers(
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

    async def handle_get_ticker(
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
            "Get ticker operation started",
            exchange=exchange,
            symbol=symbol,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            # Lazy import to avoid hard dependency at import time
            from fullon_cache import TickCache  # type: ignore

            async with TickCache() as cache:  # type: ignore[call-arg]
                # TickCache signature is (symbol, exchange)
                ticker = await cache.get_ticker(symbol, exchange)

            if ticker:
                result = {
                    "symbol": getattr(ticker, "symbol", symbol),
                    "exchange": getattr(ticker, "exchange", exchange),
                    "price": float(getattr(ticker, "price", 0.0)),
                    "volume": float(getattr(ticker, "volume", 0.0)),
                    "timestamp": float(
                        getattr(ticker, "time", getattr(ticker, "timestamp", 0.0))
                    ),
                    "bid": float(getattr(ticker, "bid", 0.0)),
                    "ask": float(getattr(ticker, "ask", 0.0)),
                    "change_24h": float(getattr(ticker, "change_24h", 0.0)),
                }
                response = {
                    "request_id": request_id,
                    "action": "get_ticker",
                    "success": True,
                    "result": result,
                }
                logger.info(
                    "Get ticker operation completed",
                    exchange=exchange,
                    symbol=symbol,
                    cache_hit=True,
                    request_id=request_id,
                )
            else:
                response = {
                    "request_id": request_id,
                    "action": "get_ticker",
                    "success": False,
                    "error_code": "TICKER_NOT_FOUND",
                    "error": f"Ticker {symbol} not found for {exchange}",
                }

            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get ticker operation failed",
                exchange=exchange,
                symbol=symbol,
                error=str(exc),
                request_id=request_id,
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve ticker data"
            )

    async def handle_get_all_tickers(
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
            "Get all tickers operation started",
            exchange=exchange,
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            from fullon_cache import TickCache  # type: ignore

            items: list[dict[str, Any]] = []
            async with TickCache() as cache:  # type: ignore[call-arg]
                # Prefer new API
                get_all = getattr(cache, "get_all_tickers", None)
                if callable(get_all):
                    try:
                        tickers = await get_all(exchange_name=exchange)  # type: ignore[misc]
                    except TypeError:
                        tickers = await get_all()  # type: ignore[misc]
                else:
                    # Legacy API: get all and filter
                    get_any = getattr(cache, "get_tickers", None)
                    tickers = await get_any() if callable(get_any) else []  # type: ignore[misc]

                for t in tickers or []:
                    ex_name = getattr(t, "exchange", getattr(t, "exchange_name", None))
                    rec = {
                        "symbol": getattr(t, "symbol", None),
                        "exchange": ex_name or exchange,
                        "price": float(getattr(t, "price", 0.0)),
                        "volume": float(getattr(t, "volume", 0.0)),
                        "timestamp": float(
                            getattr(t, "time", getattr(t, "timestamp", 0.0))
                        ),
                        "bid": float(getattr(t, "bid", 0.0)),
                        "ask": float(getattr(t, "ask", 0.0)),
                        "change_24h": float(getattr(t, "change_24h", 0.0)),
                    }
                    items.append(rec)

                # Filter by requested exchange if needed
                items = [it for it in items if str(it.get("exchange")) == str(exchange)]

            response = {
                "request_id": request_id,
                "action": "get_all_tickers",
                "success": True,
                "result": {"exchange": exchange, "tickers": items},
            }
            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get all tickers failed",
                exchange=exchange,
                error=str(exc),
                request_id=request_id,
            )
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve tickers"
            )

    async def handle_stream_tickers(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        exchange = params.get("exchange")
        symbols = params.get("symbols", [])
        if not exchange:
            await self.send_error(
                websocket, request_id, "INVALID_PARAMS", "exchange parameter required"
            )
            return

        stream_key = f"{connection_id}:{request_id}"
        try:
            task = asyncio.create_task(
                self._stream_ticker_updates(
                    websocket, request_id, exchange, symbols, stream_key
                )
            )
            self.streaming_tasks[stream_key] = task

            confirmation = {
                "request_id": request_id,
                "action": "stream_tickers",
                "success": True,
                "message": f"Streaming started for {len(symbols)} symbols on {exchange}",
                "stream_key": stream_key,
            }
            await websocket.send_text(json.dumps(confirmation))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Ticker streaming initialization failed",
                exchange=exchange,
                error=str(exc),
                stream_key=stream_key,
            )
            await self.send_error(
                websocket,
                request_id,
                "INTERNAL_ERROR",
                "Failed to start ticker streaming",
            )

    async def _stream_ticker_updates(
        self,
        websocket: WebSocket,
        request_id: str,
        exchange: str,
        symbols: list[str],
        stream_key: str,
    ) -> None:
        try:
            from fullon_cache import TickCache  # type: ignore

            async with TickCache() as cache:  # type: ignore[call-arg]
                # Prefer native async iterator if provided by cache
                stream_iter = getattr(cache, "stream_ticker_updates", None)
                if callable(stream_iter):
                    async for update in stream_iter(exchange, symbols):  # type: ignore[misc]
                        msg = {
                            "request_id": request_id,
                            "action": "ticker_update",
                            "result": {
                                "stream_key": stream_key,
                                "exchange": exchange,
                                "symbol": getattr(update, "symbol", None),
                                "price": float(getattr(update, "price", 0.0)),
                                "volume": float(getattr(update, "volume", 0.0)),
                                "timestamp": float(
                                    getattr(
                                        update,
                                        "time",
                                        getattr(update, "timestamp", 0.0),
                                    )
                                ),
                                "bid": float(getattr(update, "bid", 0.0)),
                                "ask": float(getattr(update, "ask", 0.0)),
                                "change_24h": float(getattr(update, "change_24h", 0.0)),
                            },
                        }
                        await websocket.send_text(json.dumps(msg))
                else:
                    # Fallback: lightweight polling loop (still async, no callbacks)
                    while True:
                        for symbol in symbols:
                            t = await cache.get_ticker(symbol, exchange)
                            if t:
                                msg = {
                                    "request_id": request_id,
                                    "action": "ticker_update",
                                    "result": {
                                        "stream_key": stream_key,
                                        "exchange": exchange,
                                        "symbol": getattr(t, "symbol", symbol),
                                        "price": float(getattr(t, "price", 0.0)),
                                        "volume": float(getattr(t, "volume", 0.0)),
                                        "timestamp": float(
                                            getattr(
                                                t, "time", getattr(t, "timestamp", 0.0)
                                            )
                                        ),
                                        "bid": float(getattr(t, "bid", 0.0)),
                                        "ask": float(getattr(t, "ask", 0.0)),
                                        "change_24h": float(
                                            getattr(t, "change_24h", 0.0)
                                        ),
                                    },
                                }
                                await websocket.send_text(json.dumps(msg))
                        await asyncio.sleep(0.5)
        except asyncio.CancelledError:  # pragma: no cover - cancellation timing
            logger.info("Ticker streaming cancelled", stream_key=stream_key)
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Ticker streaming error", error=str(exc), stream_key=stream_key
            )

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
