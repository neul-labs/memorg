import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta, timezone
from memorg.context_manager import (
    CompressedEntity, AllocationResult, MemoryUsage,
    RecencyWeightedStrategy, TopicCoherenceStrategy,
    ExtractiveSummarization, WorkingMemory,
    ContextManager
)
from memorg.models import Exchange, Message, ParsedContent, Entity, EntityType, Topic

class TestRecencyWeightedStrategy:
    """Test the RecencyWeightedStrategy implementation."""
    
    def test_init(self):
        """Test initialization of RecencyWeightedStrategy."""
        strategy = RecencyWeightedStrategy(decay_factor=0.5)
        assert strategy.decay_factor == 0.5
    
    def test_calculate_importance(self):
        """Test calculating importance score with time decay."""
        strategy = RecencyWeightedStrategy(decay_factor=0.1)
        
        # Create a mock exchange with base importance score
        exchange = Mock()
        exchange.importance_score = 1.0
        exchange.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Calculate importance
        importance = strategy.calculate_importance(exchange, {})
        
        # The importance should be less than the base score due to time decay
        assert importance <= exchange.importance_score
        assert importance >= 0
    
    def test_rank_context_items(self):
        """Test ranking context items by importance."""
        strategy = RecencyWeightedStrategy()
        
        # Create mock items with different importance scores
        item1 = Mock()
        item1.importance_score = 0.9
        item2 = Mock()
        item2.importance_score = 0.5
        item3 = Mock()
        item3.importance_score = 0.7
        
        items = [item1, item2, item3]
        
        # Rank items
        ranked_items = strategy.rank_context_items(items, max_items=2)
        
        # Should return top 2 items
        assert len(ranked_items) == 2
        # First item should have highest importance
        assert ranked_items[0].importance_score >= ranked_items[1].importance_score

class TestTopicCoherenceStrategy:
    """Test the TopicCoherenceStrategy implementation."""
    
    def test_calculate_importance_without_current_topic(self):
        """Test calculating importance when no current topic is provided."""
        strategy = TopicCoherenceStrategy()
        
        # Create a mock exchange
        exchange = Mock()
        exchange.importance_score = 0.8
        
        # Calculate importance without current topic
        importance = strategy.calculate_importance(exchange, {})
        
        # Should return base importance score
        assert importance == exchange.importance_score
    
    def test_rank_context_items(self):
        """Test ranking context items by importance."""
        strategy = TopicCoherenceStrategy()
        
        # Create mock items with different importance scores
        item1 = Mock()
        item1.importance_score = 0.9
        item2 = Mock()
        item2.importance_score = 0.5
        item3 = Mock()
        item3.importance_score = 0.7
        
        items = [item1, item2, item3]
        
        # Rank items
        ranked_items = strategy.rank_context_items(items, max_items=2)
        
        # Should return top 2 items
        assert len(ranked_items) == 2
        # First item should have highest importance
        assert ranked_items[0].importance_score >= ranked_items[1].importance_score

class TestExtractiveSummarization:
    """Test the ExtractiveSummarization implementation."""
    
    @pytest.mark.asyncio
    async def test_init(self, mock_openai_client):
        """Test initialization of ExtractiveSummarization."""
        strategy = ExtractiveSummarization(mock_openai_client)
        assert strategy.openai_client == mock_openai_client
    
    @pytest.mark.asyncio
    async def test_compress_with_openai_success(self, mock_openai_client):
        """Test compressing an entity with successful OpenAI response."""
        strategy = ExtractiveSummarization(mock_openai_client)
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"summary": "Test summary", "preserved_entities": ["entity1", "entity2"]}'
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Create a mock entity
        entity = Mock()
        entity.content = "Test content to summarize"
        entity.key_entities = []
        entity.id = "test-entity-1"
        
        # Compress the entity
        result = await strategy.compress(entity)
        
        # Check the result
        assert isinstance(result, CompressedEntity)
        assert result.original_id == "test-entity-1"
        assert result.compressed_content == "Test summary"
        assert result.compression_ratio > 0

class TestWorkingMemory:
    """Test the WorkingMemory implementation."""
    
    def test_init(self):
        """Test initialization of WorkingMemory."""
        memory = WorkingMemory(capacity=1000)
        assert memory.capacity == 1000
        assert memory.allocations == {}
        assert memory._next_allocation_id == 0
    
    def test_allocate_tokens_success(self):
        """Test successful token allocation."""
        memory = WorkingMemory(capacity=1000)
        
        # Allocate tokens
        result = memory.allocate_tokens("Test content", priority=0.5)
        
        # Check the result
        assert isinstance(result, AllocationResult)
        assert result.allocated == True
        assert result.token_count > 0
        assert result.allocation_id != ""
    
    def test_allocate_tokens_failure(self):
        """Test token allocation failure when capacity is exceeded."""
        # Create memory with very small capacity
        memory = WorkingMemory(capacity=1)
        
        # Try to allocate more tokens than capacity
        result = memory.allocate_tokens("This is a long content that should exceed capacity", priority=0.5)
        
        # Check the result
        assert isinstance(result, AllocationResult)
        assert result.allocated == False
    
    def test_release_tokens(self):
        """Test releasing tokens."""
        memory = WorkingMemory(capacity=1000)
        
        # Allocate tokens
        result = memory.allocate_tokens("Test content", priority=0.5)
        allocation_id = result.allocation_id
        
        # Release tokens
        memory.release_tokens(allocation_id)
        
        # Check that allocation is removed
        assert allocation_id not in memory.allocations
    
    def test_get_current_usage(self):
        """Test getting current memory usage."""
        memory = WorkingMemory(capacity=1000)
        
        # Get initial usage
        usage = memory.get_current_usage()
        
        # Check the result
        assert isinstance(usage, MemoryUsage)
        assert usage.used == 0
        assert usage.available == 1000
        assert usage.allocations == {}

class TestContextManager:
    """Test the ContextManager implementation."""
    
    @pytest.fixture
    def context_manager(self, mock_openai_client):
        """Create a ContextManager instance for testing."""
        prioritization_strategy = RecencyWeightedStrategy()
        compression_strategy = ExtractiveSummarization(mock_openai_client)
        working_memory = WorkingMemory(capacity=1000)
        
        return ContextManager(
            prioritization_strategy=prioritization_strategy,
            compression_strategy=compression_strategy,
            working_memory=working_memory
        )
    
    def test_init(self, context_manager):
        """Test initialization of ContextManager."""
        assert context_manager.prioritization_strategy is not None
        assert context_manager.compression_strategy is not None
        assert context_manager.working_memory is not None
    
    def test_update_importance(self, context_manager):
        """Test updating importance score."""
        # Create a mock exchange
        exchange = Mock()
        exchange.importance_score = 0.8
        exchange.created_at = datetime.now(timezone.utc)
        
        # Update importance
        importance = context_manager.update_importance(exchange, {})
        
        # Should return a float
        assert isinstance(importance, float)
        assert importance >= 0
    
    def test_rank_context(self, context_manager):
        """Test ranking context items."""
        # Create mock items with different importance scores
        item1 = Mock()
        item1.importance_score = 0.9
        item2 = Mock()
        item2.importance_score = 0.5
        item3 = Mock()
        item3.importance_score = 0.7
        
        items = [item1, item2, item3]
        
        # Rank items
        ranked_items = context_manager.rank_context(items, max_items=2)
        
        # Should return top 2 items
        assert len(ranked_items) == 2
    
    @pytest.mark.asyncio
    async def test_compress_entity(self, context_manager, mock_openai_client):
        """Test compressing an entity."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"summary": "Test summary", "preserved_entities": ["entity1", "entity2"]}'
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Create a mock entity
        entity = Mock()
        entity.content = "Test content to summarize"
        entity.key_entities = []
        entity.id = "test-entity-1"
        
        # Compress the entity
        result = await context_manager.compress_entity(entity)
        
        # Check the result
        assert isinstance(result, CompressedEntity)
    
    def test_allocate_memory(self, context_manager):
        """Test allocating memory."""
        # Allocate memory
        result = context_manager.allocate_memory("Test content", priority=0.5)
        
        # Check the result
        assert isinstance(result, AllocationResult)
        assert result.allocated == True
    
    def test_release_memory(self, context_manager):
        """Test releasing memory."""
        # Allocate memory first
        result = context_manager.allocate_memory("Test content", priority=0.5)
        allocation_id = result.allocation_id
        
        # Release memory
        context_manager.release_memory(allocation_id)
        # If no exception is raised, the test passes
    
    def test_get_memory_usage(self, context_manager):
        """Test getting memory usage."""
        # Get memory usage
        usage = context_manager.get_memory_usage()
        
        # Check the result
        assert isinstance(usage, MemoryUsage)
        assert usage.used >= 0