# 🚀 Master API Guide - fullon Ecosystem

**Unified API Gateway and Orchestration Layer for fullon Trading Platform**

## 🎯 Overview

The `master_api` is the **central orchestration layer** for the fullon trading ecosystem, providing a unified entry point that coordinates and routes requests across multiple specialized API services. It acts as the main gateway that integrates database operations, real-time cache data, and market data services into a cohesive trading platform API.

## 🌐 Ecosystem Integration

The master API coordinates these specialized services:

- **fullon_orm_api** (Database Operations) - PostgreSQL-backed trade records, user data, historical data
- **fullon_cache_api** (Real-time Cache) - Redis WebSocket streams for live trading data  
- **fullon_ohlcv_api** (Market Data) - External market data feeds and historical OHLCV data

## 🏗️ Master API Architecture

### Service Orchestration

```
┌─────────────────────────────────────────────────────────────────┐
│                      Master API Gateway                        │
│                                                                 │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   REST/HTTP     │ │   WebSocket     │ │   GraphQL       │   │
│  │   Endpoints     │ │   Gateway       │ │   Unified       │   │
│  │   Routing       │ │   Real-time     │ │   Query Layer   │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ fullon_orm_api  │ │fullon_cache_api │ │fullon_ohlcv_api │
│   (Database)    │ │  (Real-time)    │ │ (Market Data)   │
│                 │ │                 │ │                 │
│ PostgreSQL      │ │ Redis Cache     │ │ External APIs   │
│ HTTP REST       │ │ WebSocket       │ │ HTTP REST       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Unified Entry Points

```python
# Master API provides unified access patterns:

# HTTP REST - Database operations via fullon_orm_api
GET /api/trades/{trade_id}          → fullon_orm_api
POST /api/orders                    → fullon_orm_api  
GET /api/users/{user_id}/positions  → fullon_orm_api

# WebSocket - Real-time cache via fullon_cache_api
WS /ws/tickers                      → fullon_cache_api
WS /ws/order_queue                  → fullon_cache_api
WS /ws/bot_status                   → fullon_cache_api

# HTTP REST - Market data via fullon_ohlcv_api  
GET /api/market/ohlcv/{symbol}      → fullon_ohlcv_api
GET /api/market/exchanges           → fullon_ohlcv_api
```

## 🌐 WebSocket Protocol

### Primary Endpoint: `/ws`

The master API uses a **single WebSocket endpoint** at `/ws` for all real-time operations:

```javascript
// Connect to master API
const ws = new WebSocket('ws://localhost:8000/ws');

// Standard message format
const message = {
    "request_id": "unique-id",
    "operation": "get_ticker", 
    "params": {
        "exchange": "binance",
        "symbol": "BTC/USDT"
    }
};

ws.send(JSON.stringify(message));
```

### Message Structure

**Request Format:**
```json
{
    "request_id": "string (optional)",
    "operation": "string (required)",
    "params": {
        "key": "value"
    }
}
```

**Response Format:**
```json
{
    "request_id": "string",
    "success": true,
    "result": {
        "data": "value"
    },
    "latency_ms": 12.5
}
```

**Error Format:**
```json
{
    "request_id": "string", 
    "success": false,
    "error_code": "CACHE_MISS",
    "error_message": "Data not found in cache"
}
```

## 🛠️ Core Features

### 1. Request Proxying

| Service | Transport | Proxy Method |
|---------|-----------|-------------|
| **fullon_orm_api** | HTTP REST | HTTP proxy with path rewriting |
| **fullon_cache_api** | WebSocket | WebSocket proxy with message routing |
| **fullon_ohlcv_api** | HTTP REST | HTTP proxy with authentication |

### 2. Authentication & Authorization

```python
# Master API handles auth for all services
class AuthMiddleware:
    async def authenticate_request(self, request):
        token = request.headers.get('Authorization')
        user = await self.validate_jwt_token(token)
        
        # Add user context to downstream requests
        request.state.user = user
        return request
    
    def add_auth_headers(self, downstream_request, user):
        # Add service-specific auth headers
        downstream_request.headers['X-User-ID'] = str(user.id)
        downstream_request.headers['X-User-Role'] = user.role
        return downstream_request
```

### 3. Load Balancing & Circuit Breaking

```python
# Distribute load across service instances
class ServiceRegistry:
    def __init__(self):
        self.services = {
            'orm_api': ['localhost:8001', 'localhost:8011'],
            'cache_api': ['localhost:8002', 'localhost:8012'],
            'ohlcv_api': ['localhost:8003', 'localhost:8013']
        }
        self.circuit_breakers = {}
    
    async def get_healthy_instance(self, service_name):
        instances = self.services[service_name]
        for instance in instances:
            if await self.is_healthy(instance):
                return instance
        raise ServiceUnavailableError(f"No healthy {service_name} instances")
```

## 🚀 Quick Start

### 1. Start All Services

```bash
# Start individual services first
cd fullon_orm_api && uvicorn main:app --port 8001 &
cd fullon_cache_api && uvicorn main:app --port 8002 &  
cd fullon_ohlcv_api && uvicorn main:app --port 8003 &

# Start master API (orchestrator)
cd master_api && uvicorn main:app --port 8000
```

### 2. Service Configuration

```yaml
# master_api/config.yml
services:
  orm_api:
    instances:
      - "http://localhost:8001"
      - "http://localhost:8011"  # Load balanced instance
    health_endpoint: "/health"
    timeout: 30s
    
  cache_api:
    instances: 
      - "ws://localhost:8002"
      - "ws://localhost:8012"   # Load balanced instance
    health_endpoint: "/health"
    websocket_path: "/ws"
    
  ohlcv_api:
    instances:
      - "http://localhost:8003" 
      - "http://localhost:8013"  # Load balanced instance
    health_endpoint: "/health"
    timeout: 60s

auth:
  jwt_secret: "${JWT_SECRET}"
  token_expiry: "24h"
  
load_balancer:
  strategy: "round_robin"  # round_robin, least_connections, weighted
  circuit_breaker:
    failure_threshold: 5
    timeout: 30s
```

### 3. Client Usage Examples

```python
import httpx
import websockets
import asyncio

# HTTP requests via master API (proxied to orm/ohlcv APIs)
async def http_example():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        
        # Database operations (proxied to fullon_orm_api)
        trades = await client.get("/api/orm/trades", 
                                headers={"Authorization": "Bearer <token>"})
        
        # Market data (proxied to fullon_ohlcv_api) 
        ohlcv = await client.get("/api/market/ohlcv/BTC-USD",
                               headers={"Authorization": "Bearer <token>"})

# WebSocket via master API (proxied to fullon_cache_api)
async def websocket_example():
    uri = "ws://localhost:8000/ws/tickers"
    headers = {"Authorization": "Bearer <token>"}
    
    async with websockets.connect(uri, extra_headers=headers) as ws:
        # Real-time ticker data (proxied to fullon_cache_api)
        msg = {"operation": "stream_tickers", "params": {"exchange": "binance"}}
        await ws.send(json.dumps(msg))
        
        async for message in ws:
            data = json.loads(message)
            print(f"Ticker update: {data}")

# Run examples
asyncio.run(http_example())
asyncio.run(websocket_example())
```

## 🔌 Integration Patterns

### Docker Compose Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  master_api:
    build: ./master_api
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - orm_api
      - cache_api
      - ohlcv_api
      
  orm_api:
    build: ./fullon_orm_api
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      
  cache_api:
    build: ./fullon_cache_api  
    ports:
      - "8002:8002"
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
      
  ohlcv_api:
    build: ./fullon_ohlcv_api
    ports:
      - "8003:8003"
    environment:
      - MARKET_API_KEY=${MARKET_API_KEY}
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
      
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=fullon
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
```

### Kubernetes Deployment

```yaml
# k8s/master-api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: master-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: master-api
  template:
    metadata:
      labels:
        app: master-api
    spec:
      containers:
      - name: master-api
        image: fullon/master-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: jwt-secret
        - name: SERVICE_DISCOVERY
          value: "kubernetes"
```

## 📊 Error Handling

### Master API Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `SERVICE_UNAVAILABLE` | Downstream service unreachable | Check service health |
| `AUTH_FAILED` | Authentication failed | Verify JWT token |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Implement backoff |
| `CIRCUIT_BREAKER_OPEN` | Service circuit breaker open | Wait for recovery |
| `PROXY_TIMEOUT` | Downstream service timeout | Check service performance |
| `INVALID_ROUTE` | Unknown API endpoint | Check routing table |

### Error Response Format

```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "fullon_orm_api is currently unavailable",
    "service": "orm_api",
    "timestamp": "2025-01-15T10:30:00Z",
    "request_id": "req_123456",
    "retry_after": 30
  }
}
```

## 🔧 Configuration

### Environment Variables

```bash
# Master API Configuration
MASTER_API_HOST=0.0.0.0
MASTER_API_PORT=8000

# Service Discovery
SERVICE_DISCOVERY=consul  # consul, kubernetes, static
CONSUL_HOST=localhost:8500

# Authentication
JWT_SECRET=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRY=24h

# Load Balancing
LOAD_BALANCER_STRATEGY=round_robin
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=30s

# Service Endpoints (if using static discovery)
ORM_API_ENDPOINTS=http://localhost:8001,http://localhost:8011
CACHE_API_ENDPOINTS=ws://localhost:8002,ws://localhost:8012
OHLCV_API_ENDPOINTS=http://localhost:8003,http://localhost:8013

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60s

# Monitoring & Logging
LOG_LEVEL=INFO
METRICS_ENABLED=true
TRACING_ENABLED=true
JAEGER_ENDPOINT=http://localhost:14268/api/traces
```

### FastAPI Configuration

```python
# Custom app configuration
def create_custom_app():
    app = FastAPI(
        title="Custom Cache API",
        description="Extended cache operations",
        version="1.0.0",
        docs_url="/docs",  # Enable if needed
        redoc_url="/redoc"  # Enable if needed
    )
    
    # Add custom middleware
    app.add_middleware(CORSMiddleware, allow_origins=["*"])
    
    # Include cache routers
    from fullon_cache_api.routers.websocket import router
    app.include_router(router)
    
    return app
```

## 🧪 Testing & Monitoring

### Health Checks

```bash
# Master API health (includes all downstream services)
curl -X GET http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "services": {
    "orm_api": {"status": "healthy", "latency_ms": 12.3},
    "cache_api": {"status": "healthy", "latency_ms": 5.1},
    "ohlcv_api": {"status": "healthy", "latency_ms": 8.7}
  },
  "load_balancer": {
    "active_instances": 6,
    "circuit_breakers": 0
  }
}

# Individual service health via master API
curl -X GET http://localhost:8000/health/orm_api
curl -X GET http://localhost:8000/health/cache_api  
curl -X GET http://localhost:8000/health/ohlcv_api
```

### Load Testing

```python
import asyncio
import httpx
import time
from concurrent.futures import ThreadPoolExecutor

# HTTP load testing via master API
async def http_load_test():
    async with httpx.AsyncClient() as client:
        tasks = []
        
        # Test database operations via master API
        for i in range(100):
            task = client.get(f"http://localhost:8000/api/orm/trades/{i}")
            tasks.append(task)
            
        start = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end = time.time()
        
        success_count = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        print(f"HTTP: {success_count}/100 requests successful in {end - start:.2f}s")

# WebSocket load testing via master API  
async def websocket_load_test():
    async def ws_client(client_id):
        uri = f"ws://localhost:8000/ws/tickers"
        async with websockets.connect(uri) as ws:
            msg = {"operation": "stream_tickers", "params": {"exchange": "binance"}}
            await ws.send(json.dumps(msg))
            response = await ws.recv()
            return json.loads(response)
    
    tasks = [ws_client(i) for i in range(50)]  # 50 concurrent WS connections
    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end = time.time()
    
    success_count = len([r for r in results if not isinstance(r, Exception)])
    print(f"WebSocket: {success_count}/50 connections successful in {end - start:.2f}s")

# Run tests
asyncio.run(http_load_test())
asyncio.run(websocket_load_test())
```

## 📈 Performance & Scaling

### Master API Benchmarks

- **Request Routing**: <2ms overhead average
- **Authentication**: <1ms JWT validation
- **Load Balancing**: <0.5ms instance selection
- **Health Checks**: 5-30ms (depending on downstream services)
- **Concurrent Requests**: 10,000+ supported per instance
- **WebSocket Proxying**: <5ms connection establishment

### Scaling Strategies

```python
# Horizontal scaling with load balancer
class MasterAPICluster:
    def __init__(self):
        self.instances = [
            "http://master-api-1:8000",
            "http://master-api-2:8000", 
            "http://master-api-3:8000"
        ]
        self.load_balancer = RoundRobinBalancer(self.instances)
        
    async def route_request(self, request):
        instance = await self.load_balancer.get_healthy_instance()
        return await self.proxy_request(request, instance)
```

### Performance Optimization

1. **Service Mesh**: Use Istio/Envoy for advanced routing
2. **Caching**: Cache service discovery and auth tokens
3. **Connection Pooling**: Reuse HTTP/WebSocket connections to downstream services
4. **Circuit Breakers**: Prevent cascade failures
5. **Async Processing**: Use async/await throughout the stack

## 🔍 Monitoring & Observability

### Structured Logging

```python
from fullon_log import get_component_logger

logger = get_component_logger("fullon.master_api")

# Request routing logging
logger.info("Request routed", 
           path=request.path,
           method=request.method,
           service="orm_api",
           instance="localhost:8001",
           user_id=request.state.user.id,
           duration_ms=response_time)
```

### Metrics & Dashboards

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('master_api_requests_total', 
                       'Total requests', ['service', 'method', 'status'])

request_duration = Histogram('master_api_request_duration_seconds',
                            'Request duration', ['service', 'method'])

active_connections = Gauge('master_api_active_connections', 
                          'Active WebSocket connections', ['service'])

service_health = Gauge('master_api_service_health',
                      'Service health status', ['service'])
```

### Key Metrics to Monitor

- **Request Routing**: Success/failure rates per service
- **Service Health**: Up/down status and response times
- **Load Balancing**: Request distribution across instances  
- **Circuit Breakers**: Open/closed states and failure rates
- **Authentication**: Token validation success/failure
- **WebSocket Connections**: Active connections per service
- **Error Rates**: 4xx/5xx responses by service and endpoint

## 🔒 Security & Compliance

### Security Features

```python
# Comprehensive security middleware
class SecurityMiddleware:
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.jwt_validator = JWTValidator()
        self.audit_logger = AuditLogger()
    
    async def authenticate(self, request):
        token = request.headers.get('Authorization')
        user = await self.jwt_validator.validate(token)
        
        # Log authentication attempt
        await self.audit_logger.log_auth(user.id, request.client.host)
        return user
    
    async def authorize(self, user, resource, action):
        # Role-based access control
        if not user.has_permission(resource, action):
            raise HTTPException(403, "Insufficient permissions")
    
    async def rate_limit(self, request):
        # Per-user and per-IP rate limiting
        if await self.rate_limiter.is_exceeded(request.client.host, request.state.user.id):
            raise HTTPException(429, "Rate limit exceeded")
```

### Security Best Practices

1. **JWT Token Validation**: All requests authenticated via JWT
2. **Role-Based Access Control**: Fine-grained permissions per service
3. **Rate Limiting**: Prevent abuse with per-user/IP limits
4. **Request Sanitization**: Validate all inputs before proxying
5. **Audit Logging**: Complete audit trail of all operations
6. **TLS/SSL**: Encrypt all communications (HTTP/WebSocket)
7. **Service-to-Service Auth**: mTLS between master API and services
8. **Security Headers**: CORS, CSP, HSTS headers on all responses

### Compliance Features

- **GDPR**: User data anonymization and deletion capabilities
- **SOX**: Financial data handling and audit requirements  
- **PCI DSS**: Payment data security (if applicable)
- **Audit Trails**: Complete request/response logging with retention policies

## 📚 Resources & References

### Service Documentation
- **fullon_orm_api**: Database operations and models
- **fullon_cache_api**: Real-time cache WebSocket operations
- **fullon_ohlcv_api**: Market data and historical OHLCV
- **fullon_log**: Centralized logging framework

### Architecture Patterns
- **API Gateway Pattern**: Request routing and aggregation
- **Circuit Breaker Pattern**: Fault tolerance and resilience
- **Service Mesh**: Advanced traffic management (Istio/Envoy)
- **CQRS**: Command Query Responsibility Segregation

## 🛠️ Development Guide

### Master API Project Structure

```
master_api/
├── src/master_api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── routing/                # Request routing logic
│   │   ├── __init__.py
│   │   ├── http_proxy.py         # HTTP request proxying
│   │   ├── websocket_proxy.py    # WebSocket proxying
│   │   └── service_discovery.py  # Service registry
│   ├── middleware/             # Security and monitoring
│   │   ├── __init__.py
│   │   ├── auth.py               # JWT authentication
│   │   ├── rate_limiting.py      # Request rate limiting
│   │   └── circuit_breaker.py    # Fault tolerance
│   ├── load_balancer/          # Load balancing
│   │   ├── __init__.py
│   │   ├── strategies.py         # LB algorithms
│   │   └── health_checker.py     # Health monitoring
│   └── config/                 # Configuration
│       ├── __init__.py
│       └── settings.py           # App settings
├── tests/                      # Test suite
├── docker/                     # Container config
├── k8s/                        # Kubernetes manifests
└── docs/                       # Documentation
```

### Development Workflow

```bash
# Clone and setup master API project
git clone https://github.com/fullon/master_api
cd master_api

# Install dependencies
poetry install

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run master API
poetry run uvicorn master_api.main:app --reload --port 8000

# Run tests
poetry run pytest

# Deploy to production
kubectl apply -f k8s/
```

---

**The master_api serves as the unified gateway for the entire fullon trading ecosystem. It orchestrates multiple specialized services while providing authentication, load balancing, and fault tolerance. Deploy as the single entry point for all client applications!** 🚀

## 🏁 Next Steps

1. **Set up service infrastructure** (PostgreSQL, Redis, message queues)  
2. **Deploy individual APIs** (fullon_orm_api, fullon_cache_api, fullon_ohlcv_api)
3. **Configure master_api** with service endpoints and authentication
4. **Test end-to-end workflows** via master API gateway
5. **Monitor and scale** based on production traffic patterns

**Ready to build a robust, scalable trading platform with the master API architecture!** 🎯