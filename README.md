# 🚀 fullon_cache_api

[![Tests](https://github.com/ingmarAvocado/fullon_cache_api/workflows/Tests/badge.svg)](https://github.com/ingmarAvocado/fullon_cache_api/actions)
[![Coverage](https://codecov.io/gh/ingmarAvocado/fullon_cache_api/branch/main/graph/badge.svg)](https://codecov.io/gh/ingmarAvocado/fullon_cache_api)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

**WebSocket-Based Cache API for fullon_cache with LRRS-compliant architecture for real-time read-only cache operations**

A focused, LRRS-compliant (Little, Responsible, Reusable, Separate) library that provides a complete **read-only** WebSocket API for Redis cache operations. Every fullon_cache **read operation** is exposed via secure, high-performance WebSocket transport with async iterator patterns.

**🔍 READ-ONLY WEBSOCKET API**: This library **only** exposes data retrieval operations from Redis cache via real-time WebSocket connections. No updates, inserts, or write operations are in scope.

## ✨ Features

- **📊 Complete Cache Read Coverage** - Every fullon_cache read operation exposed via WebSocket API
- **⚡ Real-Time WebSocket Streaming** - Built for live cache data streaming with async iterators (NO CALLBACKS!)
- **🔄 High Performance** - uvloop optimization, async throughout, WebSocket connection pooling
- **🧪 100% Test Coverage** - TDD-driven development with comprehensive WebSocket tests
- **📡 WebSocket Transport** - Real-time cache operations via WebSocket with context managers
- **🐳 Docker Ready** - Production-ready WebSocket server containerization
- **🔄 CI/CD Pipeline** - Automated testing, linting, and deployment

## 🏗️ Architecture

### LRRS Compliance

Following LRRS principles for maximum ecosystem integration:

- **Little**: Single purpose - READ-ONLY Redis cache data WebSocket API
- **Responsible**: Clear separation between WebSocket handlers, validation, and read-only cache operations  
- **Reusable**: Works with any fullon_cache deployment, composable WebSocket server patterns
- **Separate**: Zero coupling to other systems beyond fullon_cache + fullon_log dependencies

### Fullon Ecosystem Integration

This library is designed to integrate seamlessly with the broader fullon trading ecosystem via WebSocket transport:

```
┌─────────────────────────────────────────────────────────────────┐
│                  Fullon Trading System Ecosystem               │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  📊 HTTP APIs   │  🗄️ HTTP APIs   │  📡 WebSocket API           │
│                 │                 │                             │
│ fullon_ohlcv_api│ fullon_orm_api  │ fullon_cache_api            │
│                 │                 │                             │
│ Historical data │ Persistent      │ Real-time cache streams     │
│ Time-series     │ Trade records   │ Live ticker feeds           │
│ OHLCV analysis  │ Positions       │ Real-time order queues     │
│                 │ Portfolio data  │ Live bot coordination       │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Transport Protocol Benefits

**🎯 Clear Separation of Concerns**
- `HTTP https://api.fullon.com/market/` - Historical & analytical data (READ-ONLY)
- `HTTP https://api.fullon.com/db/` - Persistent application data (CRUD operations)  
- `WS ws://cache-server:8765/` - Real-time & temporary data streaming (READ-ONLY)

**📚 WebSocket Benefits**
- Real-time data streaming with async iterators (NO CALLBACKS!)
- Efficient WebSocket connection management with context managers
- Live cache data feeds with automatic reconnection

```
fullon_cache_api/
├── src/fullon_cache_api/
│   ├── __init__.py              # Library exports: fullon_cache_api, CacheWebSocketServer
│   ├── websocket_server.py      # Main WebSocket server for cache operations
│   ├── websocket_client.py      # WebSocket client library
│   └── cache_handlers/          # Cache operation handlers
│       ├── tick_handler.py      # Ticker cache operations
│       ├── account_handler.py   # Account cache operations
│       ├── order_handler.py     # Order cache operations
│       ├── bot_handler.py       # Bot cache operations
│       ├── trade_handler.py     # Trade cache operations
│       ├── ohlcv_handler.py     # OHLCV cache operations
│       └── process_handler.py   # Process monitoring operations
├── examples/                    # Working WebSocket examples
│   ├── basic_usage.py           # WebSocket context manager demo
│   ├── example_tick_cache.py    # Working ticker WebSocket example
│   └── run_all.py               # Run all examples with selection
├── tests/                       # Comprehensive test suite
└── docs/                        # Additional documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13
- Poetry for dependency management
- Redis for cache storage
- Access to fullon_cache package

### Installation

```bash
# Clone the repository
git clone https://github.com/ingmarAvocado/fullon_cache_api.git
cd fullon_cache_api

# Setup development environment
make setup

# Configure Redis connection
cp .env.example .env
# Edit .env with your Redis settings
```

### Configuration

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8765
LOG_LEVEL=INFO
```

### Run the WebSocket Server

```bash
# Development WebSocket server
make dev

# Production WebSocket server  
make prod

# Run WebSocket examples
python examples/basic_usage.py
python examples/example_tick_cache.py
```

## 📖 Usage Examples

### WebSocket Context Manager Pattern

```python
from fullon_cache_api import fullon_cache_api
import asyncio

# WebSocket context manager for cache operations
async def main():
    async with fullon_cache_api() as handler:
        # One-shot queries via WebSocket
        ticker = await handler.get_ticker("binance", "BTC/USDT")
        print(f"Price: ${ticker['price']}")
        
        # Real-time streaming with async iterators (NO CALLBACKS!)
        async for update in handler.stream_tickers("binance", ["BTC/USDT"]):
            print(f"Live: {update['price']}")
            break  # Demo: stop after first update

asyncio.run(main())
```

### WebSocket Account Operations

```python
from fullon_cache_api import fullon_cache_api

async def account_operations():
    async with fullon_cache_api() as handler:
        # Get user positions via WebSocket
        positions = await handler.get_positions(1001)  # user_id
        print(f"Positions: {positions}")
        
        # Get account balances via WebSocket
        balance = await handler.get_balance(1001, "BTC")
        print(f"BTC Balance: {balance}")
        
        # Real-time position streaming
        async for position_update in handler.stream_positions(1001):
            print(f"Position Update: {position_update}")
            break  # Demo: stop after first update

asyncio.run(account_operations())
```

### WebSocket Order Operations

```python
from fullon_cache_api import fullon_cache_api

async def order_operations():
    async with fullon_cache_api() as handler:
        # Get order status via WebSocket
        order_status = await handler.get_order_status("order123")
        print(f"Order Status: {order_status}")
        
        # Get order queue metrics via WebSocket
        queue_size = await handler.get_queue_length("binance")
        print(f"Queue Size: {queue_size}")
        
        # Real-time order queue streaming
        async for queue_update in handler.stream_order_queue("binance"):
            print(f"Queue Update: {queue_update}")
            break  # Demo: stop after first update

asyncio.run(order_operations())
```

### WebSocket Bot Operations

```python
from fullon_cache_api import fullon_cache_api

async def bot_operations():
    async with fullon_cache_api() as handler:
        # Get bot coordination status via WebSocket
        bot_status = await handler.get_bot_status("bot123")
        print(f"Bot Status: {bot_status}")
        
        # Check exchange blocking status via WebSocket
        blocking_status = await handler.is_blocked("binance", "BTC/USDT")
        print(f"Blocked by: {blocking_status or 'None'}")
        
        # Get all bots via WebSocket
        all_bots = await handler.get_bots()
        print(f"All Bots: {all_bots}")
        
        # Real-time bot status streaming
        async for bot_update in handler.stream_bot_status():
            print(f"Bot Update: {bot_update}")
            break  # Demo: stop after first update

asyncio.run(bot_operations())
```

### WebSocket Trade Operations

```python
from fullon_cache_api import fullon_cache_api

async def trade_operations():
    async with fullon_cache_api() as handler:
        # Get trade data via WebSocket
        trades = await handler.get_trades("BTC/USDT", "binance")
        print(f"Trades: {len(trades)} found")
        
        # Get trade status via WebSocket
        trade_status = await handler.get_trade_status("trade_key_123")
        print(f"Trade Status: {trade_status}")
        
        # Real-time trade streaming
        async for trade_update in handler.stream_trade_updates("binance"):
            print(f"Trade Update: {trade_update}")
            break  # Demo: stop after first update

asyncio.run(trade_operations())
```

## 🔌 WebSocket Server Usage

### WebSocket Server Setup

```python
from fullon_cache_api import CacheWebSocketServer
import asyncio

async def main():
    # Create WebSocket server instance
    server = CacheWebSocketServer(
        host="localhost",
        port=8765
    )
    
    # Start the WebSocket server
    await server.start()
    print("WebSocket cache server running on ws://localhost:8765")
    
    # Keep server running
    try:
        await server.wait_for_completion()
    except KeyboardInterrupt:
        await server.stop()

asyncio.run(main())
```

### WebSocket Client Integration

```python
from fullon_cache_api import fullon_cache_api
import asyncio

# WebSocket client for cache operations
async def websocket_client_example():
    # Connect to WebSocket cache server
    async with fullon_cache_api("ws://cache-server:8765") as handler:
        # Real-time ticker monitoring
        async for ticker in handler.stream_tickers("binance", ["BTC/USDT"]):
            print(f"Live Price: ${ticker['price']}")
            
            # Get current order queue status
            queue_size = await handler.get_queue_length("binance")
            if queue_size < 10:
                print(f"Low queue: {queue_size} orders")
                break

asyncio.run(websocket_client_example())
```

### Multi-Service Architecture

```python
# Fullon Trading System with Protocol Separation

# WebSocket Cache Server (Real-time data)
from fullon_cache_api import CacheWebSocketServer

# HTTP Database API (Persistent data)
from fullon_orm_api import DatabaseHTTPServer

# HTTP Market Data API (Historical data)
from fullon_ohlcv_api import MarketDataHTTPServer

async def start_all_services():
    # WebSocket server for real-time cache data
    cache_server = CacheWebSocketServer(host="0.0.0.0", port=8765)
    await cache_server.start()
    print("WebSocket Cache Server: ws://localhost:8765")
    
    # HTTP servers would start separately
    # Database API: http://localhost:8000/db/
    # Market API: http://localhost:8001/market/
    
    # Results in clean protocol separation:
    # ws://cache-server:8765           - Real-time cache data
    # http://db-server:8000/db/        - Persistent records
    # http://market-server:8001/market/ - Historical data
    
    await cache_server.wait_for_completion()

asyncio.run(start_all_services())
```

## 📊 WebSocket Operations (READ-ONLY)

### WebSocket Operations (Direct)

When using the WebSocket client, operations are accessible directly:
- **get_ticker(exchange, symbol)** - Get ticker from cache via WebSocket
- **get_all_tickers(exchange)** - Get all tickers for exchange via WebSocket
- **get_order_status(order_id)** - Get order status from cache via WebSocket
- **get_bot_status(bot_id)** - Get bot coordination status via WebSocket

### WebSocket Cache Operations

**⚡ Query Operations** (await response)
- **get_ticker(exchange, symbol)** - Ticker data from Redis via WebSocket
- **get_all_tickers(exchange)** - All tickers for exchange via WebSocket
- **get_positions(user_id)** - Account positions via WebSocket
- **get_balance(user_id, currency)** - Account balances via WebSocket
- **get_order_status(order_id)** - Order status from cache via WebSocket
- **get_queue_length(exchange)** - Order queue metrics via WebSocket
- **get_bot_status(bot_id)** - Bot coordination status via WebSocket
- **is_blocked(exchange, symbol)** - Exchange blocking status via WebSocket
- **get_trades(symbol, exchange)** - Trade data from cache via WebSocket
- **get_latest_ohlcv_bars(symbol, timeframe)** - Cached OHLCV data via WebSocket
- **get_system_health()** - Process monitoring via WebSocket

**📡 Streaming Operations** (async iterators - NO CALLBACKS!)
- **stream_tickers(exchange, symbols)** - Real-time ticker updates
- **stream_positions(user_id)** - Live position updates
- **stream_order_queue(exchange)** - Real-time queue updates
- **stream_bot_status()** - Live bot status updates
- **stream_trade_updates(exchange)** - Real-time trade stream
- **stream_ohlcv(symbol, timeframe)** - Live OHLCV updates
- **stream_process_health()** - Real-time system monitoring

**🗄️ Database Operations** (HTTP) - *via fullon_orm_api*
- **GET** `http://db-server/trades/` - Persistent trade records  
- **POST** `http://db-server/trades/` - Store trade records
- **GET** `http://db-server/positions/` - Trading positions

**📊 Market Data Operations** (HTTP) - *via fullon_ohlcv_api*
- **GET** `http://market-server/trades/{exchange}/{symbol}` - Historical trade data
- **GET** `http://market-server/candles/{exchange}/{symbol}/{timeframe}` - OHLCV candles
- **GET** `http://market-server/exchanges` - Available exchanges

### WebSocket System Operations

- **ping()** - WebSocket connection health check
- **get_system_health()** - System status via WebSocket
- **WebSocket Server** - Built-in WebSocket server with connection management
- **Examples** - Working code examples in `examples/` directory

## 🧪 Testing

```bash
# Run all WebSocket tests
make test

# Run tests with coverage
make test-cov

# Run comprehensive test suite (required before PR)
./run_test.py

# Run specific test category
poetry run pytest tests/test_websocket_server.py -v
poetry run pytest tests/integration/test_websocket_workflows.py -v

# Test WebSocket examples
python examples/basic_usage.py
python examples/example_tick_cache.py
```

## 🛠️ Development

```bash
# Install dependencies
make install

# Format code
make format

# Run linting
make lint

# Run all checks
make check

# Start development WebSocket server with auto-reload
make dev

# Run WebSocket examples
python examples/basic_usage.py
```

## 📈 Performance Features

### WebSocket Optimizations (READ-ONLY)
- **Connection Reuse**: Long-lived WebSocket connections for multiple operations
- **Async Iterators**: Memory-efficient streaming without callback overhead
- **Message Batching**: Efficient JSON message serialization
- **Concurrent Streams**: Multiple async iterators per WebSocket connection

### Real-Time Architecture (READ-ONLY)
- **Async Throughout**: All WebSocket operations are non-blocking
- **Connection Pooling**: Optimized WebSocket connection management
- **Stream Multiplexing**: Single connection supports multiple data streams
- **Live Monitoring**: Real-time cache performance via WebSocket streams

## 📊 WebSocket Message Models

### WebSocket Request Message
```python
{
    "request_id": "uuid-string",
    "operation": "get_ticker",
    "params": {
        "exchange": "binance",
        "symbol": "BTC/USDT"
    }
}
```

### WebSocket Response Message
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

### WebSocket Stream Message
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

### WebSocket Error Message
```python
{
    "request_id": "uuid-string",
    "success": False,
    "error_code": "CACHE_MISS",
    "error": "Ticker BTC/USDT not found in binance cache"
}
```

## 🐳 Deployment

### Docker

```bash
# Build WebSocket server image
make docker-build

# Run WebSocket server container
make docker-run
```

### Production Deployment

```bash
# Install production dependencies only
poetry install --no-dev

# Run with production WebSocket server
poetry run python -m fullon_cache_api.websocket_server --host 0.0.0.0 --port 8765
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following TDD principles
4. Ensure all tests pass: `./run_test.py`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow TDD - write tests first
- Maintain 100% test coverage
- Use `./run_test.py` before any commit
- Follow existing code style (Black + Ruff)
- Update documentation for new features
- All operations must be read-only
- Use async iterators for streaming (NO CALLBACKS!)
- Always use WebSocket context managers

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the excellent [fullon_cache](https://github.com/ingmarAvocado/fullon_cache) Redis cache library
- Uses [WebSockets](https://websockets.readthedocs.io/) for real-time async communication
- Follows LRRS architectural principles for maximum reusability
- Optimized for [Redis](https://redis.io/) cache performance with real-time streaming

## 📞 Support

- 📚 Check the [CLAUDE.md](CLAUDE.md) for development assistance  
- 📋 See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for architecture details
- 🐛 Report issues on [GitHub Issues](https://github.com/ingmarAvocado/fullon_cache_api/issues)
- 💬 Discussion on [GitHub Discussions](https://github.com/ingmarAvocado/fullon_cache_api/discussions)

---

**Built with ❤️ using LRRS principles and WebSocket transport for real-time cache performance with async iterators (NO CALLBACKS!)** ⚡🚀📡