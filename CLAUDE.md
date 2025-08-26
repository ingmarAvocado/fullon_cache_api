# 🤖 CLAUDE.md - fullon_cache_api Development Guide

**For LLMs/Claude: Complete development guidelines for the fullon_cache_api project**

## 🎯 Project Mission

**LRRS-Compliant Library**: Create a composable WebSocket-based library that exposes **READ-ONLY** fullon_cache operations via real-time WebSocket transport with async iterator patterns, designed for building WebSocket servers and clients with clean resource management.

## 🏗️ LRRS Architecture Principles

**This project MUST follow LRRS principles:**

- **Little**: Single purpose - READ-ONLY cache data WebSocket API only
- **Responsible**: One clear job - secure WebSocket API for read-only cache operations
- **Reusable**: Works with any fullon_cache deployment, composable WebSocket server patterns
- **Separate**: Zero coupling beyond fullon_cache + fullon_log dependencies

### **Critical Design Decision: Library vs Standalone**

```python
# Library usage (PRIMARY use case):
from fullon_cache_api import fullon_cache_api, CacheWebSocketServer

# WebSocket context manager pattern:
async with fullon_cache_api() as handler:
    ticker = await handler.get_ticker("binance", "BTC/USDT")
    
    # Real-time streaming with async iterators (NO CALLBACKS!)
    async for update in handler.stream_tickers("binance", ["BTC/USDT"]):
        print(f"Live: {update['price']}")

# Server startup for testing:
server = CacheWebSocketServer()
await server.start()
```

## 📊 Cache Focus Areas

**Core Cache Operations** (using fullon_cache dependency):

### **🔍 READ-ONLY WEBSOCKET CACHE API**
**IMPORTANT**: This API **ONLY** exposes read/fetch operations via WebSocket transport. No updates, inserts, or write operations are in scope.

### **1. WebSocket Cache Data Operations**
- Real-time ticker data streaming from Redis cache - **READ ONLY**
- Live account/position data streaming from Redis - **READ ONLY**
- WebSocket-based order status and queue monitoring
- Real-time bot coordination status and exchange blocking info
- Live trade queue status and processing metrics streaming
- WebSocket OHLCV cached data retrieval and streaming
- Real-time process monitoring and health status

### **2. WebSocket Server Cache Integration Pattern**
```python
# WebSocket server integrates directly with fullon_cache:
from fullon_cache import TickCache, OrdersCache, BotCache, TradesCache, AccountCache, OHLCVCache

class CacheWebSocketServer:
    async def handle_ticker_request(self, params):
        async with TickCache() as cache:
            ticker = await cache.get_ticker(params['exchange'], params['symbol'])
            return ticker
    
    async def handle_queue_request(self, params):
        async with OrdersCache() as cache:
            queue_size = await cache.get_queue_length(params['exchange'])
            return queue_size
    
    async def handle_bot_request(self, params):
        async with BotCache() as cache:
            bot_status = await cache.is_blocked(params['exchange'], params['symbol'])
            return bot_status
    
    async def handle_stream_tickers(self, params):
        async with TickCache() as cache:
            # Real-time streaming with async iterator
            async for ticker_update in cache.stream_ticker_updates(params['exchange'], params['symbols']):
                yield {
                    "type": "ticker_update",
                    "exchange": params['exchange'],
                    "symbol": ticker_update.symbol,
                    "price": ticker_update.price,
                    "volume": ticker_update.volume,
                    "timestamp": ticker_update.timestamp
                }
```

### **3. WebSocket Operations** (via WebSocket transport)
- `get_ticker(exchange, symbol)` - Retrieve ticker data via WebSocket
- `get_all_tickers(exchange)` - All tickers for exchange via WebSocket
- `get_positions(user_id)` - Account positions from cache via WebSocket
- `get_order_status(order_id)` - Order status from Redis via WebSocket
- `get_queue_length(exchange)` - Order queue metrics via WebSocket
- `is_blocked(exchange, symbol)` - Bot coordination status via WebSocket
- `get_trades(symbol, exchange)` - Trade data from cache via WebSocket
- `get_latest_ohlcv_bars(symbol, timeframe)` - Cached OHLCV data via WebSocket
- `get_system_health()` - Process monitoring data via WebSocket

### **4. Real-time Streaming Operations** (async iterators - NO CALLBACKS!)
- `stream_tickers(exchange, symbols)` - Real-time ticker updates
- `stream_positions(user_id)` - Live position updates
- `stream_order_queue(exchange)` - Real-time queue updates
- `stream_bot_status()` - Live bot status updates
- `stream_trade_updates(exchange)` - Real-time trade stream
- `stream_ohlcv(symbol, timeframe)` - Live OHLCV updates
- `stream_process_health()` - Real-time system monitoring

## 🛠️ Architecture Overview

### **WebSocket-Based Transport Architecture**
```
┌─────────────────────────────────────────────────────────────────┐
│                    WebSocket Cache Ecosystem                   │
│                                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   HTTP APIs     │ │  WebSocket API  │ │   HTTP APIs     │   │
│  │ fullon_orm_api  │ │fullon_cache_api │ │fullon_ohlcv_api │   │
│  │   (Database)    │ │  (Real-time)    │ │  (Market Data)  │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   PostgreSQL              Redis Cache              Market APIs
    Database              WebSocket Server         (External)

# Perfect transport separation prevents conflicts:
HTTP https://api.fullon.com/orm/trades/    # Database: Trade records 
WS   ws://cache-server:8765/tickers        # Redis: Real-time cache data ← THIS PROJECT
HTTP https://api.fullon.com/market/trades/ # Market: Historical trade data
```

### **Project Structure**
```
fullon_cache_api/
├── src/fullon_cache_api/
│   ├── __init__.py              # Library exports: fullon_cache_api, CacheWebSocketServer
│   ├── websocket_server.py      # Main WebSocket server for cache operations
│   ├── websocket_client.py      # WebSocket client library
│   └── cache_handlers/          # Cache operation handlers
│       ├── __init__.py
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
│   ├── example_account_cache.py # Account cache WebSocket operations
│   ├── example_bot_cache.py     # Bot cache WebSocket operations
│   ├── example_orders_cache.py  # Orders cache WebSocket operations
│   ├── example_trades_cache.py  # Trades cache WebSocket operations
│   ├── example_ohlcv_cache.py   # OHLCV cache WebSocket operations
│   ├── example_process_cache.py # Process cache WebSocket operations
│   └── run_all.py               # Run all examples with selection
├── tests/                       # Comprehensive test suite
└── docs/                        # Additional documentation
```

## 🚀 Core Development Patterns

### **1. WebSocket Cache Operation Handler Pattern**
```python
# Standard pattern for all READ-ONLY WebSocket cache operations:
from fullon_cache import TickCache
import json

class TickerHandler:
    async def handle_get_ticker(self, websocket, message):
        params = message.get('params', {})
        exchange = params.get('exchange')
        symbol = params.get('symbol')
        
        # 1. Validate parameters
        if not exchange or not symbol:
            await websocket.send(json.dumps({
                "request_id": message.get('request_id'),
                "success": False,
                "error": "Missing exchange or symbol parameter"
            }))
            return
        
        # 2. READ-ONLY cache operation
        async with TickCache() as cache:
            ticker = await cache.get_ticker(exchange, symbol)
        
        # 3. Send WebSocket response
        response = {
            "request_id": message.get('request_id'),
            "success": True,
            "result": {
                "symbol": symbol,
                "exchange": exchange,
                "price": ticker.price if ticker else None,
                "volume": ticker.volume if ticker else None,
                "timestamp": ticker.timestamp if ticker else None
            } if ticker else None
        }
        await websocket.send(json.dumps(response))
    
    async def handle_stream_tickers(self, websocket, message):
        params = message.get('params', {})
        exchange = params.get('exchange')
        symbols = params.get('symbols', [])
        
        # Real-time streaming with async iterator (NO CALLBACKS!)
        async with TickCache() as cache:
            async for update in cache.stream_ticker_updates(exchange, symbols):
                stream_message = {
                    "type": "ticker_update",
                    "exchange": exchange,
                    "symbol": update.symbol,
                    "price": update.price,
                    "volume": update.volume,
                    "timestamp": update.timestamp,
                    "update_id": update.id
                }
                await websocket.send(json.dumps(stream_message))
```

### **2. WebSocket Connection Management**
```python
# WebSocket client context manager:
from fullon_cache_api import fullon_cache_api

class WebSocketCacheClient:
    async def __aenter__(self):
        """Connect to WebSocket server."""
        self.websocket = await websockets.connect(self.ws_url)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Disconnect from WebSocket server."""
        await self.websocket.close()

# Health check pattern
async def check_websocket_health():
    async with fullon_cache_api() as client:
        response = await client.ping()
        return response.get('status') == 'ok'

# Multiple cache operations via WebSocket
async def get_trading_status_via_websocket(exchange: str):
    async with fullon_cache_api() as client:
        # Get data via WebSocket operations
        queue_size = await client.get_queue_length(exchange)
        bots_data = await client.get_bots()
        blocked_status = await client.is_blocked(exchange, "BTC/USDT")
        
        return {
            "queue_size": queue_size, 
            "bots": bots_data,
            "blocked": blocked_status
        }
```

### **3. WebSocket Error Handling Pattern**
```python
import json

# WebSocket-specific error responses:
async def send_error_response(websocket, request_id, error_code, message):
    error_response = {
        "request_id": request_id,
        "success": False,
        "error_code": error_code,
        "error": message
    }
    await websocket.send(json.dumps(error_response))

# Common WebSocket error patterns:
# Data not found in cache
await send_error_response(websocket, request_id, "CACHE_MISS", "Data not found in cache")

# Cache service unavailable
await send_error_response(websocket, request_id, "CACHE_UNAVAILABLE", "Cache service unavailable")

# Invalid parameters
await send_error_response(websocket, request_id, "INVALID_PARAMS", "Invalid cache operation parameters")

# Connection timeout
await send_error_response(websocket, request_id, "TIMEOUT", "Cache operation timeout")
```

### **4. Logging Pattern (fullon_log)**
```python
from fullon_log import get_component_logger
import time

# Component-specific logging (REQUIRED pattern):
logger = get_component_logger("fullon.api.cache")

# Standard cache endpoint logging pattern:
async def get_ticker_with_logging(exchange: str, symbol: str):
    start_time = time.time()
    logger.info("Cache operation started", 
               operation="get_ticker", 
               exchange=exchange, 
               symbol=symbol)
    
    try:
        async with TickCache() as cache:
            ticker = await cache.get_ticker(exchange, symbol)
            cache_hit = ticker is not None
            
        duration_ms = (time.time() - start_time) * 1000
        
        # Success logging with performance metrics
        logger.info("Cache operation completed", 
                   operation="get_ticker", 
                   exchange=exchange, 
                   symbol=symbol,
                   cache_hit=cache_hit,
                   latency_ms=duration_ms,
                   status="success")
        
        return ticker
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Error logging with context
        logger.error("Cache operation failed", 
                    operation="get_ticker",
                    exchange=exchange,
                    symbol=symbol,
                    error=str(e),
                    error_type=type(e).__name__,
                    latency_ms=duration_ms,
                    status="error")
        raise

# Health check logging:
async def log_cache_health():
    try:
        async with TickCache() as cache:
            await cache.test()
        logger.info("Cache health check passed", service="redis", status="healthy")
    except Exception as e:
        logger.error("Cache health check failed", service="redis", status="unhealthy", error=str(e))

# Component initialization logging:
class FullonCacheGateway:
    def __init__(self, prefix: str = "", title: str = "fullon_cache_api"):
        self.logger = get_component_logger("fullon.api.cache.gateway")
        self.logger.info("Cache gateway initialized", prefix=prefix, title=title)
```

## 🔑 Environment Configuration

### **Required Environment Variables**
```bash
# Redis Configuration (handled by fullon_cache)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Logging (fullon-log)
LOG_LEVEL=DEBUG              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=development       # beautiful, minimal, development, detailed, trading, json
LOG_CONSOLE=true             # Enable console output
LOG_COLORS=true              # Enable colored output
LOG_FILE_PATH=/tmp/fullon/cache_api.log
LOG_ROTATION=100 MB          # Optional: file rotation
LOG_RETENTION=7 days         # Optional: retention period
```

## 📋 WebSocket Cache Operation Coverage Requirements

**Every READ-ONLY fullon_cache operation MUST have a WebSocket handler:**

### **TickCache Operations (READ-ONLY)** - Ticker Handler
- `get_ticker(exchange, symbol)` - Ticker data retrieval via WebSocket
- `get_all_tickers(exchange)` - All tickers for exchange via WebSocket
- `stream_tickers(exchange, symbols)` - Real-time ticker updates
- `ping()` - Connection health check

### **AccountCache Operations (READ-ONLY)** - Account Handler  
- `get_balance(user_id, exchange)` - Account balance data via WebSocket
- `get_positions(user_id)` - User account positions via WebSocket
- `stream_positions(user_id)` - Real-time position updates

### **OrdersCache Operations (READ-ONLY)** - Order Handler
- `get_order_status(order_id)` - Order status from cache via WebSocket
- `get_queue_length(exchange)` - Order queue metrics via WebSocket
- `stream_order_queue(exchange)` - Real-time queue updates

### **BotCache Operations (READ-ONLY)** - Bot Handler
- `get_bot_status(bot_id)` - Bot coordination status via WebSocket
- `is_blocked(exchange, symbol)` - Exchange blocking status via WebSocket
- `get_bots()` - All bot statuses via WebSocket
- `stream_bot_status()` - Real-time bot updates

### **TradesCache Operations (READ-ONLY)** - Trade Handler
- `get_trades(symbol, exchange)` - Trade data from cache via WebSocket
- `get_trade_status(trade_key)` - Trade processing status via WebSocket
- `stream_trade_updates(exchange)` - Real-time trade stream

### **OHLCVCache Operations (READ-ONLY)** - OHLCV Handler
- `get_latest_ohlcv_bars(symbol, timeframe)` - Cached OHLCV data via WebSocket
- `stream_ohlcv(symbol, timeframe)` - Real-time OHLCV updates

### **ProcessCache Operations (READ-ONLY)** - Process Handler
- `get_system_health()` - System health status via WebSocket
- `get_active_processes()` - Active process data via WebSocket
- `stream_process_health()` - Real-time system monitoring

## 🧪 Testing Strategy

### **Test Categories**
```bash
# Unit tests - Individual components
tests/test_websocket_server.py
tests/test_websocket_client.py
tests/test_cache_handlers.py

# Integration tests - End-to-end workflows
tests/integration/test_websocket_workflows.py
tests/integration/test_cache_integration.py

# Performance tests - WebSocket performance testing
tests/performance/test_websocket_performance.py
```

### **Required Test Coverage**
- **WebSocket Operations**: Connection management, message handling, real-time streaming
- **Cache Integration**: All fullon_cache operations via WebSocket, connection handling
- **Message Validation**: WebSocket message format validation, parameter validation
- **Integration**: Complete WebSocket cache workflows, multi-cache operations
- **Performance**: WebSocket response times, large dataset streaming, concurrent connections
- **Async Iterators**: Verify all streaming operations use async iterators (NO CALLBACKS!)

## 🚀 Quick Start Commands

```bash
# Initial setup
make setup      # Install dependencies, setup pre-commit

# Development
make dev        # Start development server
make test       # Run test suite
make check      # Full quality check

# Testing & Quality  
./run_test.py   # Comprehensive test runner (REQUIRED before commits)
make format     # Format code with Black + Ruff
make lint       # Check code quality

# WebSocket API Testing
python examples/basic_usage.py           # Basic WebSocket demo
python examples/example_tick_cache.py    # Ticker WebSocket example
python examples/run_all.py              # All WebSocket examples
```

## 📖 Key References

- **fullon_cache Methods**: See `docs/FULLON_CACHE_METHOD_REFERENCE.md` for all available cache operations
- **fullon_orm Methods**: See `docs/FULLON_ORM_LLM_METHOD_REFERENCE.md` for repository patterns
- **fullon_cache Quick Start**: See `docs/FULLON_CACHE_LLM_QUICKSTART.md` for integration patterns
- **fullon_orm Integration**: See `docs/FULLON_ORM_LLM_README.md` for model-based API usage
- **Examples**: Working code in `examples/` directory
- **Tests**: Pattern examples in `tests/conftest.py`

### **🚨 Critical Integration Points**
- **Model Usage**: Always use `fullon_orm.models` (Symbol, Tick, Trade, etc.) with cache operations
- **Async Context Managers**: Required for all cache operations (`async with Cache() as cache:`)
- **Method Signatures**: TickCache.get_ticker(symbol: Symbol, exchange: str), not (exchange, symbol)
- **Queue Operations**: Use `get_queue_length()` not `get_queue_size()`
- **Bot Blocking**: Use `is_blocked()` which returns bot_id or None, not boolean

## ⚠️ Critical Rules

1. **LRRS Compliance**: Never violate Little, Responsible, Reusable, Separate
2. **TDD Only**: Tests first, implementation second, `./run_test.py` must pass
3. **WebSocket First**: Real-time cache operations via WebSocket transport
4. **Read-Only**: No write/update/insert operations in scope
5. **Async Iterators**: Streaming data with NO CALLBACKS pattern
6. **Context Managers**: Clean resource management with `async with` patterns

## 🔄 Cache-Specific Best Practices

### **1. Always Use WebSocket Context Managers**
```python
# Correct - WebSocket context manager:
async with fullon_cache_api() as handler:
    ticker = await handler.get_ticker("binance", "BTC/USDT")
    
    # Real-time streaming with async iterators
    async for update in handler.stream_tickers("binance", ["BTC/USDT"]):
        print(f"Live: {update['price']}")

# Wrong:
handler = fullon_cache_api()
data = await handler.get_ticker("binance", "BTC/USDT")  # No connection management
```

### **2. Handle WebSocket Cache Misses Gracefully**
```python
# Provide meaningful WebSocket responses for cache misses:
async def handle_ticker_request(websocket, message):
    params = message.get('params', {})
    exchange = params.get('exchange')
    symbol = params.get('symbol')
    
    async with fullon_cache_api() as handler:
        ticker = await handler.get_ticker(exchange, symbol)
        
        if not ticker:
            # Send WebSocket error response
            error_response = {
                "request_id": message.get('request_id'),
                "success": False,
                "error_code": "CACHE_MISS",
                "error": f"Ticker {symbol} not found in {exchange} cache"
            }
            await websocket.send(json.dumps(error_response))
            return
        
        # Send successful response
        success_response = {
            "request_id": message.get('request_id'),
            "success": True,
            "result": ticker
        }
        await websocket.send(json.dumps(success_response))
```

### **3. WebSocket Connection Health Monitoring**
```python
# Include WebSocket health check operations:
async def handle_ping_request(websocket, message):
    try:
        async with fullon_cache_api() as handler:
            # Test underlying cache connection
            health_status = await handler.ping()
        
        response = {
            "request_id": message.get('request_id'),
            "success": True,
            "result": {
                "status": "healthy", 
                "websocket": "connected",
                "cache": "available",
                "timestamp": time.time()
            }
        }
        await websocket.send(json.dumps(response))
    except Exception as e:
        error_response = {
            "request_id": message.get('request_id'),
            "success": False,
            "error_code": "HEALTH_CHECK_FAILED",
            "error": "Cache unavailable"
        }
        await websocket.send(json.dumps(error_response))
```

### **4. WebSocket Performance Monitoring**
```python
# Log WebSocket cache performance:
import time

async def handle_ticker_request_with_metrics(websocket, message):
    start_time = time.time()
    params = message.get('params', {})
    exchange = params.get('exchange')
    symbol = params.get('symbol')
    
    try:
        async with fullon_cache_api() as handler:
            result = await handler.get_ticker(exchange, symbol)
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info("WebSocket cache operation completed",
                   operation="get_ticker",
                   exchange=exchange,
                   symbol=symbol,
                   duration_ms=duration_ms,
                   cache_hit=result is not None,
                   transport="websocket")
        
        # Send response with performance metrics
        response = {
            "request_id": message.get('request_id'),
            "success": True,
            "result": result,
            "metrics": {
                "duration_ms": duration_ms,
                "cache_hit": result is not None
            }
        }
        await websocket.send(json.dumps(response))
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("WebSocket cache operation failed",
                    operation="get_ticker",
                    exchange=exchange,
                    symbol=symbol,
                    duration_ms=duration_ms,
                    error=str(e))
        raise
```

## 📊 Fullon Log Integration Best Practices

### **1. Component-Specific Logger Setup**
```python
from fullon_log import get_component_logger, configure_logger

class FullonCacheGateway:
    def __init__(self):
        self.logger = get_component_logger("fullon.api.cache.gateway")
        
        # Optional: Component-specific file logging
        configure_logger(
            file_path="/var/log/fullon/cache_api.log",
            console=True,
            level="INFO"
        )
        
        self.logger.info("Cache gateway initialized", component="gateway")
```

### **2. Router-Level Logging Patterns**
```python
# In each router file (tickers.py, orders.py, etc.)
from fullon_log import get_component_logger

# Router-specific logger
logger = get_component_logger("fullon.api.cache.tickers")

@router.get("/{exchange}/{symbol}")
async def get_ticker(exchange: str, symbol: str):
    logger.info("Ticker request started", exchange=exchange, symbol=symbol)
    
    try:
        # Cache operation with timing using fullon_orm models
        from fullon_orm.models import Symbol
        
        start_time = time.time()
        symbol_obj = Symbol(symbol=symbol, cat_ex_id=1, base=symbol.split("/")[0], quote=symbol.split("/")[1])
        
        async with TickCache() as cache:
            ticker = await cache.get_ticker(symbol_obj, exchange)
        
        duration_ms = (time.time() - start_time) * 1000
        
        if ticker:
            logger.info("Ticker retrieved successfully", 
                       exchange=exchange, 
                       symbol=symbol,
                       latency_ms=duration_ms,
                       cache_hit=True)
        else:
            logger.warning("Ticker not found in cache", 
                          exchange=exchange, 
                          symbol=symbol,
                          latency_ms=duration_ms,
                          cache_hit=False)
            
        return ticker
        
    except Exception as e:
        logger.error("Ticker retrieval failed", 
                    exchange=exchange, 
                    symbol=symbol,
                    error=str(e),
                    error_type=type(e).__name__)
        raise
```

### **3. Environment-Based Logging Configuration**
```python
# Example configurations for different environments

# Development (.env.development)
LOG_LEVEL=DEBUG
LOG_FORMAT=development
LOG_COLORS=true
LOG_CONSOLE=true
LOG_FILE_PATH=/tmp/fullon/cache_api_dev.log

# Production (.env.production)  
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_COLORS=false
LOG_CONSOLE=false
LOG_FILE_PATH=/var/log/fullon/cache_api.log
LOG_ROTATION=100 MB
LOG_RETENTION=30 days

# Trading-specific (.env.trading)
LOG_LEVEL=INFO
LOG_FORMAT=trading
LOG_COLORS=true
LOG_CONSOLE=true
LOG_FILE_PATH=/var/log/fullon/trading_cache.log
```

### **4. Performance and Metrics Logging**
```python
from fullon_log import get_component_logger
import time
from contextlib import asynccontextmanager

logger = get_component_logger("fullon.api.cache.metrics")

@asynccontextmanager
async def log_cache_operation(operation: str, **context):
    """Context manager for consistent cache operation logging."""
    start_time = time.time()
    logger.info(f"Cache {operation} started", operation=operation, **context)
    
    try:
        yield
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Cache {operation} completed", 
                   operation=operation, 
                   latency_ms=duration_ms,
                   status="success",
                   **context)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Cache {operation} failed", 
                    operation=operation,
                    error=str(e),
                    error_type=type(e).__name__,
                    latency_ms=duration_ms,
                    status="error",
                    **context)
        raise

# Usage:
async def get_ticker(exchange: str, symbol: str):
    from fullon_orm.models import Symbol
    
    async with log_cache_operation("get_ticker", exchange=exchange, symbol=symbol):
        symbol_obj = Symbol(symbol=symbol, cat_ex_id=1, base=symbol.split("/")[0], quote=symbol.split("/")[1])
        async with TickCache() as cache:
            return await cache.get_ticker(symbol_obj, exchange)
```

### **5. Health Check and Monitoring Integration**
```python
from fullon_log import get_component_logger

logger = get_component_logger("fullon.api.cache.health")

@router.get("/health")
async def health_check():
    """Health check with comprehensive logging."""
    health_status = {"status": "healthy", "services": {}}
    
    # Redis health check
    try:
        async with TickCache() as cache:
            await cache.test()
        health_status["services"]["redis"] = "healthy"
        logger.info("Health check passed", service="redis", status="healthy")
    except Exception as e:
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "unhealthy"
        logger.error("Health check failed", service="redis", status="unhealthy", error=str(e))
    
    # Log overall health status
    logger.info("Health check completed", 
               overall_status=health_status["status"],
               services_count=len(health_status["services"]))
    
    return health_status
```

---

**Remember**: This is a WebSocket-based library that provides real-time cache operations with async iterator patterns. Design every decision with WebSocket transport, real-time streaming, and clean resource management in mind! NO CALLBACKS - use async iterators for all streaming operations! 🚀