"""
FastAPI router providing the bots WebSocket endpoint.
"""

from fastapi import APIRouter, WebSocket

from ..handlers.bot_handler import BotWebSocketHandler

router = APIRouter()
bot_handler = BotWebSocketHandler()


@router.websocket("/ws/bots/{connection_id}")
async def bots_websocket_endpoint(websocket: WebSocket, connection_id: str) -> None:
    await bot_handler.handle_connection(websocket, connection_id)
