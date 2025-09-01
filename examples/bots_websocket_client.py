"""Minimal example client for Bots WebSocket API.

Usage:
    poetry run python examples/bots_websocket_client.py
"""

import asyncio
import json

import websockets


async def main() -> None:
    uri = "ws://127.0.0.1:8000/ws/bots/example"
    async with websockets.connect(uri) as ws:
        # Query blocking status
        await ws.send(
            json.dumps(
                {
                    "action": "is_blocked",
                    "request_id": "blk1",
                    "params": {"exchange": "binance", "symbol": "BTC/USDT"},
                }
            )
        )
        print("is_blocked:", await ws.recv())

        # Start stream (all bots)
        await ws.send(
            json.dumps(
                {
                    "action": "stream_bot_status",
                    "request_id": "s1",
                    "params": {},
                }
            )
        )
        # Print a couple of updates
        for _ in range(2):
            print("update:", await ws.recv())


if __name__ == "__main__":
    asyncio.run(main())

