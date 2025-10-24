"""Pytest configuration and fixtures for fullon_cache_api tests.

Provides per-worker Redis database isolation for parallel testing.
"""

import asyncio
import os

import pytest


def get_worker_id(request):
    """Get the pytest-xdist worker ID, or 'master' if not using xdist."""
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


def get_redis_db_for_worker(worker_id: str) -> int:
    """Map worker ID to Redis database number (0-15).

    Args:
        worker_id: Worker ID from pytest-xdist (e.g., 'master', 'gw0', 'gw1', etc.)

    Returns:
        Redis database number between 0 and 15
    """
    if worker_id == "master":
        return 0

    # Extract worker number from 'gwN' format
    if worker_id.startswith("gw"):
        try:
            worker_num = int(worker_id[2:])
            # Map to databases 1-15 (0 is reserved for master/sequential runs)
            # Supports up to 15 parallel workers
            return (worker_num % 15) + 1
        except (ValueError, IndexError):
            return 0

    return 0


@pytest.fixture(scope="session")
def worker_id(request):
    """Provide worker ID for the current test worker."""
    return get_worker_id(request)


@pytest.fixture(scope="session")
def redis_db(worker_id):
    """Provide isolated Redis database number for this test worker.

    Each pytest-xdist worker gets its own Redis database (0-15).
    This prevents test interference when running in parallel.
    """
    db_num = get_redis_db_for_worker(worker_id)

    # Set environment variable for fullon_cache to use
    os.environ["REDIS_DB"] = str(db_num)

    return db_num


@pytest.fixture(autouse=True)
async def clean_redis(redis_db):
    """Clean Redis database before and after each test.

    This fixture runs automatically for every test, ensuring clean state.
    Uses the worker-specific Redis database from the redis_db fixture.
    """
    try:
        from fullon_cache import BaseCache  # type: ignore
    except ImportError:
        # If fullon_cache not available, skip cleanup
        yield
        return

    async def _flush():
        """Flush the worker-specific Redis database."""
        cache = BaseCache()
        try:
            async with cache._redis_context() as redis:
                await redis.flushdb()
        finally:
            await cache.close()

    # Clean before test
    try:
        await _flush()
    except Exception:
        pass

    # Run the test
    yield

    # Clean after test
    try:
        await _flush()
    except Exception:
        pass


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
