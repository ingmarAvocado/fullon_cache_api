"""
FastAPI router providing the accounts WebSocket endpoint.
"""

from fastapi import APIRouter, WebSocket

from ..handlers.account_handler import AccountWebSocketHandler

router = APIRouter()
account_handler = AccountWebSocketHandler()


@router.websocket("/ws/accounts/{connection_id}")
async def accounts_websocket_endpoint(websocket: WebSocket, connection_id: str) -> None:
    await account_handler.handle_connection(websocket, connection_id)
