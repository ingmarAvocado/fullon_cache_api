from typing import Any

from fastapi import HTTPException
from fullon_log import get_component_logger

from .cache import (
    get_account_cache,
    get_bot_cache,
    get_ohlcv_cache,
    get_orders_cache,
    get_process_cache,
    get_tick_cache,
    get_trades_cache,
)

logger = get_component_logger("fullon.api.cache.health")


async def check_all_cache_services() -> dict[str, Any]:
    """Check health of all cache services."""
    logger.debug("Starting comprehensive cache health check")

    health_results = {"overall_status": "healthy", "services": {}, "timestamp": None}

    # Test each cache service
    cache_tests = [
        ("ticker_cache", get_tick_cache),
        ("orders_cache", get_orders_cache),
        ("bot_cache", get_bot_cache),
        ("account_cache", get_account_cache),
        ("trades_cache", get_trades_cache),
        ("ohlcv_cache", get_ohlcv_cache),
        ("process_cache", get_process_cache),
    ]

    unhealthy_count = 0

    for service_name, cache_getter in cache_tests:
        try:
            async with cache_getter() as cache:
                # Test basic connectivity
                await cache.test() if hasattr(cache, "test") else True

            health_results["services"][service_name] = {
                "status": "healthy",
                "error": None,
            }
            logger.debug("Cache service healthy", service=service_name)

        except Exception as e:
            health_results["services"][service_name] = {
                "status": "unhealthy",
                "error": str(e),
            }
            unhealthy_count += 1
            logger.error("Cache service unhealthy", service=service_name, error=str(e))

    # Set overall status
    if unhealthy_count > 0:
        health_results["overall_status"] = (
            "degraded" if unhealthy_count < len(cache_tests) else "unhealthy"
        )

    from datetime import datetime

    health_results["timestamp"] = datetime.utcnow().isoformat()

    logger.info(
        "Cache health check completed",
        overall_status=health_results["overall_status"],
        healthy_services=len(cache_tests) - unhealthy_count,
        total_services=len(cache_tests),
    )

    return health_results


async def require_healthy_cache() -> None:
    """Dependency that requires cache services to be healthy."""
    health = await check_all_cache_services()

    if health["overall_status"] == "unhealthy":
        logger.error("Cache services are unhealthy", health_status=health)
        raise HTTPException(
            status_code=503, detail="Cache services are currently unavailable"
        )
