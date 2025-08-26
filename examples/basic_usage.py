#!/usr/bin/env python3
"""
Basic WebSocket Cache API Usage Example

This shows the desired WebSocket context manager pattern for fullon_cache_api.
This is a PROTOTYPE - actual WebSocket implementation comes later.

Desired Usage Pattern:
    async with fullon_cache_api() as handler:
        # One-shot queries via WebSocket
        ticker = await handler.get_ticker("binance", "BTC/USDT")
        
        # Real-time streams via WebSocket (async iterators)
        async for update in handler.stream_tickers("binance", ["BTC/USDT"]):
            print(f"Live: {update['price']}")
"""

import asyncio
import time
from typing import AsyncIterator, Dict, Any


class MockWebSocketCacheAPI:
    """
    MOCK implementation showing the desired WebSocket API pattern.
    This demonstrates the interface we want to build.
    """
    
    def __init__(self, ws_url: str = "ws://localhost:8000"):
        self.ws_url = ws_url
        print(f"📡 Mock connecting to: {ws_url}")

    async def __aenter__(self):
        print("🔌 Mock WebSocket connected")
        await asyncio.sleep(0.1)  # Simulate connection time
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔌 Mock WebSocket disconnected")

    # READ-ONLY Query Operations (await response)
    async def get_ticker(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Mock get ticker via WebSocket query."""
        print(f"🔍 Query: get_ticker({exchange}, {symbol})")
        await asyncio.sleep(0.05)  # Simulate WebSocket round-trip
        return {
            "symbol": symbol,
            "exchange": exchange,
            "price": 47000.50,
            "volume": 1250.0,
            "timestamp": time.time()
        }

    async def get_order_status(self, order_id: str) -> str:
        """Mock get order status via WebSocket query."""
        print(f"🔍 Query: get_order_status({order_id})")
        await asyncio.sleep(0.05)
        return "filled"

    async def get_queue_length(self, exchange: str) -> int:
        """Mock get queue length via WebSocket query."""
        print(f"🔍 Query: get_queue_length({exchange})")
        await asyncio.sleep(0.05)
        return 42

    async def is_blocked(self, exchange: str, symbol: str) -> str:
        """Mock check if blocked via WebSocket query."""
        print(f"🔍 Query: is_blocked({exchange}, {symbol})")
        await asyncio.sleep(0.05)
        return None  # Not blocked

    async def get_bots(self) -> Dict[str, Dict[str, Any]]:
        """Mock get all bots via WebSocket query."""
        print("🔍 Query: get_bots()")
        await asyncio.sleep(0.05)
        return {
            "bot_1001": {"status": "running", "name": "ScalpBot"},
            "bot_1002": {"status": "paused", "name": "GridBot"}
        }

    # Stream Operations (async iterators - NO CALLBACKS!)
    async def stream_tickers(self, exchange: str, symbols: list[str]) -> AsyncIterator[Dict[str, Any]]:
        """Mock live ticker stream via WebSocket."""
        print(f"📡 Stream: ticker updates for {exchange}: {symbols}")
        
        # Simulate live ticker updates
        for i in range(10):  # Mock 10 updates
            for symbol in symbols:
                await asyncio.sleep(0.5)  # Simulate real-time updates
                yield {
                    "symbol": symbol,
                    "exchange": exchange, 
                    "price": 47000 + (i * 10) + hash(symbol) % 100,
                    "volume": 1000 + i * 50,
                    "timestamp": time.time(),
                    "update_id": i
                }

    async def stream_order_queue(self, exchange: str) -> AsyncIterator[Dict[str, Any]]:
        """Mock live order queue stream via WebSocket."""
        print(f"📡 Stream: order queue updates for {exchange}")
        
        # Simulate queue size changes
        for i in range(5):
            await asyncio.sleep(1.0)
            yield {
                "exchange": exchange,
                "queue_size": 50 - i * 5,
                "processing_rate": 10.5,
                "timestamp": time.time()
            }


# Convenience function (desired pattern)
def fullon_cache_api(ws_url: str = "ws://localhost:8000") -> MockWebSocketCacheAPI:
    """Create mock WebSocket cache API client."""
    return MockWebSocketCacheAPI(ws_url)


async def demo_query_operations():
    """Demo one-shot query operations."""
    print("\n🔍 === Query Operations Demo ===")
    
    async with fullon_cache_api() as handler:
        # Ticker queries
        ticker = await handler.get_ticker("binance", "BTC/USDT")
        print(f"✅ Ticker: {ticker['symbol']} @ ${ticker['price']}")
        
        # Order queries  
        status = await handler.get_order_status("order_12345")
        print(f"✅ Order status: {status}")
        
        queue_size = await handler.get_queue_length("binance")
        print(f"✅ Queue size: {queue_size}")
        
        # Bot queries
        blocked = await handler.is_blocked("binance", "BTC/USDT")
        print(f"✅ Blocked: {blocked or 'None'}")
        
        bots = await handler.get_bots()
        print(f"✅ Bots: {len(bots)} active")


async def demo_streaming_operations():
    """Demo real-time streaming operations."""
    print("\n📡 === Streaming Operations Demo ===")
    
    async with fullon_cache_api() as handler:
        print("🔄 Starting ticker stream...")
        
        # Stream ticker updates (async iterator - NO CALLBACKS!)
        async for ticker_update in handler.stream_tickers("binance", ["BTC/USDT", "ETH/USDT"]):
            print(f"📈 Live: {ticker_update['symbol']} @ ${ticker_update['price']}")
            
            # Demo: break after 5 updates
            if ticker_update.get('update_id', 0) >= 4:
                print("🛑 Stopping ticker stream")
                break


async def demo_concurrent_streams():
    """Demo multiple concurrent streams."""
    print("\n🚀 === Concurrent Streams Demo ===")
    
    async with fullon_cache_api() as handler:
        
        async def ticker_monitor():
            async for update in handler.stream_tickers("binance", ["BTC/USDT"]):
                print(f"📊 Ticker: ${update['price']}")
                if update.get('update_id', 0) >= 2:
                    break
        
        async def queue_monitor():
            async for update in handler.stream_order_queue("binance"):
                print(f"📋 Queue: {update['queue_size']} orders")
        
        # Run both streams concurrently
        await asyncio.gather(
            ticker_monitor(),
            queue_monitor()
        )


async def main():
    """Main demo runner."""
    print("🚀 fullon_cache_api WebSocket Demo")
    print("=================================")
    print("📝 This shows the DESIRED WebSocket API pattern")
    print("🔧 Actual WebSocket implementation comes later")
    
    try:
        # Demo query operations
        await demo_query_operations()
        
        # Demo streaming operations  
        await demo_streaming_operations()
        
        # Demo concurrent operations
        await demo_concurrent_streams()
        
        print("\n✅ All demos completed successfully!")
        print("🎯 This is the WebSocket API pattern we want to build!")
        
    except KeyboardInterrupt:
        print("\n🔄 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())