"""
FastAPI router providing the trades WebSocket endpoint.
"""

from fastapi import APIRouter, WebSocket

from ..handlers.trade_handler import TradesWebSocketHandler

router = APIRouter()
trades_handler = TradesWebSocketHandler()


@router.websocket("/ws/trades/{connection_id}")
async def trades_websocket_endpoint(websocket: WebSocket, connection_id: str) -> None:
    await trades_handler.handle_connection(websocket, connection_id)
