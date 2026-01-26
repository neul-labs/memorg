import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    client = AsyncMock()
    client.embeddings = AsyncMock()
    client.embeddings.create = AsyncMock()
    client.chat = Mock()
    client.chat.completions = AsyncMock()
    client.chat.completions.create = AsyncMock()
    return client