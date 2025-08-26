import asyncio
from unittest.mock import patch

import pytest


class TestBaseCacheOperation:
    """Test suite for BaseCacheOperation abstract base class."""

    def test_base_cache_operation_is_abstract(self):
        """Test that BaseCacheOperation cannot be instantiated directly."""
        from fullon_cache_api import BaseCacheOperation

        with pytest.raises(TypeError):
            BaseCacheOperation()

    def test_concrete_implementation_works(self):
        """Test that concrete implementations work correctly."""
        from fullon_cache_api import BaseCacheOperation

        class ConcreteCacheOp(BaseCacheOperation):
            async def execute(self):
                return {"test": "data"}

        op = ConcreteCacheOp()
        assert hasattr(op, "logger")
        assert asyncio.iscoroutinefunction(op.execute)

        # Test logger exists and has component structure
        assert op.logger is not None

    @pytest.mark.asyncio
    async def test_concrete_implementation_execute(self):
        """Test that concrete implementation execute method works."""
        from fullon_cache_api import BaseCacheOperation

        class ConcreteCacheOp(BaseCacheOperation):
            async def execute(self):
                return {"status": "success", "data": "test_data"}

        op = ConcreteCacheOp()
        result = await op.execute()

        assert result == {"status": "success", "data": "test_data"}


class TestCacheHealthChecker:
    """Test suite for CacheHealthChecker utility class."""

    def test_health_checker_initialization(self):
        """Test health checker initializes correctly."""
        from fullon_cache_api import CacheHealthChecker

        checker = CacheHealthChecker()
        assert hasattr(checker, "logger")
        assert hasattr(checker, "check_cache_connectivity")

        # Test logger exists
        assert checker.logger is not None

    @pytest.mark.asyncio
    async def test_check_cache_connectivity_method_exists(self):
        """Test that check_cache_connectivity method exists and is async."""
        from fullon_cache_api import CacheHealthChecker

        checker = CacheHealthChecker()
        assert asyncio.iscoroutinefunction(checker.check_cache_connectivity)


class TestExceptions:
    """Test suite for custom exception classes."""

    def test_cache_not_found_error(self):
        """Test CacheNotFoundError exception."""
        from fullon_cache_api import CacheNotFoundError

        # Test default message
        error = CacheNotFoundError()
        assert error.status_code == 404
        assert "not found" in error.detail.lower()

        # Test custom message
        custom_error = CacheNotFoundError("Custom not found message")
        assert custom_error.status_code == 404
        assert custom_error.detail == "Custom not found message"

    def test_cache_service_unavailable_error(self):
        """Test CacheServiceUnavailableError exception."""
        from fullon_cache_api import CacheServiceUnavailableError

        # Test default message
        error = CacheServiceUnavailableError()
        assert error.status_code == 503
        assert "unavailable" in error.detail.lower()

        # Test custom message
        custom_error = CacheServiceUnavailableError("Redis is down")
        assert custom_error.status_code == 503
        assert custom_error.detail == "Redis is down"

    def test_cache_timeout_error(self):
        """Test CacheTimeoutError exception."""
        from fullon_cache_api import CacheTimeoutError

        # Test default message
        error = CacheTimeoutError()
        assert error.status_code == 408
        assert "timeout" in error.detail.lower()

        # Test custom message
        custom_error = CacheTimeoutError("Operation took too long")
        assert custom_error.status_code == 408
        assert custom_error.detail == "Operation took too long"

    def test_cache_api_exception_base_class(self):
        """Test CacheAPIException base class."""
        # Test that it's based on HTTPException
        from fastapi import HTTPException
        from fullon_cache_api import CacheAPIException

        assert issubclass(CacheAPIException, HTTPException)

        # Test instantiation
        error = CacheAPIException(status_code=500, detail="Test error")
        assert error.status_code == 500
        assert error.detail == "Test error"

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from CacheAPIException."""
        from fullon_cache_api import (
            CacheAPIException,
            CacheNotFoundError,
            CacheServiceUnavailableError,
            CacheTimeoutError,
        )

        assert issubclass(CacheNotFoundError, CacheAPIException)
        assert issubclass(CacheServiceUnavailableError, CacheAPIException)
        assert issubclass(CacheTimeoutError, CacheAPIException)


class TestTypes:
    """Test suite for type definitions."""

    def test_type_definitions_exist(self):
        """Test that all expected type definitions exist."""
        # Import typing utilities to verify types

        from fullon_cache_api import APIResponse, CacheData, CacheResult, HealthStatus

        # These should be type aliases, not actual classes
        assert CacheData is not None
        assert CacheResult is not None
        assert APIResponse is not None
        assert HealthStatus is not None

    def test_type_annotations_work(self):
        """Test that type annotations work with our custom types."""
        from fullon_cache_api import APIResponse, CacheData, CacheResult, HealthStatus

        # Test function annotations work
        def test_func(data: CacheData) -> CacheResult:
            return data

        def test_api_func(response: APIResponse) -> HealthStatus:
            return {"status": "healthy"}

        # Should not raise any errors
        assert callable(test_func)
        assert callable(test_api_func)


class TestImports:
    """Test suite for package imports and exports."""

    def test_version_import(self):
        """Test version is correctly imported."""
        from fullon_cache_api import __version__

        assert __version__ == "0.1.0"

    def test_all_expected_imports_available(self):
        """Test all expected infrastructure imports are available."""
        import fullon_cache_api

        # Check base classes
        assert hasattr(fullon_cache_api, "BaseCacheOperation")
        assert hasattr(fullon_cache_api, "CacheHealthChecker")

        # Check types
        assert hasattr(fullon_cache_api, "CacheData")
        assert hasattr(fullon_cache_api, "CacheResult")
        assert hasattr(fullon_cache_api, "APIResponse")
        assert hasattr(fullon_cache_api, "HealthStatus")

        # Check exceptions
        assert hasattr(fullon_cache_api, "CacheAPIException")
        assert hasattr(fullon_cache_api, "CacheNotFoundError")
        assert hasattr(fullon_cache_api, "CacheServiceUnavailableError")
        assert hasattr(fullon_cache_api, "CacheTimeoutError")

    def test_all_exports_in_all_list(self):
        """Test that __all__ list contains all expected exports."""
        import fullon_cache_api

        expected_exports = [
            "__version__",
            "BaseCacheOperation",
            "CacheHealthChecker",
            "CacheData",
            "CacheResult",
            "APIResponse",
            "HealthStatus",
            "CacheAPIException",
            "CacheNotFoundError",
            "CacheServiceUnavailableError",
            "CacheTimeoutError",
        ]

        for export in expected_exports:
            assert export in fullon_cache_api.__all__

    def test_module_imports_cleanly(self):
        """Test that the module can be imported without errors."""
        import fullon_cache_api

        assert fullon_cache_api.__name__ == "fullon_cache_api"

    def test_no_unexpected_imports(self):
        """Test that we don't have any unexpected imports in the public API."""
        import fullon_cache_api

        # Get all public attributes (not starting with _)
        public_attrs = [
            name for name in dir(fullon_cache_api) if not name.startswith("_")
        ]

        # They should all be in __all__
        for attr in public_attrs:
            if attr not in [
                "annotations",
                "base",
                "types",
                "exceptions",
            ]:  # Skip internal modules and special attributes
                assert attr in fullon_cache_api.__all__, f"'{attr}' not in __all__"


class TestLoggingIntegration:
    """Test suite for fullon_log integration."""

    @patch("fullon_cache_api.base.get_component_logger")
    def test_base_cache_operation_logging(self, mock_get_logger):
        """Test that BaseCacheOperation uses fullon_log correctly."""
        from fullon_cache_api import BaseCacheOperation

        class ConcreteCacheOp(BaseCacheOperation):
            async def execute(self):
                return {"test": "data"}

        ConcreteCacheOp()

        # Verify get_component_logger was called with correct component
        mock_get_logger.assert_called_with("fullon.api.cache")

    @patch("fullon_cache_api.base.get_component_logger")
    def test_cache_health_checker_logging(self, mock_get_logger):
        """Test that CacheHealthChecker uses fullon_log correctly."""
        from fullon_cache_api import CacheHealthChecker

        CacheHealthChecker()

        # Verify get_component_logger was called with correct component
        mock_get_logger.assert_called_with("fullon.api.cache.health")


class TestLRRSCompliance:
    """Test suite for LRRS (Little, Responsible, Reusable, Separate) compliance."""

    def test_little_principle(self):
        """Test that components follow the Little principle - single purpose."""
        from fullon_cache_api import BaseCacheOperation, CacheHealthChecker

        # BaseCacheOperation should only provide abstract cache operation base
        base_methods = [
            method for method in dir(BaseCacheOperation) if not method.startswith("_")
        ]
        assert "execute" in base_methods
        # logger is an instance attribute, not a class method
        # Should be minimal - just the essentials

        # CacheHealthChecker should only handle health checks
        health_methods = [
            method for method in dir(CacheHealthChecker) if not method.startswith("_")
        ]
        assert "check_cache_connectivity" in health_methods
        # logger is an instance attribute, not a class method

    def test_responsible_principle(self):
        """Test that each component has one clear responsibility."""
        from fullon_cache_api import (
            BaseCacheOperation,
            CacheHealthChecker,
            CacheNotFoundError,
            CacheServiceUnavailableError,
            CacheTimeoutError,
        )

        # Each class should have a clear single responsibility
        assert BaseCacheOperation.__doc__ and "Base class" in BaseCacheOperation.__doc__
        assert CacheHealthChecker.__doc__ and "Health" in CacheHealthChecker.__doc__
        assert CacheNotFoundError.__doc__ and "not found" in CacheNotFoundError.__doc__
        assert (
            CacheServiceUnavailableError.__doc__
            and "unavailable" in CacheServiceUnavailableError.__doc__
        )
        assert CacheTimeoutError.__doc__ and (
            "timeout" in CacheTimeoutError.__doc__
            or "times out" in CacheTimeoutError.__doc__
        )

    def test_reusable_principle(self):
        """Test that components are designed for reuse."""
        from fullon_cache_api import BaseCacheOperation

        # Should be able to create multiple concrete implementations
        class CacheOp1(BaseCacheOperation):
            async def execute(self):
                return {"op": "1"}

        class CacheOp2(BaseCacheOperation):
            async def execute(self):
                return {"op": "2"}

        op1 = CacheOp1()
        op2 = CacheOp2()

        # Both should work independently
        assert hasattr(op1, "logger")
        assert hasattr(op2, "logger")
        assert op1 is not op2

    def test_separate_principle(self):
        """Test that components are properly separated and loosely coupled."""
        # Test that we can import components independently
        from fullon_cache_api.base import BaseCacheOperation
        from fullon_cache_api.exceptions import CacheNotFoundError
        from fullon_cache_api.types import CacheData

        # They should work without depending on each other
        assert BaseCacheOperation is not None
        assert CacheNotFoundError is not None
        assert CacheData is not None
