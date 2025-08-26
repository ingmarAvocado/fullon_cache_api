#!/usr/bin/env python3
"""
Ticker Cache WebSocket Operations Example

Real WebSocket implementation that demonstrates the desired API pattern.
This shows how fullon_cache operations would work via WebSocket transport.

Usage:
    python example_tick_cache_working.py --operations basic --exchanges binance,kraken  
    python example_tick_cache_working.py --operations streaming --verbose
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
import uuid
from typing import AsyncIterator, Dict, Any, Optional

import websockets
# WebSocket server import - no need for deprecated WebSocketServerProtocol

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("fullon.cache_api.examples.tick")


class TickerWebSocketServer:
    """Simple WebSocket server for ticker operations."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.ticker_cache = {}  # Simple in-memory cache for demo
        
    async def start(self):
        """Start the WebSocket server."""
        logger.info("Starting WebSocket server: host=%s, port=%s", self.host, self.port)
        
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info("WebSocket server started")
        
    async def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            logger.info("Stopping WebSocket server")
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def handle_client(self, websocket):
        """Handle new WebSocket client connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info("Client connected: %s", client_id)
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.handle_request(data)
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    error_response = {"error": "Invalid JSON format", "request_id": None}
                    await websocket.send(json.dumps(error_response))
                    
                except Exception as e:
                    logger.error("Request handling failed: client_id=%s, error=%s", client_id, str(e))
                    error_response = {
                        "error": str(e),
                        "request_id": data.get("request_id") if isinstance(data, dict) else None
                    }
                    await websocket.send(json.dumps(error_response))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected: %s", client_id)
    
    async def handle_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle individual WebSocket request."""
        request_id = data.get("request_id")
        operation = data.get("operation")
        params = data.get("params", {})
        
        try:
            if operation == "ping":
                return {"result": True, "request_id": request_id, "success": True}
                
            elif operation == "set_ticker":
                ticker_key = f"{params['exchange']}:{params['symbol']}"
                self.ticker_cache[ticker_key] = {
                    "symbol": params["symbol"],
                    "exchange": params["exchange"],
                    "price": params["price"],
                    "volume": params.get("volume", 0),
                    "bid": params.get("bid"),
                    "ask": params.get("ask"),
                    "last": params.get("last"),
                    "time": time.time()
                }
                return {"result": True, "request_id": request_id, "success": True}
                
            elif operation == "get_ticker":
                ticker_key = f"{params['exchange']}:{params['symbol']}"
                ticker = self.ticker_cache.get(ticker_key)
                return {"result": ticker, "request_id": request_id, "success": True}
                
            else:
                return {"error": f"Unknown operation: {operation}", "request_id": request_id, "success": False}
                
        except Exception as e:
            logger.error("Operation failed: operation=%s, error=%s", operation, str(e))
            return {"error": str(e), "request_id": request_id, "success": False}


class TickerWebSocketClient:
    """Simple WebSocket client for ticker operations."""
    
    def __init__(self, ws_url: str = "ws://localhost:8765"):
        self.ws_url = ws_url
        self.websocket = None
        self.connected = False
        
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    async def connect(self):
        """Connect to WebSocket server."""
        try:
            logger.info("Connecting to WebSocket server: %s", self.ws_url)
            self.websocket = await websockets.connect(self.ws_url)
            self.connected = True
            logger.info("WebSocket connection established")
        except Exception as e:
            logger.error("Failed to connect to WebSocket server: url=%s, error=%s", self.ws_url, str(e))
            raise ConnectionError(f"Could not connect to WebSocket server: {e}")
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket:
            logger.info("Disconnecting from WebSocket server")
            await self.websocket.close()
            self.connected = False
    
    async def send_request(self, operation: str, params: Dict[str, Any] = None) -> Any:
        """Send request to WebSocket server and get response."""
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected to WebSocket server")
        
        request_id = str(uuid.uuid4())
        request = {
            "request_id": request_id,
            "operation": operation,
            "params": params or {}
        }
        
        try:
            await self.websocket.send(json.dumps(request))
            response_str = await self.websocket.recv()
            response = json.loads(response_str)
            
            if not response.get("success", False) or "error" in response:
                error_msg = response.get("error", "Unknown error")
                raise RuntimeError(f"WebSocket operation failed: {error_msg}")
            
            return response.get("result")
            
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            raise ConnectionError("WebSocket connection closed")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")
    
    async def ping(self) -> bool:
        """Test connection."""
        return await self.send_request("ping", {})
    
    async def get_ticker(self, exchange: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get ticker data."""
        params = {"exchange": exchange, "symbol": symbol}
        return await self.send_request("get_ticker", params)
    
    async def set_ticker(self, symbol: str, exchange: str, price: float, volume: float = 0) -> bool:
        """Set ticker data."""
        params = {
            "symbol": symbol,
            "exchange": exchange, 
            "price": price,
            "volume": volume,
            "bid": price * 0.999,
            "ask": price * 1.001,
            "last": price
        }
        return await self.send_request("set_ticker", params)
    
    async def stream_tickers(self, exchange: str, symbols: list[str]) -> AsyncIterator[Dict[str, Any]]:
        """Stream ticker updates (mock implementation)."""
        logger.info("Starting ticker stream: exchange=%s, symbols=%s", exchange, symbols)
        
        for i in range(10):
            await asyncio.sleep(1.0)
            for symbol in symbols:
                base_prices = {"BTC/USDT": 47000, "ETH/USDT": 3100, "ADA/USDT": 1.2}
                base_price = base_prices.get(symbol, 100)
                current_price = base_price * (1 + (i * 0.001))
                
                yield {
                    "type": "ticker_update",
                    "exchange": exchange,
                    "symbol": symbol,
                    "price": current_price,
                    "volume": 1000 + (i * 100),
                    "timestamp": time.time(),
                    "update_id": i
                }


async def start_test_server():
    """Start the WebSocket test server."""
    server = TickerWebSocketServer()
    await server.start()
    return server


async def test_cache_connection(client) -> bool:
    """Test WebSocket cache connection."""
    try:
        await client.ping()
        print("✅ WebSocket cache connection successful")
        return True
    except Exception as e:
        print("❌ WebSocket cache connection failed")
        print(f"   Error: {e}")
        return False


async def basic_ticker_operations(client, exchanges: list[str], verbose: bool = False) -> bool:
    """Demonstrate basic ticker operations via WebSocket."""
    print("📊 === Basic Ticker WebSocket Operations ===")
    
    try:
        symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        
        # Set up test ticker data
        print("🔄 Setting up test ticker data...")
        for exchange in exchanges:
            for symbol in symbols:
                base_prices = {"BTC/USDT": 47000, "ETH/USDT": 3100, "ADA/USDT": 1.2}
                base_price = base_prices.get(symbol, 100)
                current_price = base_price * (1 + random.uniform(-0.02, 0.02))
                
                await client.set_ticker(symbol, exchange, current_price, 
                                       volume=random.uniform(100, 1000))
        
        print(f"🔄 Getting ticker data for {len(symbols)} symbols on {len(exchanges)} exchanges...")
        
        ticker_count = 0
        for symbol in symbols:
            for exchange in exchanges:
                ticker = await client.get_ticker(exchange, symbol)
                ticker_count += 1
                
                if verbose and ticker:
                    print(f"   📈 {exchange}: {symbol} @ ${ticker['price']:,.2f}")
        
        print(f"✅ Retrieved {ticker_count} tickers via WebSocket")
        return True
        
    except Exception as e:
        logger.error("Basic ticker operations failed: %s", str(e))
        print(f"❌ Basic ticker operations failed: {e}")
        return False


async def streaming_ticker_demo(client, symbols: list[str], duration: int = 15, 
                              verbose: bool = False) -> bool:
    """Demonstrate real-time ticker streaming."""
    print("📡 === Real-Time Ticker Streaming Demo ===")
    
    try:
        print(f"🔄 Streaming {symbols} for {duration}s...")
        
        start_time = time.time()
        update_count = 0
        
        async for ticker_update in client.stream_tickers("binance", symbols):
            update_count += 1
            
            if verbose:
                print(f"   📊 {ticker_update['symbol']}: ${ticker_update['price']:,.2f} "
                      f"(Vol: {ticker_update['volume']:.2f})")
            elif update_count % 5 == 0:
                print(f"   📈 Received {update_count} ticker updates")
            
            elapsed = time.time() - start_time
            if elapsed >= duration or ticker_update.get("update_id", 0) >= 8:
                print(f"🛑 Stopping stream after {elapsed:.1f}s, {update_count} updates")
                break
        
        print(f"✅ Streaming completed: {update_count} updates")
        return True
        
    except Exception as e:
        logger.error("Ticker streaming failed: %s", str(e))
        print(f"❌ Ticker streaming failed: {e}")
        return False


async def run_demo(args) -> bool:
    """Main demo runner."""
    print("🚀 fullon_cache_api Ticker WebSocket Demo")
    print("========================================")
    print("📝 Working WebSocket implementation")
    print("🔧 Shows async iterator patterns (NO CALLBACKS!)")
    
    # Start WebSocket server
    server = await start_test_server()
    
    try:
        # Wait for server to be ready
        await asyncio.sleep(1.0)
        
        # Create and test client connection
        client = TickerWebSocketClient()
        async with client:
            print("\n🔌 Testing WebSocket cache connection...")
            if not await test_cache_connection(client):
                return False
            
            start_time = time.time()
            results = {}
            
            # Parse parameters
            exchanges = [e.strip() for e in args.exchanges.split(",")] if args.exchanges else ["binance", "kraken"]
            symbols = [s.strip() for s in args.symbols.split(",")] if args.symbols else ["BTC/USDT", "ETH/USDT"]
            
            # Run selected operations
            if args.operations in ["basic", "all"]:
                results["basic"] = await basic_ticker_operations(client, exchanges, args.verbose)
            
            if args.operations in ["streaming", "all"]:
                results["streaming"] = await streaming_ticker_demo(client, symbols, args.duration, args.verbose)
            
            # Summary
            elapsed = time.time() - start_time
            success_count = sum(results.values())
            total_count = len(results)
            
            print("\n📊 === Summary ===")
            print(f"⏱️  Total time: {elapsed:.2f}s")
            print(f"✅ Success: {success_count}/{total_count} operations")
            
            if success_count == total_count:
                print("🎉 All ticker WebSocket operations completed!")
                print("🎯 Real WebSocket server with cache-like operations works!")
                return True
            else:
                failed = [op for op, success in results.items() if not success]
                print(f"❌ Failed operations: {', '.join(failed)}")
                return False
                
    except Exception as e:
        logger.error("Demo failed: %s", str(e))
        print(f"❌ Demo failed: {e}")
        return False
        
    finally:
        await server.stop()


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--operations",
        choices=["basic", "streaming", "all"],
        default="all",
        help="Operations to demonstrate (default: all)"
    )
    parser.add_argument(
        "--exchanges",
        default="binance,kraken", 
        help="Comma-separated exchanges (default: binance,kraken)"
    )
    parser.add_argument(
        "--symbols",
        default="BTC/USDT,ETH/USDT",
        help="Comma-separated symbols (default: BTC/USDT,ETH/USDT)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Streaming duration in seconds (default: 10)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(run_demo(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🔄 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()