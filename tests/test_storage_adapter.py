import pytest
from unittest.mock import Mock, AsyncMock
import asyncio
from memorg.storage.storage_adapter import StorageAdapter

class TestStorageAdapter:
    """Test the StorageAdapter protocol."""
    
    def test_storage_adapter_protocol(self):
        """Test that StorageAdapter defines the correct interface."""
        # This is more of a compile-time check since StorageAdapter is a Protocol
        # We're just ensuring the methods exist
        assert hasattr(StorageAdapter, 'write')
        assert hasattr(StorageAdapter, 'read')
        assert hasattr(StorageAdapter, 'query')
        assert hasattr(StorageAdapter, 'delete')
        
        # Check that methods are coroutines (async)
        import inspect
        assert inspect.iscoroutinefunction(StorageAdapter.write)
        assert inspect.iscoroutinefunction(StorageAdapter.read)
        assert inspect.iscoroutinefunction(StorageAdapter.query)
        assert inspect.iscoroutinefunction(StorageAdapter.delete)