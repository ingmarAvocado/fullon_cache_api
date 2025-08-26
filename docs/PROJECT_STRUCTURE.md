# 🏗️ fullon_cache_api Project Structure

**LRRS-Compliant Cache Data WebSocket API Architecture**

## 📋 Project Overview

fullon_cache_api is a WebSocket-based library that exposes **read-only** Redis cache operations via WebSocket transport with async iterator patterns. It follows LRRS (Little, Responsible, Reusable, Separate) principles and provides real-time cache data streaming without callbacks.

**🔍 READ-ONLY API**: This library **only** exposes data retrieval operations from Redis cache. No updates, inserts, or write operations are in scope.

**📡 WebSocket Transport**: Real-time cache operations via WebSocket with async iterators (NO CALLBACKS!).

## 🏗️ Architecture Principles

### LRRS Compliance
- **Little**: Single purpose - READ-ONLY cache data WebSocket API
- **Responsible**: Secure WebSocket API for read-only Redis cache operations  
- **Reusable**: WebSocket server patterns work with any fullon_cache deployment
- **Separate**: Zero coupling beyond fullon_cache + fullon_log dependencies

### Design Philosophy
- **WebSocket First**: Real-time cache operations via WebSocket transport
- **Async Iterators**: Streaming data with NO CALLBACKS pattern
- **Cache Focused**: Optimized for read-only Redis cache data patterns
- **Read-Only Operations**: No write/update/insert operations in scope
- **Context Managers**: Clean resource management with `async with` patterns
- **Self-Contained**: Examples include complete WebSocket server implementations

## 📁 Directory Structure

```
fullon_cache_api/
├── CLAUDE.md                    # 🤖 Development guidelines for LLMs
├── PROJECT_STRUCTURE.md         # 📋 This architecture documentation
├── README.md                    # 📖 Project overview and usage guide
├── Makefile                     # 🔧 Development automation commands
├── pyproject.toml              # 📦 Modern Python project configuration
├── run_test.py                 # 🧪 Comprehensive test runner script
│
├── src/                        # 📂 Source code directory (future WebSocket server)
│   └── fullon_cache_api/      # 📦 Main package
│       ├── __init__.py         # 🔌 Library exports and public API
│       ├── websocket_server.py # 📡 WebSocket server for cache operations
│       ├── websocket_client.py # 📡 WebSocket client library
│       └── cache_handlers/     # 🗄️ Cache operation handlers
│           ├── __init__.py
│           ├── tick_handler.py    # 📈 Ticker cache operations
│           ├── account_handler.py # 👤 Account cache operations
│           ├── order_handler.py   # 📋 Order cache operations
│           ├── bot_handler.py     # 🤖 Bot cache operations
│           ├── trade_handler.py   # 💹 Trade cache operations
│           ├── ohlcv_handler.py   # 🕯️ OHLCV cache operations
│           └── process_handler.py # ⚙️ Process monitoring operations
│
├── examples/                  # 📚 Working WebSocket examples
│   ├── README.md              # 📖 Examples documentation
│   ├── basic_usage.py         # 🚀 WebSocket context manager demo
│   ├── example_tick_cache.py  # 📈 Working ticker WebSocket example
│   ├── example_account_cache.py # 👤 Account cache WebSocket operations
│   ├── example_bot_cache.py   # 🤖 Bot cache WebSocket operations
│   ├── example_orders_cache.py # 📋 Orders cache WebSocket operations
│   ├── example_trades_cache.py # 💹 Trades cache WebSocket operations
│   ├── example_ohlcv_cache.py # 🕯️ OHLCV cache WebSocket operations
│   ├── example_process_cache.py # ⚙️ Process cache WebSocket operations
│   └── run_all.py             # 🏃 Run all examples with selection
│
├── tests/                     # 🧪 Comprehensive test suite
│   ├── __init__.py
│   ├── conftest.py            # ⚙️ Pytest configuration and fixtures
│   ├── test_main.py           # 🔬 Main module tests
│   ├── unit/                  # 🔬 Unit tests directory
│   │   └── __init__.py
│   └── integration/           # 🔗 Integration tests directory
│       └── __init__.py
│
└── docs/                      # 📖 Additional documentation
    └── (additional docs)
```

## 🔌 WebSocket Library Interface

### Public API Exports (`__init__.py`)
```python
from .websocket_client import fullon_cache_api
from .websocket_server import CacheWebSocketServer

# Context manager for WebSocket cache operations
def fullon_cache_api(ws_url: str = "ws://localhost:8765"):
    """Create WebSocket cache API client."""
    pass

# Public exports
__all__ = ["fullon_cache_api", "CacheWebSocketServer"]
```

### Primary Usage Patterns
```python
# WebSocket context manager pattern:
async with fullon_cache_api() as handler:
    ticker = await handler.get_ticker("binance", "BTC/USDT")
    
    # Real-time streaming with async iterators (NO CALLBACKS!)
    async for update in handler.stream_tickers("binance", ["BTC/USDT"]):
        print(f"Live: {update['price']}")

# Server startup for testing:
from fullon_cache_api import CacheWebSocketServer
server = CacheWebSocketServer()
await server.start()
```

## 🏗️ Core Components

### 1. CacheWebSocketServer (`websocket_server.py`)
**Main WebSocket server providing cache operations via WebSocket transport.**

```python
class CacheWebSocketServer:
    """
    WebSocket server that exposes fullon_cache operations.
    
    Features:
    - Real-time cache operations via WebSocket
    - Async request/response patterns
    - Automatic fullon_cache integration
    - Connection management and error handling
    - Support for multiple concurrent clients
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        pass
    
    async def start(self):
        """Start the WebSocket server."""
        pass
        
    async def stop(self):
        """Stop the WebSocket server."""
        pass
        
    async def handle_client(self, websocket):
        """Handle individual client connections."""
        pass
```

### 2. Cache Handler Architecture (`cache_handlers/`)
**Modular WebSocket operation handlers by cache type.**

#### Ticker Cache Handler (`tick_handler.py`) - **READ-ONLY**
- `get_ticker(exchange, symbol)` - Specific ticker data
- `get_all_tickers(exchange)` - All tickers for exchange
- `stream_tickers(exchange, symbols)` - Real-time ticker stream
- `ping()` - Connection health check

#### Account Cache Handler (`account_handler.py`) - **READ-ONLY**
- `get_balance(user_id, exchange)` - Account balance data
- `get_positions(user_id)` - User account positions
- `stream_positions(user_id)` - Real-time position updates

#### Order Cache Handler (`order_handler.py`) - **READ-ONLY**
- `get_order_status(order_id)` - Order status from cache
- `get_queue_length(exchange)` - Order queue metrics
- `stream_order_queue(exchange)` - Real-time queue updates

#### Bot Cache Handler (`bot_handler.py`) - **READ-ONLY**
- `get_bot_status(bot_id)` - Bot coordination status
- `is_blocked(exchange, symbol)` - Exchange blocking status
- `get_bots()` - All bot statuses
- `stream_bot_status()` - Real-time bot updates

#### Trade Cache Handler (`trade_handler.py`) - **READ-ONLY**
- `get_trades(symbol, exchange)` - Trade data from cache
- `get_trade_status(trade_key)` - Trade processing status
- `stream_trade_updates(exchange)` - Real-time trade stream

#### OHLCV Cache Handler (`ohlcv_handler.py`) - **READ-ONLY**
- `get_latest_ohlcv_bars(symbol, timeframe)` - Cached OHLCV data
- `stream_ohlcv(symbol, timeframe)` - Real-time OHLCV updates

#### Process Cache Handler (`process_handler.py`) - **READ-ONLY**
- `get_system_health()` - System health status
- `get_active_processes()` - Active process data
- `stream_process_health()` - Real-time system monitoring

### 3. WebSocket Message Patterns
**JSON message structures for WebSocket request/response.**

#### Request Message Format
```python
{
    "request_id": "uuid-string",
    "operation": "get_ticker",  # Operation name
    "params": {
        "exchange": "binance",
        "symbol": "BTC/USDT"
    }
}
```

#### Response Message Format
```python
{
    "request_id": "uuid-string",
    "success": True,
    "result": {
        "symbol": "BTC/USDT",
        "exchange": "binance", 
        "price": 47000.50,
        "volume": 1250.0,
        "timestamp": 1640995200.123
    }
}
```

#### Stream Message Format
```python
{
    "type": "ticker_update",
    "exchange": "binance",
    "symbol": "BTC/USDT",
    "price": 47100.25,
    "volume": 1275.0,
    "timestamp": 1640995201.456,
    "update_id": 123
}
```

### 4. WebSocket Client (`websocket_client.py`)
**Async WebSocket client with context manager support.**

#### WebSocket Client API
```python
class WebSocketCacheClient:
    """WebSocket client for cache operations."""
    
    async def __aenter__(self):
        """Connect to WebSocket server."""
        pass
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Disconnect from WebSocket server."""
        pass
    
    async def get_ticker(self, exchange: str, symbol: str) -> Dict[str, Any]:
        """Get ticker data via WebSocket."""
        pass
    
    async def stream_tickers(self, exchange: str, symbols: List[str]) -> AsyncIterator[Dict[str, Any]]:
        """Stream ticker updates via async iterator."""
        async for update in self._stream_handler("tickers", {"exchange": exchange, "symbols": symbols}):
            yield update
```

## 🔄 WebSocket Data Flow Architecture

### WebSocket Cache Request Processing Flow
```
1. WebSocket Connection → CacheWebSocketServer
2. JSON Message → Request Parsing & Validation
3. Handler → fullon_cache Instance Creation (READ-ONLY)
4. Cache → Redis Query (READ-ONLY)
5. Redis → Cached Data Return (NO MODIFICATIONS)
6. Cache → Data Processing & Formatting
7. Handler → JSON Response Construction
8. WebSocket → JSON Response to Client
```

### WebSocket Streaming Data Flow
```
1. Stream Request → WebSocket Connection
2. Async Iterator → Continuous Data Generation
3. Cache Operations → Real-time Redis Queries
4. Stream Updates → JSON Message Broadcasting
5. Client Async Iterator → Message Reception
6. NO CALLBACKS → Clean async/await patterns
```

### Integration with Existing Systems
```
1. WebSocket Server Startup
2. fullon_cache Integration via Context Managers
3. Real-time Data Streaming to Multiple Clients
4. Clean Resource Management with async/await
5. Self-contained Testing with Auto-starting Servers
```

## 🌐 WebSocket Transport Benefits

### Real-Time Cache Data Access
```python
# WebSocket-based cache operations with async iterators:
async with fullon_cache_api("ws://cache-server:8765") as cache:
    # One-shot queries
    ticker = await cache.get_ticker("binance", "BTC/USDT")
    
    # Real-time streaming (NO CALLBACKS!)
    async for update in cache.stream_tickers("binance", ["BTC/USDT", "ETH/USDT"]):
        process_ticker_update(update)
        
    # Concurrent streams
    async def monitor_multiple():
        tasks = [
            cache.stream_tickers("binance", ["BTC/USDT"]),
            cache.stream_order_queue("binance"),
            cache.stream_bot_status()
        ]
        async for update in asyncio.as_completed(tasks):
            handle_update(update)
```

### Transport Protocol Separation
```
WebSocket ws://cache-server:8765    # Real-time cache data (THIS PROJECT)
HTTP https://api.fullon.com/orm/    # Database operations (fullon_orm_api)
HTTP https://api.fullon.com/market/ # Market data (fullon_ohlcv_api)
```

## 🔄 fullon_cache Integration

### WebSocket Server Cache Integration Pattern
```python
# WebSocket server integrates directly with fullon_cache:
from fullon_cache import TickCache, OrdersCache, BotCache

class CacheWebSocketServer:
    async def handle_ticker_request(self, params):
        async with TickCache() as cache:
            ticker = await cache.get_ticker(params['exchange'], params['symbol'])
            return ticker
    
    async def handle_queue_request(self, params):
        async with OrdersCache() as cache:
            queue_size = await cache.get_queue_size(params['exchange'])
            return queue_size
    
    async def handle_bot_request(self, params):
        async with BotCache() as cache:
            bot_status = await cache.get_bot_status(params['bot_id'])
            return bot_status
```

### WebSocket Cache Connection Management
- **Context Managers**: Automatic fullon_cache resource cleanup
- **Connection Reuse**: Efficient Redis connection handling per WebSocket
- **Health Monitoring**: Built-in WebSocket and Redis health checks
- **Real-Time Updates**: Live cache data streaming with async iterators

## 🧪 WebSocket Testing Architecture

### Test Organization
```
tests/
├── conftest.py              # WebSocket test fixtures and Redis setup
├── test_main.py             # Integration tests for WebSocket components
├── unit/                    # Isolated component testing
│   ├── test_websocket_server.py # WebSocket server unit tests
│   ├── test_websocket_client.py # WebSocket client unit tests
│   └── test_cache_handlers.py   # Cache handler unit tests
└── integration/             # End-to-end workflow testing  
    ├── test_websocket_workflows.py # Complete WebSocket operation flows
    └── test_cache_integration.py   # fullon_cache integration tests
```

### WebSocket TDD Approach
- **Tests First**: Write WebSocket tests before implementation
- **100% Coverage**: All WebSocket and cache operations tested
- **`./run_test.py`**: Comprehensive test runner with WebSocket testing
- **Async Testing**: All tests use pytest-asyncio for WebSocket operations
- **Real Servers**: WebSocket server testing with actual connections
- **Cache Testing**: Real Redis testing via fullon_cache integration

## 🚀 Development Workflow

### Setup and Development
```bash
# Project setup
make setup          # Install dependencies, setup pre-commit hooks

# Development server  
make dev           # Start WebSocket development server

# Code quality
make format        # Format code with Black + Ruff
make lint         # Run linting checks
make test         # Run WebSocket test suite
make check        # Run all quality checks

# Comprehensive validation
./run_test.py     # Full test suite including WebSocket tests
```

### WebSocket Integration Example
```python
# WebSocket cache client usage
from fullon_cache_api import fullon_cache_api

async def trading_application():
    async with fullon_cache_api("ws://cache-server:8765") as cache:
        # Real-time ticker monitoring
        async for ticker in cache.stream_tickers("binance", ["BTC/USDT"]):
            if should_trade(ticker):
                # Get current order queue status
                queue_size = await cache.get_queue_length("binance")
                if queue_size < 10:
                    place_order(ticker)
                    break

# Result: Real-time cache-driven trading application
# ws://cache-server:8765 -> WebSocket connection
# Async iterators for real-time data (NO CALLBACKS!)
# Context manager resource management
```

## 📈 WebSocket Performance Considerations

### WebSocket-Specific Optimizations
- **Connection Reuse**: Long-lived WebSocket connections for multiple operations
- **Async Iterators**: Memory-efficient streaming without callback overhead
- **Message Batching**: Efficient JSON message serialization
- **Concurrent Streams**: Multiple async iterators per WebSocket connection

### Real-Time Scaling Patterns
- **Multiple Clients**: WebSocket server handles concurrent connections
- **Stream Multiplexing**: Single connection supports multiple data streams
- **Live Monitoring**: Real-time cache performance via WebSocket streams
- **Auto-Reconnect**: WebSocket client resilience and connection management

---

**This WebSocket-based architecture enables real-time, high-performance cache data access with async iterator patterns, providing superior streaming capabilities while maintaining clean resource management and fullon_cache integration.** 🚀