"""
FastAPI router providing the process WebSocket endpoint.
"""

from fastapi import APIRouter, WebSocket

from ..handlers.process_handler import ProcessWebSocketHandler

router = APIRouter()
process_handler = ProcessWebSocketHandler()


@router.websocket("/ws/process/{connection_id}")
async def process_websocket_endpoint(websocket: WebSocket, connection_id: str) -> None:
    await process_handler.handle_connection(websocket, connection_id)
