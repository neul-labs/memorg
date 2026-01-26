import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from memorg.window_optimizer import (
    SummarizedContent, OptimizedContext,
    ProgressiveSummarization, TokenOptimizer,
    ContextWindowOptimizer
)
from memorg.models import Entity, EntityType

class TestProgressiveSummarization:
    """Test the ProgressiveSummarization implementation."""
    
    @pytest.fixture
    def summarization_strategy(self, mock_openai_client):
        """Create a ProgressiveSummarization instance for testing."""
        return ProgressiveSummarization(mock_openai_client)
    
    def test_init(self, summarization_strategy, mock_openai_client):
        """Test initialization of ProgressiveSummarization."""
        assert summarization_strategy.openai_client == mock_openai_client
    
    def test_chunk_content(self, summarization_strategy):
        """Test chunking content into smaller pieces."""
        # Create a long content string
        content = "This is a test sentence. " * 1000  # Long content
        
        # Chunk the content
        chunks = summarization_strategy._chunk_content(content, max_chunk_tokens=100)
        
        # Should return a list of chunks
        assert isinstance(chunks, list)
        assert len(chunks) > 0

class TestTokenOptimizer:
    """Test the TokenOptimizer implementation."""
    
    @pytest.fixture
    def token_optimizer(self, mock_openai_client):
        """Create a TokenOptimizer instance for testing."""
        return TokenOptimizer(mock_openai_client, max_tokens=1000)
    
    def test_init(self, token_optimizer, mock_openai_client):
        """Test initialization of TokenOptimizer."""
        assert token_optimizer.openai_client == mock_openai_client
        assert token_optimizer.max_tokens == 1000
    
    @pytest.mark.asyncio
    async def test_optimize_within_limit(self, token_optimizer):
        """Test optimizing content that is already within token limits."""
        content = "Short content"
        
        # Optimize the content
        result = await token_optimizer.optimize(content, max_tokens=1000)
        
        # Should return the same content since it's within limits
        assert isinstance(result, OptimizedContext)
        assert result.content == content
    
    @pytest.mark.asyncio
    async def test_optimize_exceeds_limit(self, token_optimizer, mock_openai_client):
        """Test optimizing content that exceeds token limits."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Optimized content"
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Create content that would exceed token limits
        content = "Very long content. " * 1000
        
        # Optimize the content
        result = await token_optimizer.optimize(content, max_tokens=100)
        
        # Should return optimized content
        assert isinstance(result, OptimizedContext)
        assert result.content == "Optimized content"

class TestContextWindowOptimizer:
    """Test the ContextWindowOptimizer implementation."""
    
    @pytest.fixture
    def context_optimizer(self, mock_openai_client):
        """Create a ContextWindowOptimizer instance for testing."""
        summarization_strategy = ProgressiveSummarization(mock_openai_client)
        token_optimizer = TokenOptimizer(mock_openai_client)
        return ContextWindowOptimizer(
            summarization_strategy=summarization_strategy,
            token_optimization_strategy=token_optimizer
        )
    
    def test_init(self, context_optimizer):
        """Test initialization of ContextWindowOptimizer."""
        assert context_optimizer.summarization_strategy is not None
        assert context_optimizer.token_optimization_strategy is not None
    
    @pytest.mark.asyncio
    async def test_optimize_context(self, context_optimizer, mock_openai_client):
        """Test optimizing context."""
        # Mock OpenAI responses
        mock_summarization_response = Mock()
        mock_summarization_response.choices = [Mock()]
        mock_summarization_response.choices[0].message.content = "Summarized content"
        mock_openai_client.chat.completions.create.return_value = mock_summarization_response
        
        mock_optimization_response = Mock()
        mock_optimization_response.choices = [Mock()]
        mock_optimization_response.choices[0].message.content = "Optimized content"
        mock_openai_client.chat.completions.create.return_value = mock_optimization_response
        
        # Create test content and entities
        content = "Test content to optimize"
        entities = [Entity("test", EntityType.PERSON, 0.8, {})]
        
        # Optimize the context
        result = await context_optimizer.optimize_context(content, entities, max_tokens=1000)
        
        # Check the result
        assert isinstance(result, OptimizedContext)
    
    def test_create_prompt_template(self, context_optimizer):
        """Test creating a prompt template."""
        # Create a test context
        context = OptimizedContext(
            content="Test context content",
            token_count=100,
            preserved_entities=[Entity("test", EntityType.PERSON, 0.8, {})],
            metadata={}
        )
        
        # Create a prompt template
        template = context_optimizer.create_prompt_template(context, template_type="default")
        
        # Should return a string
        assert isinstance(template, str)
        assert "Test context content" in template