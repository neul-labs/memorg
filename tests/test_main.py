import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import tempfile
import os
from app.main import MemorgSystem
from app.models import Session, Conversation, Topic, Exchange, SearchScope
from app.storage.sqlite_storage import SQLiteStorageAdapter
from app.vector_store.usearch_vector_store import USearchVectorStore

class TestMemorgSystem:
    """Test the MemorgSystem implementation."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        
        # Also cleanup the index file
        index_path = db_path.replace('.db', '.usearch')
        if os.path.exists(index_path):
            os.unlink(index_path)
    
    @pytest.fixture
    def memorg_system(self, temp_db_path):
        """Create a MemorgSystem instance for testing."""
        storage = SQLiteStorageAdapter(db_path=temp_db_path)
        vector_store = USearchVectorStore(db_path=temp_db_path, vector_dim=1536)
        openai_client = AsyncMock()
        
        return MemorgSystem(
            storage=storage,
            vector_store=vector_store,
            openai_client=openai_client
        )
    
    def test_init(self, memorg_system):
        """Test initialization of MemorgSystem."""
        assert memorg_system.context_store is not None
        assert memorg_system.context_manager is not None
        assert memorg_system.retrieval_system is not None
        assert memorg_system.window_optimizer is not None
        assert memorg_system.openai_client is not None
    
    @pytest.mark.asyncio
    async def test_create_session(self, memorg_system):
        """Test creating a session."""
        session = await memorg_system.create_session("test-user", {"max_tokens": 4096})
        
        # Check the result
        assert isinstance(session, Session)
        assert session.user_id == "test-user"
        assert session.system_config == {"max_tokens": 4096}
        assert session.id is not None
    
    @pytest.mark.asyncio
    async def test_start_conversation(self, memorg_system):
        """Test starting a conversation."""
        # Create a session first
        session = await memorg_system.create_session("test-user", {"max_tokens": 4096})
        
        # Start a conversation
        conversation = await memorg_system.start_conversation(session.id)
        
        # Check the result
        assert isinstance(conversation, Conversation)
        assert conversation.id is not None
    
    @pytest.mark.asyncio
    async def test_add_exchange(self, memorg_system):
        """Test adding an exchange."""
        # Mock OpenAI embedding response
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock()]
        mock_embedding_response.data[0].embedding = [0.1] * 1536  # 1536-dimensional embedding
        memorg_system.openai_client.embeddings.create.return_value = mock_embedding_response
        
        # Create a session, conversation, and topic
        session = await memorg_system.create_session("test-user", {"max_tokens": 4096})
        conversation = await memorg_system.start_conversation(session.id)
        topic = await memorg_system.context_store.create_topic(conversation.id, "Test Topic")
        
        # Add an exchange
        exchange = await memorg_system.add_exchange(
            topic.id,
            "User message",
            "System response"
        )
        
        # Check the result
        assert isinstance(exchange, Exchange)
        assert exchange.id is not None
        assert exchange.user_message.raw_content == "User message"
        assert exchange.system_message.raw_content == "System response"
    
    @pytest.mark.asyncio
    async def test_search_context(self, memorg_system):
        """Test searching context."""
        # Mock OpenAI responses
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock()]
        mock_embedding_response.data[0].embedding = [0.1] * 1536  # 1536-dimensional embedding
        memorg_system.openai_client.embeddings.create.return_value = mock_embedding_response
        
        mock_entity_response = Mock()
        mock_entity_response.choices = [Mock()]
        mock_entity_response.choices[0].message.content = '[{"name": "test", "type": "PERSON"}]'
        memorg_system.openai_client.chat.completions.create.return_value = mock_entity_response
        
        # Create a session, conversation, topic, and exchange
        session = await memorg_system.create_session("test-user", {"max_tokens": 4096})
        conversation = await memorg_system.start_conversation(session.id)
        topic = await memorg_system.context_store.create_topic(conversation.id, "Test Topic")
        
        # Add an exchange
        exchange = await memorg_system.add_exchange(
            topic.id,
            "User message",
            "System response"
        )
        
        # Search context
        results = await memorg_system.search_context("test query", SearchScope.ALL, max_results=10)
        
        # Check the result
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_optimize_context(self, memorg_system):
        """Test optimizing context."""
        # Mock OpenAI responses
        mock_summarization_response = Mock()
        mock_summarization_response.choices = [Mock()]
        mock_summarization_response.choices[0].message.content = "Summarized content"
        memorg_system.openai_client.chat.completions.create.return_value = mock_summarization_response
        
        mock_optimization_response = Mock()
        mock_optimization_response.choices = [Mock()]
        mock_optimization_response.choices[0].message.content = "Optimized content"
        memorg_system.openai_client.chat.completions.create.return_value = mock_optimization_response
        
        # Optimize context
        entities = []  # Empty list for now
        result = await memorg_system.optimize_context(
            "Test content to optimize",
            entities,
            max_tokens=1000
        )
        
        # Check the result
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_get_memory_usage(self, memorg_system):
        """Test getting memory usage."""
        # Get memory usage
        usage = await memorg_system.get_memory_usage()
        
        # Check the result
        assert isinstance(usage, dict)
        assert "total_tokens" in usage
        assert "active_items" in usage
        assert "compressed_items" in usage
        assert "vector_count" in usage
        assert "index_size" in usage