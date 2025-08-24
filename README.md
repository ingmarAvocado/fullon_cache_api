# 🚀 fullon_cache_api

[![Tests](https://github.com/ingmarAvocado/fullon_cache_api/workflows/Tests/badge.svg)](https://github.com/ingmarAvocado/fullon_cache_api/actions)
[![Coverage](https://codecov.io/gh/ingmarAvocado/fullon_cache_api/branch/main/graph/badge.svg)](https://codecov.io/gh/ingmarAvocado/fullon_cache_api)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

**FastAPI Gateway for fullon_cache with LRRS-compliant architecture for read-only cache operations**

A focused, LRRS-compliant (Little, Responsible, Reusable, Separate) library that provides a complete **read-only** REST API gateway for Redis cache operations. Every fullon_cache **read operation** is exposed via secure, high-performance HTTP endpoints.

**🔍 READ-ONLY API**: This library **only** exposes data retrieval operations from Redis cache. No updates, inserts, or write operations are in scope.

## ✨ Features

- **📊 Complete Cache Read Coverage** - Every fullon_cache read operation exposed via REST API
- **⚡ Real-Time Optimized** - Built for efficient cache data retrieval and monitoring
- **🔄 High Performance** - uvloop optimization, async throughout, Redis connection pooling
- **🧪 100% Test Coverage** - TDD-driven development with comprehensive tests
- **📚 Auto-Generated Docs** - Interactive OpenAPI/Swagger documentation
- **🐳 Docker Ready** - Production-ready containerization
- **🔄 CI/CD Pipeline** - Automated testing, linting, and deployment

## 🏗️ Architecture

### LRRS Compliance

Following LRRS principles for maximum ecosystem integration:

- **Little**: Single purpose - READ-ONLY Redis cache data API gateway
- **Responsible**: Clear separation between routing, validation, and read-only cache operations  
- **Reusable**: Works with any fullon_cache deployment, composable into master_api
- **Separate**: Zero coupling to other systems beyond fullon_cache + fullon_log

### Fullon Ecosystem Integration

This library is designed to integrate seamlessly with the broader fullon trading ecosystem:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fullon Master Trading API                   │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  📊 Market Data │  🗄️ Database    │  ⚡ Cache & Real-time       │
│                 │                 │                             │
│ fullon_ohlcv_api│ fullon_orm_api  │ fullon_cache_api            │
│                 │                 │                             │
│ Historical data │ Persistent      │ Live feeds &                │
│ Time-series     │ Trade records   │ Real-time queues            │
│ OHLCV analysis  │ Positions       │ Price alerts                │
│                 │ Portfolio data  │ Event streaming             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### API Structure Benefits

**🎯 Clear Separation of Concerns**
- `/api/v1/market/` - Historical & analytical data (READ-ONLY)
- `/api/v1/db/` - Persistent application data (CRUD operations)  
- `/api/v1/cache/` - Real-time & temporary data (READ-ONLY)

**📚 Documentation Benefits**
- Combined Swagger/OpenAPI docs with organized tags
- Clear endpoint categorization
- Consistent versioning across all modules

```
fullon_cache_api/
├── src/fullon_cache_api/
│   ├── dependencies/         # Read-only cache session management
│   ├── routers/             # Read-only cache endpoints (tickers, orders, bots)
│   ├── models/              # Pydantic request/response models
│   └── gateway.py           # Main FastAPI application
├── examples/                # Working code examples
├── tests/                   # Comprehensive test suite
└── docs/                    # Additional documentation
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
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Run the API

```bash
# Development server
make dev

# Production server  
make prod

# View API documentation
# Open http://localhost:8000/docs
```

## 📖 Usage Examples

### Ticker Cache Operations

```python
import httpx
from datetime import datetime, timezone, timedelta

# Get ticker data from cache
response = httpx.get("http://localhost:8000/api/tickers/binance/BTC-USDT")
ticker = response.json()

# Get all tickers for exchange
response = httpx.get("http://localhost:8000/api/tickers/binance")
all_tickers = response.json()

# Check ticker cache status
response = httpx.get("http://localhost:8000/api/tickers/health")
health_status = response.json()
```

### Account Cache Operations

```python
# Get user positions from cache
response = httpx.get("http://localhost:8000/api/accounts/user123/positions")
positions = response.json()

# Get account balances
response = httpx.get("http://localhost:8000/api/accounts/user123/balances")
balances = response.json()

# Get account cache summary
response = httpx.get("http://localhost:8000/api/accounts/summary")
summary = response.json()
```

### Order Cache Operations

```python
# Get order status from cache
response = httpx.get("http://localhost:8000/api/orders/order123/status")
order_status = response.json()

# Get order queue metrics
response = httpx.get("http://localhost:8000/api/orders/queue/size")
queue_metrics = response.json()

# Get user orders from cache
response = httpx.get("http://localhost:8000/api/orders/user123/orders")
user_orders = response.json()
```

### Bot Cache Operations

```python
# Get bot coordination status
response = httpx.get("http://localhost:8000/api/bots/bot123/status")
bot_status = response.json()

# Check exchange blocking status
response = httpx.get("http://localhost:8000/api/bots/binance/BTC-USDT/blocked")
blocking_status = response.json()

# Get coordination info
response = httpx.get("http://localhost:8000/api/bots/coordination/status")
coordination = response.json()
```

### Trade Cache Operations

```python
# Get trade queue status
response = httpx.get("http://localhost:8000/api/trades/queue/status")
queue_status = response.json()

# Get trade processing metrics
response = httpx.get("http://localhost:8000/api/trades/performance/metrics")
metrics = response.json()
```

## 🔌 Library Usage (Master API Integration)

### Direct Gateway Usage

```python
from fullon_cache_api import FullonCacheGateway

# Create gateway instance
gateway = FullonCacheGateway(
    title="Master API - Cache Module",
    prefix="/cache"  # All routes prefixed with /cache
)

# Get the FastAPI app
app = gateway.get_app()
```

### Router Composition for Master API

```python
from fastapi import FastAPI
from fullon_cache_api import get_all_routers

# Create main FastAPI app
app = FastAPI(title="Fullon Master API", version="1.0.0")

# Mount Cache routers
for router in get_all_routers():
    app.include_router(router, prefix="/cache", tags=["Cache"])
    
# Routes available under /cache/ prefix
# /cache/tickers/{exchange}/{symbol}
# /cache/orders/{order_id}/status
# /cache/bots/{bot_id}/status
# etc.
```

### Multiple Library Composition

```python
from fastapi import FastAPI

# Fullon Master Trading API with complete ecosystem
app = FastAPI(title="Fullon Master Trading API", version="1.0.0")

# Database operations
from fullon_orm_api import get_all_routers as get_orm_routers
for router in get_orm_routers():
    app.include_router(router, prefix="/api/v1/db", tags=["Database"])

# Cache operations  
from fullon_cache_api import get_all_routers as get_cache_routers
for router in get_cache_routers():
    app.include_router(router, prefix="/api/v1/cache", tags=["Cache"])

# Market data operations
from fullon_ohlcv_api import get_all_routers as get_ohlcv_routers
for router in get_ohlcv_routers():
    app.include_router(router, prefix="/api/v1/market", tags=["Market Data"])

# Results in clean API separation:
# /api/v1/db/trades/              - Persistent trade records
# /api/v1/cache/trades/queue      - Real-time trade queue
# /api/v1/market/trades/          - Historical market data
# /docs                           - Combined documentation
```

## 📊 API Endpoints (READ-ONLY)

### Cache Data Endpoints (Standalone)

When used standalone, endpoints are accessible directly:
- **GET** `/api/tickers/{exchange}/{symbol}` - Get ticker from cache
- **GET** `/api/tickers/{exchange}` - Get all tickers for exchange  
- **GET** `/api/orders/{order_id}/status` - Get order status from cache
- **GET** `/api/bots/{bot_id}/status` - Get bot coordination status

### Master API Integration (Recommended)

When integrated into the master API, endpoints are prefixed with `/api/v1/cache`:

**⚡ Cache Operations** (`/api/v1/cache/`)
- **GET** `/api/v1/cache/tickers/{exchange}/{symbol}` - Ticker data from Redis
- **GET** `/api/v1/cache/tickers/{exchange}` - All tickers for exchange
- **GET** `/api/v1/cache/accounts/{user_id}/positions` - Account positions
- **GET** `/api/v1/cache/accounts/{user_id}/balances` - Account balances
- **GET** `/api/v1/cache/orders/{order_id}/status` - Order status from cache
- **GET** `/api/v1/cache/orders/queue/size` - Order queue metrics
- **GET** `/api/v1/cache/bots/{bot_id}/status` - Bot coordination status
- **GET** `/api/v1/cache/bots/{exchange}/{symbol}/blocked` - Exchange blocking
- **GET** `/api/v1/cache/trades/queue/status` - Trade processing queue
- **GET** `/api/v1/cache/ohlcv/{symbol}/{timeframe}` - Cached OHLCV data
- **GET** `/api/v1/cache/processes/status` - Process monitoring

**🗄️ Database Operations** (`/api/v1/db/`) - *via fullon_orm_api*
- **GET** `/api/v1/db/trades/` - Persistent trade records  
- **POST** `/api/v1/db/trades/` - Store trade records
- **GET** `/api/v1/db/positions/` - Trading positions

**📊 Market Data Operations** (`/api/v1/market/`) - *via fullon_ohlcv_api*
- **GET** `/api/v1/market/trades/{exchange}/{symbol}` - Historical trade data
- **GET** `/api/v1/market/candles/{exchange}/{symbol}/{timeframe}` - OHLCV candles
- **GET** `/api/v1/market/exchanges` - Available exchanges

### System Endpoints

- **GET** `/health` - Health check endpoint
- **GET** `/` - API information and links  
- **GET** `/docs` - Interactive Swagger documentation (combined when using master API)
- **GET** `/redoc` - ReDoc documentation

## 🧪 Testing

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run comprehensive test suite (required before PR)
./run_test.py

# Run specific test category
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v
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

# Start development server with auto-reload
make dev
```

## 📈 Performance Features

### Redis Cache Optimizations (READ-ONLY)
- **Connection Pooling**: Optimized Redis connections for read operations
- **Data Serialization**: Efficient JSON serialization for cached data
- **Query Optimization**: Fast Redis key-value lookups
- **Memory Management**: Efficient handling of large cached datasets

### Async Architecture (READ-ONLY)
- **Async Throughout**: All read operations are non-blocking
- **Connection Pooling**: Optimized Redis connections for reads
- **Concurrent Processing**: Multiple read requests handled simultaneously
- **Memory Efficient**: Streaming for large cache datasets retrieval

## 📊 Data Models

### Ticker Cache Model
```python
{
    "exchange": "binance",
    "symbol": "BTC-USDT",
    "ticker": {
        "bid": 45000.0,
        "ask": 45050.0,
        "last": 45025.0,
        "volume": 1234.5
    },
    "cached_at": "2024-01-01T12:00:00Z",
    "cache_hit": true
}
```

### Order Queue Model
```python
{
    "queue_name": "binance_orders",
    "size": 150,
    "processing_rate": 25.5,
    "health_status": "healthy",
    "last_processed": "2024-01-01T12:00:00Z"
}
```

## 🐳 Deployment

### Docker

```bash
# Build image
make docker-build

# Run container
make docker-run
```

### Production Deployment

```bash
# Install production dependencies only
poetry install --no-dev

# Run with production ASGI server
poetry run uvicorn src.fullon_cache_api.main:app --host 0.0.0.0 --port 8000 --workers 4
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

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the excellent [fullon_cache](https://github.com/ingmarAvocado/fullon_cache) Redis cache library
- Uses [FastAPI](https://fastapi.tiangolo.com/) for high-performance async API
- Follows LRRS architectural principles for maximum reusability
- Optimized for [Redis](https://redis.io/) cache performance

## 📞 Support

- 📚 Check the [CLAUDE.md](CLAUDE.md) for development assistance  
- 📋 See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for architecture details
- 🐛 Report issues on [GitHub Issues](https://github.com/ingmarAvocado/fullon_cache_api/issues)
- 💬 Discussion on [GitHub Discussions](https://github.com/ingmarAvocado/fullon_cache_api/discussions)

---

**Built with ❤️ using LRRS principles for maximum reusability and cache performance** ⚡🚀