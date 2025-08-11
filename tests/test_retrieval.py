import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from app.retrieval import (
    ProcessedQuery,
    SimpleQueryProcessor,
    MultiFactorScorer,
    RetrievalSystem
)
from app.models import Exchange, Message, ParsedContent, Entity, EntityType, MatchType

class TestSimpleQueryProcessor:
    """Test the SimpleQueryProcessor implementation."""
    
    @pytest.fixture
    def query_processor(self, mock_openai_client):
        """Create a SimpleQueryProcessor instance for testing."""
        return SimpleQueryProcessor(mock_openai_client)
    
    def test_init(self, query_processor, mock_openai_client):
        """Test initialization of SimpleQueryProcessor."""
        assert query_processor.openai_client == mock_openai_client
    
    @pytest.mark.asyncio
    async def test_process_query(self, query_processor, mock_openai_client):
        """Test processing a query."""
        # Mock OpenAI embedding response
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock()]
        mock_embedding_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4]
        mock_openai_client.embeddings.create.return_value = mock_embedding_response
        
        # Mock OpenAI entity extraction response
        mock_entity_response = Mock()
        mock_entity_response.choices = [Mock()]
        mock_entity_response.choices[0].message.content = '[{"name": "test", "type": "PERSON"}]'
        mock_openai_client.chat.completions.create.return_value = mock_entity_response
        
        # Process a query
        raw_query = "Test query about something"
        result = await query_processor.process(raw_query, {})
        
        # Check the result
        assert isinstance(result, ProcessedQuery)
        assert result.original_query == raw_query
        assert isinstance(result.expanded_terms, list)
        assert isinstance(result.entities, list)
        assert isinstance(result.semantic_embedding, list)

class TestMultiFactorScorer:
    """Test the MultiFactorScorer implementation."""
    
    def test_init(self):
        """Test initialization of MultiFactorScorer."""
        scorer = MultiFactorScorer(
            semantic_weight=0.5,
            temporal_weight=0.3,
            importance_weight=0.2
        )
        assert scorer.semantic_weight == 0.5
        assert scorer.temporal_weight == 0.3
        assert scorer.importance_weight == 0.2
    
    def test_score_without_embeddings(self):
        """Test scoring an item without embeddings."""
        scorer = MultiFactorScorer()
        
        # Create a mock item without embedding
        item = Mock()
        item.importance_score = 0.8
        # Ensure the item doesn't have view_count or favorite_count attributes
        if hasattr(item, 'view_count'):
            delattr(item, 'view_count')
        if hasattr(item, 'favorite_count'):
            delattr(item, 'favorite_count')
        
        # Create a processed query without embedding
        query = ProcessedQuery(
            original_query="test query",
            expanded_terms=["test", "query"],
            entities=[]
        )
        
        # Score the item
        score = scorer.score(item, query, {})
        
        # Should score based on importance only
        assert isinstance(score, float)
        assert score >= 0
    
    def test_score_with_embeddings(self):
        """Test scoring an item with embeddings."""
        scorer = MultiFactorScorer()
        
        # Create a mock item with embedding
        item = Mock()
        item.importance_score = 0.8
        item.embedding = [0.1, 0.2, 0.3, 0.4]
        # Ensure the item doesn't have view_count or favorite_count attributes
        if hasattr(item, 'view_count'):
            delattr(item, 'view_count')
        if hasattr(item, 'favorite_count'):
            delattr(item, 'favorite_count')
        
        # Create a processed query with embedding
        query = ProcessedQuery(
            original_query="test query",
            expanded_terms=["test", "query"],
            entities=[],
            semantic_embedding=[0.2, 0.3, 0.4, 0.5]
        )
        
        # Score the item
        score = scorer.score(item, query, {})
        
        # Should return a score
        assert isinstance(score, float)
        assert score >= 0

class TestRetrievalSystem:
    """Test the RetrievalSystem implementation."""
    
    @pytest.fixture
    def retrieval_system(self, mock_openai_client):
        """Create a RetrievalSystem instance for testing."""
        query_processor = SimpleQueryProcessor(mock_openai_client)
        relevance_scorer = MultiFactorScorer()
        return RetrievalSystem(
            query_processor=query_processor,
            relevance_scorer=relevance_scorer
        )
    
    def test_init(self, retrieval_system):
        """Test initialization of RetrievalSystem."""
        assert retrieval_system.query_processor is not None
        assert retrieval_system.relevance_scorer is not None
    
    @pytest.mark.asyncio
    async def test_process_query(self, retrieval_system, mock_openai_client):
        """Test processing a query through the retrieval system."""
        # Mock OpenAI responses
        mock_embedding_response = Mock()
        mock_embedding_response.data = [Mock()]
        mock_embedding_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4]
        mock_openai_client.embeddings.create.return_value = mock_embedding_response
        
        mock_entity_response = Mock()
        mock_entity_response.choices = [Mock()]
        mock_entity_response.choices[0].message.content = '[{"name": "test", "type": "PERSON"}]'
        mock_openai_client.chat.completions.create.return_value = mock_entity_response
        
        # Process a query
        raw_query = "Test query about something"
        result = await retrieval_system.process_query(raw_query, {})
        
        # Check the result
        assert isinstance(result, ProcessedQuery)
    
    def test_score_relevance(self, retrieval_system):
        """Test scoring relevance of an item."""
        # Create a mock item
        item = Mock()
        item.importance_score = 0.8
        # Ensure the item doesn't have view_count or favorite_count attributes
        if hasattr(item, 'view_count'):
            delattr(item, 'view_count')
        if hasattr(item, 'favorite_count'):
            delattr(item, 'favorite_count')
        
        # Create a processed query
        query = ProcessedQuery(
            original_query="test query",
            expanded_terms=["test", "query"],
            entities=[]
        )
        
        # Score relevance
        score = retrieval_system.score_relevance(item, query, {})
        
        # Should return a score
        assert isinstance(score, float)
        assert score >= 0
    
    @pytest.mark.asyncio
    async def test_rank_results(self, retrieval_system):
        """Test ranking results."""
        # Create mock items
        item1 = Mock()
        item1.importance_score = 0.9
        item1.id = "item-1"
        # Ensure the items don't have view_count or favorite_count attributes
        if hasattr(item1, 'view_count'):
            delattr(item1, 'view_count')
        if hasattr(item1, 'favorite_count'):
            delattr(item1, 'favorite_count')
        
        item2 = Mock()
        item2.importance_score = 0.5
        item2.id = "item-2"
        # Ensure the items don't have view_count or favorite_count attributes
        if hasattr(item2, 'view_count'):
            delattr(item2, 'view_count')
        if hasattr(item2, 'favorite_count'):
            delattr(item2, 'favorite_count')
        
        items = [item1, item2]
        
        # Create a processed query
        query = ProcessedQuery(
            original_query="test query",
            expanded_terms=["test", "query"],
            entities=[]
        )
        
        # Rank results
        result = await retrieval_system.rank_results(items, query, {}, max_results=10)
        
        # Check the result
        assert isinstance(result, dict)
        assert "results" in result
        assert "pagination" in result
        assert "metadata" in result
        assert isinstance(result["results"], list)