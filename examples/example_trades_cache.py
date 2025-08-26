#!/usr/bin/env python3
"""
Trades Cache WebSocket Operations Example

PROTOTYPE - Shows desired WebSocket API pattern. 
Will be updated to use real WebSocket server like fullon_cache examples.

Usage:
    python example_trades_cache.py --operations basic --trades 100
    python example_trades_cache.py --operations analytics --verbose
"""

import argparse
import asyncio
import random
import sys
import time
from typing import AsyncIterator, Dict, Any, Optional


class MockTradesWebSocketAPI:
    """MOCK - will be replaced with real WebSocket client."""
    
    def __init__(self, ws_url: str = "ws://localhost:8000"):
        self.ws_url = ws_url

    async def __aenter__(self):
        print("🔌 Trades WebSocket connected (MOCK)")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔌 Trades WebSocket disconnected (MOCK)")

    # READ-ONLY Trade Operations
    async def get_trades(self, symbol: str, exchange: str) -> list:
        await asyncio.sleep(0.02)
        trade_count = random.randint(5, 20)
        trades = []
        
        for i in range(trade_count):
            trades.append({
                "trade_id": 10000 + i,
                "symbol": symbol,
                "exchange": exchange,
                "side": random.choice(["buy", "sell"]),
                "volume": round(random.uniform(0.1, 2.0), 8),
                "price": round(random.uniform(20000, 50000), 2),
                "timestamp": time.time() - random.uniform(0, 3600)
            })
        
        return trades

    async def get_trade_status(self, trade_key: str) -> Optional[str]:
        await asyncio.sleep(0.02)
        return random.choice(["pending", "confirmed", "settled", "failed"])

    # Streaming Operations
    async def stream_trade_updates(self, exchange: str) -> AsyncIterator[Dict[str, Any]]:
        print(f"📡 Streaming trade updates for {exchange} (MOCK)")
        for i in range(10):
            await asyncio.sleep(0.8)
            yield {
                "type": "trade_update",
                "exchange": exchange,
                "symbol": random.choice(["BTC/USDT", "ETH/USDT"]),
                "side": random.choice(["buy", "sell"]),
                "volume": round(random.uniform(0.1, 1.0), 8),
                "price": round(random.uniform(30000, 50000), 2),
                "update_id": i
            }


def fullon_cache_api(ws_url: str = "ws://localhost:8000") -> MockTradesWebSocketAPI:
    return MockTradesWebSocketAPI(ws_url)


async def basic_trade_operations(trade_count: int = 100, verbose: bool = False) -> bool:
    print("💱 === Basic Trade WebSocket Operations (MOCK) ===")
    
    try:
        async with fullon_cache_api() as handler:
            symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
            exchanges = ["binance", "kraken"]
            
            total_trades = 0
            for exchange in exchanges:
                for symbol in symbols:
                    trades = await handler.get_trades(symbol, exchange)
                    total_trades += len(trades)
                    if verbose:
                        print(f"   💱 {exchange}:{symbol}: {len(trades)} trades")
            
            print(f"✅ Retrieved {total_trades} total trades")
            return True
            
    except Exception as e:
        print(f"❌ Basic trade operations failed: {e}")
        return False


async def streaming_demo(verbose: bool = False) -> bool:
    print("📡 === Trade Streaming Demo (MOCK) ===")
    
    try:
        async with fullon_cache_api() as handler:
            update_count = 0
            async for update in handler.stream_trade_updates("binance"):
                update_count += 1
                if verbose:
                    side_emoji = "📈" if update["side"] == "buy" else "📉"
                    print(f"   {side_emoji} {update['symbol']}: {update['side']} "
                          f"{update['volume']:.4f} @ ${update['price']:.2f}")
                
                if update.get("update_id", 0) >= 5:
                    break
            
            print(f"✅ Streaming completed: {update_count} trade updates")
            return True
            
    except Exception as e:
        print(f"❌ Trade streaming failed: {e}")
        return False


async def run_demo(args) -> bool:
    print("🚀 fullon_cache_api Trades WebSocket Demo (MOCK)")
    print("===============================================")
    print("🔧 Will be updated to use real WebSocket server")
    
    results = {}
    
    if args.operations in ["basic", "all"]:
        results["basic"] = await basic_trade_operations(args.trades, args.verbose)
    
    if args.operations in ["streaming", "all"]:
        results["streaming"] = await streaming_demo(args.verbose)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n📊 Success: {success_count}/{total_count} operations")
    return success_count == total_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operations", choices=["basic", "streaming", "all"], default="all")
    parser.add_argument("--trades", type=int, default=100)
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    try:
        success = asyncio.run(run_demo(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🔄 Demo interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()