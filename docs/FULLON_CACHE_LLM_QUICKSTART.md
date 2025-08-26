# Fullon Cache - LLM Quick Start Guide for WebSocket Integration

**Redis-based high-performance caching system for cryptocurrency trading operations, designed for WebSocket-based real-time access patterns.**

## Installation

```bash
poetry add git+ssh://git@github.com/ingmarAvocado/fullon_cache.git
```

## Essential Imports

```python
from fullon_cache import (
    TickCache,      # Real-time market data
    OrdersCache,    # Order queue management  
    TradesCache,    # Trade data and analytics
    AccountCache,   # Account balances and positions
    BotCache,       # Bot coordination and blocking
    OHLCVCache     # Candlestick/OHLCV data
)
```

## Basic Usage Patterns

### Ticker Data (Real-time Prices)
```python
async with TickCache() as cache:
    # Set ticker data
    from fullon_orm.models import Tick, Symbol
    import time
    
    # Create symbol object
    symbol = Symbol(symbol="BTC/USDT", cat_ex_id=1, base="BTC", quote="USDT")
    
    # Create tick with all required data
    tick = Tick(
        symbol="BTC/USDT",
        exchange="binance", 
        price=50000.0,
        volume=100.0,
        bid=49999.0,
        ask=50001.0,
        time=time.time()
    )
    await cache.set_ticker(tick)  # Only pass the tick object
    
    # Get ticker data
    ticker = await cache.get_ticker(symbol, "binance")
    print(f"Price: ${ticker.price}")
```

### Order Queue Management
```python
async with OrdersCache() as cache:
    # Push order to queue
    from fullon_orm.models import Order
    order = Order(order_id=12345, symbol="BTC/USDT", side="buy", volume=0.1)
    await cache.push_open_order("binance", order)
    
    # Pop order from queue (FIFO)
    next_order = await cache.pop_open_order("binance", timeout=5)
    if next_order:
        print(f"Processing order: {next_order.order_id}")
```

### Trade Data Management
```python
async with TradesCache() as cache:
    # Store trade data
    from fullon_orm.models import Trade
    trade = Trade(
        trade_id=67890,
        symbol="BTC/USDT",
        side="sell",
        volume=0.05,
        price=50500.0,
        cost=2525.0
    )
    await cache.push_trade("binance", trade)
    
    # Retrieve trades
    trades = await cache.get_trades("BTC/USDT", "binance")
    print(f"Found {len(trades)} trades")
```

### Account & Position Tracking
```python
async with AccountCache() as cache:
    # Set account balance
    balance_data = {
        "BTC": {"total": 1.5, "free": 1.2, "used": 0.3},
        "USDT": {"total": 10000, "free": 8500, "used": 1500}
    }
    await cache.set_user_balances(1001, balance_data)  # exchange_id
    
    # Get balance
    btc_balance = await cache.get_user_balance(1001, "BTC")
    print(f"BTC Balance: {btc_balance}")
    
    # Set position
    from fullon_orm.models import Position
    position = Position(
        symbol="BTC/USDT",
        volume=0.5,
        cost=25000.0,
        price=50000.0
    )
    await cache.set_position(1001, position)
```

### Bot Coordination (Prevent Conflicts)
```python
async with BotCache() as cache:
    # Block exchange/symbol for exclusive access
    success = await cache.block_exchange("binance", "BTC/USDT", bot_id=101)
    
    # Check if blocked by another bot
    blocking_bot = await cache.is_blocked("binance", "BTC/USDT") 
    if blocking_bot:
        print(f"Blocked by bot: {blocking_bot}")
    
    # Release block when done
    await cache.unblock_exchange("binance", "BTC/USDT")
```

### OHLCV Data (Candlesticks)
```python
async with OHLCVCache() as cache:
    # Store OHLCV bars [timestamp, open, high, low, close, volume]
    bars = [
        [1640995200, 47000.0, 47200.0, 46800.0, 47100.0, 150.5],
        [1640995260, 47100.0, 47300.0, 46900.0, 47200.0, 200.3]
    ]
    await cache.update_ohlcv_bars("BTCUSD", "1m", bars)
    
    # Retrieve latest bars
    latest_bars = await cache.get_latest_ohlcv_bars("BTCUSD", "1m", count=100)
    print(f"Retrieved {len(latest_bars)} bars")
```

## Configuration (.env file)

```env
REDIS_HOST=localhost
REDIS_PORT=6379  
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
```

## Testing Examples

```bash
# Run all cache examples
poetry run python src/fullon_cache/examples/run_all.py

# Run specific example
poetry run python src/fullon_cache/examples/example_tick_cache.py --operations basic

# Test individual cache
poetry run python src/fullon_cache/examples/example_account_cache.py --operations all --verbose
```

## Architecture Hierarchy

```
BaseCache (Redis connection)
└── ProcessCache (monitoring)
    └── ExchangeCache (exchange metadata)  
        └── SymbolCache (symbol info)
            └── TickCache (real-time tickers)
                └── AccountCache (balances/positions)
                    ├── OrdersCache (order queues)
                    │   └── TradesCache (trade data)
                    └── BotCache (bot coordination)
                        └── OHLCVCache (candlestick data)
```

## Complete Method Reference

📖 **See [METHOD_REFERENCE.md](METHOD_REFERENCE.md)** for complete list of all methods demonstrated in examples, organized by cache type with signatures and usage patterns.

## Key Points for WebSocket Integration with LLMs

1. **Always use async context managers**: `async with Cache() as cache:`
2. **All methods are async**: Use `await` for all cache operations
3. **Uses fullon_orm models**: Import from `fullon_orm.models` (Trade, Order, Position, etc.)
4. **WebSocket-Ready**: All cache operations integrate seamlessly with WebSocket transport
5. **Real-time Streaming**: Supports async iterator patterns for live data streaming
6. **Method reference available**: All working methods documented in `METHOD_REFERENCE.md`
7. **Examples available**: Check `src/fullon_cache/examples/` for working code patterns
8. **Self-documenting**: Run `help(fullon_cache)` for complete API reference
9. **No mocking in tests**: Uses real Redis for reliability
10. **Environment-based config**: Uses `.env` files, no complex configuration

### WebSocket Usage Patterns

**For WebSocket servers using fullon_cache:**

```python
# WebSocket handler pattern:
import json
from fullon_cache import TickCache

class WebSocketCacheHandler:
    async def handle_ticker_request(self, websocket, message):
        params = message.get('params', {})
        exchange = params.get('exchange')
        symbol = params.get('symbol')
        
        # Direct fullon_cache integration
        async with TickCache() as cache:
            ticker = await cache.get_ticker(exchange, symbol)
        
        # Send WebSocket response
        response = {
            "request_id": message.get('request_id'),
            "success": True,
            "result": {
                "symbol": symbol,
                "exchange": exchange,
                "price": ticker.price if ticker else None,
                "timestamp": ticker.timestamp if ticker else None
            }
        }
        await websocket.send(json.dumps(response))
    
    async def handle_stream_tickers(self, websocket, message):
        params = message.get('params', {})
        exchange = params.get('exchange')
        symbols = params.get('symbols', [])
        
        # Real-time streaming with async iterator
        async with TickCache() as cache:
            # Note: stream_ticker_updates is conceptual - actual streaming
            # would use polling or Redis pub/sub patterns
            while True:
                for symbol in symbols:
                    ticker = await cache.get_ticker(exchange, symbol)
                    if ticker:
                        update = {
                            "type": "ticker_update",
                            "exchange": exchange,
                            "symbol": symbol,
                            "price": ticker.price,
                            "volume": ticker.volume,
                            "timestamp": ticker.timestamp
                        }
                        await websocket.send(json.dumps(update))
                await asyncio.sleep(1)  # Polling interval
```

**For WebSocket clients using fullon_cache data:**

```python
# WebSocket client consuming cache data:
async def websocket_cache_client():
    async with websockets.connect("ws://cache-server:8765") as websocket:
        # Request ticker data
        request = {
            "request_id": "req_001",
            "operation": "get_ticker",
            "params": {
                "exchange": "binance",
                "symbol": "BTC/USDT"
            }
        }
        await websocket.send(json.dumps(request))
        
        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get('success'):
            print(f"Ticker: ${data['result']['price']}")
```

This library is designed to be immediately usable by LLMs for WebSocket-based cache access without external documentation - all APIs, examples, and help are built into the package itself.