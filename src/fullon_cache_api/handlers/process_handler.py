"""
Process WebSocket handler implementing read-only process monitoring operations.

Implements:
- get_system_health: fetch system/process health snapshot
- get_active_processes: fetch list of active processes
- stream_process_health: start real-time health updates via async polling/iterator

Design constraints:
- Read-only operations only
- Uses fullon_log for structured logging
- Uses fullon_cache ProcessCache sessions with async context mgmt
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from fullon_log import get_component_logger  # type: ignore


logger = get_component_logger("fullon.api.cache.process")


class ProcessWebSocketHandler:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.streaming_tasks: dict[str, asyncio.Task[Any]] = {}

    async def handle_connection(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(
            "Process WebSocket connected", connection_id=connection_id, handler="process"
        )

        try:
            while True:
                message = await websocket.receive_text()
                await self.route_process_message(websocket, message, connection_id)
        except WebSocketDisconnect:
            logger.info(
                "Process WebSocket disconnected",
                connection_id=connection_id,
                handler="process",
            )
        finally:
            await self.cleanup_connection(connection_id)

    async def route_process_message(
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

        if action == "get_system_health":
            await self.handle_get_system_health(websocket, request_id, params, connection_id)
        elif action == "get_active_processes":
            await self.handle_get_active_processes(
                websocket, request_id, params, connection_id
            )
        elif action == "stream_process_health":
            await self.handle_stream_process_health(
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

    async def handle_get_system_health(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        logger.info(
            "Get system health started",
            request_id=request_id,
            connection_id=connection_id,
        )

        try:
            try:
                from fullon_cache import ProcessCache  # type: ignore
            except Exception:  # pragma: no cover - import path variant
                from fullon_cache.process_cache import ProcessCache  # type: ignore

            async with ProcessCache() as cache:  # type: ignore[call-arg]
                get_health = getattr(cache, "get_system_health", None)
                if callable(get_health):
                    health = await get_health()
                else:
                    # Fallback: synthesize minimal health data
                    processes = await getattr(cache, "get_active_processes")()
                    health = {
                        "overall_status": "healthy",
                        "active_processes": len(processes or []),
                        "timestamp": time.time(),
                    }

            response = {
                "request_id": request_id,
                "action": "get_system_health",
                "success": True,
                "result": health,
            }
            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error("Get system health failed", error=str(exc), request_id=request_id)
            await self.send_error(
                websocket, request_id, "CACHE_ERROR", "Failed to retrieve system health"
            )

    async def handle_get_active_processes(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        logger.info(
            "Get active processes started",
            request_id=request_id,
            connection_id=connection_id,
        )

        process_type = params.get("process_type")
        component = params.get("component")
        since_minutes = params.get("since_minutes")

        try:
            try:
                from fullon_cache import ProcessCache  # type: ignore
            except Exception:  # pragma: no cover
                from fullon_cache.process_cache import ProcessCache  # type: ignore

            items: list[dict[str, Any]] = []
            async with ProcessCache() as cache:  # type: ignore[call-arg]
                get_active = getattr(cache, "get_active_processes")
                kwargs: dict[str, Any] = {}
                if process_type is not None:
                    kwargs["process_type"] = process_type
                if component is not None:
                    kwargs["component"] = component
                if since_minutes is not None:
                    kwargs["since_minutes"] = int(since_minutes)

                processes = await get_active(**kwargs) if callable(get_active) else []

                for p in processes or []:
                    rec = {
                        "process_id": getattr(p, "process_id", getattr(p, "id", None)),
                        "name": getattr(p, "name", None),
                        "status": getattr(p, "status", None),
                        "pid": getattr(p, "pid", None),
                        "last_seen": float(
                            getattr(
                                p,
                                "last_seen",
                                getattr(p, "timestamp", time.time()),
                            )
                        ),
                    }
                    items.append(rec)

            response = {
                "request_id": request_id,
                "action": "get_active_processes",
                "success": True,
                "result": {"processes": items},
            }
            await websocket.send_text(json.dumps(response))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Get active processes failed", error=str(exc), request_id=request_id
            )
            await self.send_error(
                websocket,
                request_id,
                "CACHE_ERROR",
                "Failed to retrieve active processes",
            )

    async def handle_stream_process_health(
        self,
        websocket: WebSocket,
        request_id: str,
        params: dict[str, Any],
        connection_id: str,
    ) -> None:
        stream_key = f"{connection_id}:{request_id}"
        try:
            task = asyncio.create_task(
                self._stream_health_updates(websocket, request_id, stream_key)
            )
            self.streaming_tasks[stream_key] = task

            confirmation = {
                "request_id": request_id,
                "action": "stream_process_health",
                "success": True,
                "message": "Streaming started for process health",
                "stream_key": stream_key,
            }
            await websocket.send_text(json.dumps(confirmation))
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Process health streaming init failed",
                error=str(exc),
                stream_key=stream_key,
            )
            await self.send_error(
                websocket,
                request_id,
                "INTERNAL_ERROR",
                "Failed to start process health streaming",
            )

    async def _stream_health_updates(
        self, websocket: WebSocket, request_id: str, stream_key: str
    ) -> None:
        last_active_count: int | None = None
        try:
            try:
                from fullon_cache import ProcessCache  # type: ignore
            except Exception:  # pragma: no cover
                from fullon_cache.process_cache import ProcessCache  # type: ignore

            async with ProcessCache() as cache:  # type: ignore[call-arg]
                while True:
                    try:
                        get_active = getattr(cache, "get_active_processes")
                        processes = await get_active() if callable(get_active) else []
                        active_count = len(processes or [])
                    except Exception:
                        active_count = last_active_count if last_active_count is not None else 0

                    if active_count != last_active_count:
                        last_active_count = active_count
                        msg = {
                            "request_id": request_id,
                            "action": "process_health_update",
                            "result": {
                                "stream_key": stream_key,
                                "active_processes": active_count,
                                "timestamp": time.time(),
                            },
                        }
                        await websocket.send_text(json.dumps(msg))

                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:  # pragma: no cover - cancellation timing
            logger.info("Process health streaming cancelled", stream_key=stream_key)
        except Exception as exc:  # pragma: no cover - env dependent
            logger.error(
                "Process health streaming error", error=str(exc), stream_key=stream_key
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

