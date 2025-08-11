from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime
import math
from app.models import Exchange, Topic, Conversation, Entity, SearchResult, MatchType
from openai import AsyncOpenAI
import tiktoken
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class ProcessedQuery:
    """
    Represents a processed and enriched query with various components for improved search.
    
    This dataclass encapsulates all the different aspects of a query that can be used
    for multi-faceted search and ranking. It includes the original query text, expanded
    search terms, extracted entities, temporal constraints, and semantic embedding.
    """
    original_query: str
    expanded_terms: List[str]
    entities: List[Entity]
    temporal_constraints: Optional[Dict[str, datetime]] = None
    semantic_embedding: Optional[List[float]] = None

class QueryProcessor(Protocol):
    """
    Protocol defining the interface for query processing.
    
    This protocol ensures that any query processor implementation must provide
    a process method that takes a raw query and context, and returns a ProcessedQuery
    with enriched information for better search results.
    """
    async def process(self, raw_query: str, context: Dict[str, Any]) -> ProcessedQuery:
        ...

class RelevanceScorer(Protocol):
    """
    Protocol defining the interface for relevance scoring.
    
    This protocol ensures that any relevance scorer implementation must provide
    a score method that evaluates how relevant an item is to a given query,
    taking into account the context of the search.
    """
    def score(self, item: Any, query: ProcessedQuery, context: Dict[str, Any]) -> float:
        ...

class SimpleQueryProcessor(QueryProcessor):
    """
    A basic implementation of QueryProcessor that uses OpenAI for query enrichment.
    
    This processor enhances raw queries by:
    1. Generating semantic embeddings for semantic search
    2. Expanding search terms for better matching
    3. Extracting named entities for entity-based search
    """
    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        logger.info("Initialized SimpleQueryProcessor with OpenAI client")

    async def process(self, raw_query: str, context: Dict[str, Any]) -> ProcessedQuery:
        """
        Process a raw query into an enriched ProcessedQuery object.
        
        The processing pipeline:
        1. Generates semantic embedding using OpenAI's embedding model
        2. Performs basic term expansion by splitting and deduplicating words
        3. Uses GPT to extract named entities from the query
        4. Handles various edge cases and error conditions gracefully
        
        Args:
            raw_query: The original search query string
            context: Additional context for processing the query
            
        Returns:
            ProcessedQuery object containing all enriched query components
        """
        logger.info(f"Processing query: {raw_query}")
        
        # Generate semantic embedding for the query
        logger.debug("Generating semantic embedding")
        embedding_response = await self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=raw_query
        )
        semantic_embedding = embedding_response.data[0].embedding
        
        # Extract key terms from the query
        words = raw_query.lower().split()
        expanded_terms = list(set(words))  # Basic term expansion
        logger.debug(f"Expanded terms: {expanded_terms}")
        
        # Use OpenAI to extract entities
        logger.debug("Extracting entities from query")
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Extract key entities from the query. Return a JSON array of objects with 'name' and 'type' fields.
                    Example format:
                    [
                        {"name": "entity1", "type": "PERSON"},
                        {"name": "entity2", "type": "LOCATION"}
                    ]
                    If there is only one entity, still return it as a single-item array.
                    Return ONLY the JSON array, nothing else."""
                },
                {"role": "user", "content": raw_query}
            ],
            response_format={ "type": "json_object" }
        )
        
        try:
            content = response.choices[0].message.content.strip()
            if not content:
                logger.warning("Empty response from OpenAI for entity extraction")
                entities = []
            else:
                # Try to parse the response as JSON
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, list):
                        entities = parsed
                    elif isinstance(parsed, dict):
                        # Handle single entity object
                        if "name" in parsed and "type" in parsed:
                            entities = [parsed]
                        # Handle object with entities array
                        elif "entities" in parsed and isinstance(parsed["entities"], list):
                            entities = parsed["entities"]
                        else:
                            logger.warning(f"Unexpected JSON structure: {parsed}")
                            entities = []
                    else:
                        logger.warning(f"Unexpected JSON structure: {parsed}")
                        entities = []
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    entities = []
            
            # Convert entity dictionaries to Entity objects
            entity_objects = []
            for entity in entities:
                if isinstance(entity, dict) and "name" in entity and "type" in entity:
                    entity_objects.append(Entity(
                        name=entity["name"],
                        type=entity["type"],
                        salience=1.0,  # Default salience
                        metadata={}  # Empty metadata
                    ))
            
            logger.debug(f"Extracted {len(entity_objects)} entities from query")
        except Exception as e:
            logger.warning(f"Failed to parse entities from response: {e}")
            entity_objects = []
        
        return ProcessedQuery(
            original_query=raw_query,
            expanded_terms=expanded_terms,
            entities=entity_objects,
            semantic_embedding=semantic_embedding
        )

class MultiFactorScorer(RelevanceScorer):
    """
    A sophisticated relevance scorer that combines multiple factors for ranking.
    
    This scorer implements a weighted scoring system that considers:
    1. Semantic similarity between query and content
    2. Temporal relevance based on creation time
    3. Content importance based on various metrics
    
    The scoring system uses a cache to optimize performance for repeated comparisons.
    """
    def __init__(
        self,
        semantic_weight: float = 0.4,
        temporal_weight: float = 0.3,
        importance_weight: float = 0.3,
        cache_size: int = 1000
    ):
        self.semantic_weight = semantic_weight
        self.temporal_weight = temporal_weight
        self.importance_weight = importance_weight
        self._similarity_cache = {}
        self._cache_size = cache_size
        logger.info(f"Initialized MultiFactorScorer with weights: semantic={semantic_weight}, temporal={temporal_weight}, importance={importance_weight}")

    def score(self, item: Any, query: ProcessedQuery, context: Dict[str, Any]) -> float:
        """
        Calculate a comprehensive relevance score for an item.
        
        The scoring process:
        1. Computes semantic similarity using cached cosine similarity
        2. Evaluates temporal relevance if temporal constraints exist
        3. Assesses content importance based on various metrics
        4. Combines scores using configurable weights
        
        Args:
            item: The item to score
            query: The processed query to score against
            context: Additional context for scoring
            
        Returns:
            float: A normalized score between 0 and 1
        """
        scores = []
        
        # Semantic similarity score with caching
        if query.semantic_embedding and hasattr(item, "embedding"):
            cache_key = (tuple(query.semantic_embedding), tuple(item.embedding))
            if cache_key in self._similarity_cache:
                semantic_score = self._similarity_cache[cache_key]
                logger.debug(f"Using cached semantic score for item {getattr(item, 'id', 'unknown')}")
            else:
                semantic_score = self._calculate_semantic_similarity(
                    query.semantic_embedding,
                    item.embedding
                )
                # Update cache with LRU-like behavior
                if len(self._similarity_cache) >= self._cache_size:
                    self._similarity_cache.pop(next(iter(self._similarity_cache)))
                self._similarity_cache[cache_key] = semantic_score
                logger.debug(f"Calculated new semantic score for item {getattr(item, 'id', 'unknown')}: {semantic_score:.3f}")
            scores.append(semantic_score * self.semantic_weight)
        
        # Enhanced temporal relevance score
        if query.temporal_constraints and hasattr(item, "created_at"):
            temporal_score = self._calculate_temporal_relevance(
                item.created_at,
                query.temporal_constraints,
                context.get("current_time", datetime.now())
            )
            logger.debug(f"Calculated temporal score for item {getattr(item, 'id', 'unknown')}: {temporal_score:.3f}")
            scores.append(temporal_score * self.temporal_weight)
        
        # Enhanced importance score with context
        if hasattr(item, "importance_score"):
            importance_score = self._calculate_importance_score(
                item.importance_score,
                item,
                context
            )
            logger.debug(f"Calculated importance score for item {getattr(item, 'id', 'unknown')}: {importance_score:.3f}")
            scores.append(importance_score * self.importance_weight)
        
        final_score = sum(scores) if scores else 0.0
        logger.debug(f"Final score for item {getattr(item, 'id', 'unknown')}: {final_score:.3f}")
        return final_score

    def _calculate_semantic_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors with optimizations.
        
        Implements several optimizations:
        1. Early exit for invalid or zero vectors
        2. Fast path for identical vectors
        3. Efficient dot product and norm calculations
        
        Args:
            vec1: First vector for comparison
            vec2: Second vector for comparison
            
        Returns:
            float: Cosine similarity between vectors (0 to 1)
        """
        # Cosine similarity with early exit for zero vectors
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            logger.debug("Invalid vectors for similarity calculation")
            return 0.0
        
        # Early exit if vectors are identical
        if vec1 == vec2:
            logger.debug("Identical vectors, returning 1.0")
            return 1.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            logger.debug("Zero norm vectors, returning 0.0")
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        logger.debug(f"Calculated cosine similarity: {similarity:.3f}")
        return similarity

    def _calculate_temporal_relevance(
        self,
        item_time: datetime,
        constraints: Dict[str, datetime],
        current_time: datetime
    ) -> float:
        """
        Calculate temporal relevance score with recency bias.
        
        The scoring considers:
        1. Whether the item falls within temporal constraints
        2. How close the item is to the start of the time range
        3. Recency bias that favors newer content
        4. Normalization to ensure scores are between 0 and 1
        
        Args:
            item_time: Creation time of the item
            constraints: Start and end time constraints
            current_time: Current time for recency calculation
            
        Returns:
            float: Temporal relevance score (0 to 1)
        """
        # Enhanced temporal relevance with recency bias
        if "start" in constraints and "end" in constraints:
            if item_time < constraints["start"] or item_time > constraints["end"]:
                logger.debug(f"Item time {item_time} outside constraints {constraints}")
                return 0.0
            
            total_duration = (constraints["end"] - constraints["start"]).total_seconds()
            if total_duration == 0:
                logger.debug("Zero duration constraints, returning 1.0")
                return 1.0
            
            # Calculate base temporal score
            time_diff = abs((item_time - constraints["start"]).total_seconds())
            base_score = 1.0 - (time_diff / total_duration)
            
            # Add recency bias
            recency_factor = 1.0 / (1.0 + (current_time - item_time).total_seconds() / (365 * 24 * 3600))  # Decay over years
            final_score = base_score * (0.7 + 0.3 * recency_factor)
            logger.debug(f"Calculated temporal score: base={base_score:.3f}, recency={recency_factor:.3f}, final={final_score:.3f}")
            return final_score
        
        logger.debug("No temporal constraints, returning 1.0")
        return 1.0

    def _calculate_importance_score(
        self,
        base_score: float,
        item: Any,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate importance score with contextual boosting.
        
        The scoring considers:
        1. Base importance score
        2. View count boosting
        3. Favorite count boosting
        4. User preference alignment
        5. Normalization to ensure scores are between 0 and 1
        
        Args:
            base_score: Initial importance score
            item: The item being scored
            context: Additional context including user preferences
            
        Returns:
            float: Normalized importance score (0 to 1)
        """
        # Enhanced importance scoring with context
        importance_score = base_score
        logger.debug(f"Base importance score: {base_score:.3f}")
        
        # Boost score based on item metadata
        if hasattr(item, "view_count"):
            view_boost = 1.0 + 0.1 * min(item.view_count / 1000, 1.0)
            importance_score *= view_boost
            logger.debug(f"Applied view count boost: {view_boost:.3f}")
        
        if hasattr(item, "favorite_count"):
            favorite_boost = 1.0 + 0.2 * min(item.favorite_count / 100, 1.0)
            importance_score *= favorite_boost
            logger.debug(f"Applied favorite count boost: {favorite_boost:.3f}")
        
        # Consider user preferences from context
        if "user_preferences" in context:
            user_prefs = context["user_preferences"]
            if hasattr(item, "category") and item.category in user_prefs.get("preferred_categories", []):
                importance_score *= 1.2
                logger.debug("Applied category preference boost: 1.2")
        
        final_score = min(importance_score, 1.0)  # Normalize to [0,1]
        logger.debug(f"Final importance score: {final_score:.3f}")
        return final_score

class RetrievalSystem:
    """
    Main retrieval system that coordinates query processing and result ranking.
    
    This system:
    1. Processes raw queries into enriched queries
    2. Scores and ranks items based on relevance
    3. Handles pagination and result formatting
    4. Provides detailed metadata about the search process
    """
    def __init__(
        self,
        query_processor: QueryProcessor,
        relevance_scorer: RelevanceScorer,
        batch_size: int = 100
    ):
        self.query_processor = query_processor
        self.relevance_scorer = relevance_scorer
        self.batch_size = batch_size
        logger.info(f"Initialized RetrievalSystem with batch_size={batch_size}")

    async def process_query(self, raw_query: str, context: Dict[str, Any]) -> ProcessedQuery:
        """
        Process a raw query into an enriched query.
        
        This is a convenience method that delegates to the query processor.
        
        Args:
            raw_query: The original search query
            context: Additional context for processing
            
        Returns:
            ProcessedQuery: The enriched query object
        """
        logger.info(f"Processing query: {raw_query}")
        return await self.query_processor.process(raw_query, context)

    def score_relevance(self, item: Any, query: ProcessedQuery, context: Dict[str, Any]) -> float:
        """
        Score an item's relevance to a query.
        
        This is a convenience method that delegates to the relevance scorer.
        
        Args:
            item: The item to score
            query: The processed query
            context: Additional context for scoring
            
        Returns:
            float: The relevance score
        """
        score = self.relevance_scorer.score(item, query, context)
        logger.debug(f"Scored item {getattr(item, 'id', 'unknown')}: {score:.3f}")
        return score

    async def rank_results(
        self,
        items: List[Any],
        query: ProcessedQuery,
        context: Dict[str, Any],
        max_results: int = 10,
        page: int = 1,
        items_per_page: int = 10
    ) -> Dict[str, Any]:
        """
        Rank and paginate search results.
        
        The ranking process:
        1. Processes items in batches for efficiency
        2. Scores each item using the relevance scorer
        3. Sorts items by score
        4. Applies pagination
        5. Determines match types for each result
        6. Returns formatted results with metadata
        
        Args:
            items: List of items to rank
            query: The processed query
            context: Additional context for ranking
            max_results: Maximum number of results to return
            page: Current page number
            items_per_page: Number of items per page
            
        Returns:
            Dict containing:
            - results: List of SearchResult objects
            - pagination: Pagination metadata
            - metadata: Query processing metadata
        """
        logger.info(f"Ranking {len(items)} items with page={page}, items_per_page={items_per_page}")
        
        # Process items in batches
        scored_items = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            logger.debug(f"Processing batch {i//self.batch_size + 1} with {len(batch)} items")
            batch_scores = [
                (item, self.score_relevance(item, query, context))
                for item in batch
            ]
            scored_items.extend(batch_scores)
        
        # Sort by score in descending order
        sorted_items = sorted(scored_items, key=lambda x: x[1], reverse=True)
        
        # Calculate pagination
        total_items = len(sorted_items)
        total_pages = math.ceil(total_items / items_per_page)
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        
        logger.debug(f"Pagination: page {page}/{total_pages}, items {start_idx}-{end_idx} of {total_items}")
        
        # Convert to SearchResult objects
        results = [
            SearchResult(
                entity=item,
                score=score,
                match_type=self._determine_match_type(item, query, score)
            )
            for item, score in sorted_items[start_idx:end_idx]
        ]
        
        logger.info(f"Returning {len(results)} results")
        return {
            "results": results,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "items_per_page": items_per_page
            },
            "metadata": {
                "query_terms": query.expanded_terms,
                "entities": query.entities,
                "temporal_constraints": query.temporal_constraints
            }
        }

    def _determine_match_type(self, item: Any, query: ProcessedQuery, score: float) -> MatchType:
        """
        Determine the type of match that led to the item's relevance.
        
        The match type is determined by:
        1. Available scoring components (semantic, temporal, importance)
        2. Relative contribution of each component to the final score
        3. Fallback to simpler match types when components are missing
        
        Args:
            item: The matched item
            query: The processed query
            score: The final relevance score
            
        Returns:
            MatchType: The type of match that was most significant
        """
        logger.debug(f"Determining match type for item {getattr(item, 'id', 'unknown')}")
        
        # Determine the type of match based on scoring components
        if not query.semantic_embedding or not hasattr(item, "embedding"):
            if query.temporal_constraints and hasattr(item, "created_at"):
                logger.debug("Match type: TEMPORAL (no semantic embedding)")
                return MatchType.TEMPORAL
            logger.debug("Match type: IMPORTANCE (no semantic embedding or temporal constraints)")
            return MatchType.IMPORTANCE
        
        if not query.temporal_constraints or not hasattr(item, "created_at"):
            logger.debug("Match type: SEMANTIC (no temporal constraints)")
            return MatchType.SEMANTIC
        
        if not hasattr(item, "importance_score"):
            logger.debug("Match type: HYBRID (missing importance score)")
            return MatchType.HYBRID
        
        # If all components are present, determine the dominant factor
        semantic_score = self.relevance_scorer._calculate_semantic_similarity(
            query.semantic_embedding,
            item.embedding
        ) * self.relevance_scorer.semantic_weight
        
        temporal_score = self.relevance_scorer._calculate_temporal_relevance(
            item.created_at,
            query.temporal_constraints,
            datetime.now()
        ) * self.relevance_scorer.temporal_weight
        
        importance_score = item.importance_score * self.relevance_scorer.importance_weight
        
        max_score = max(semantic_score, temporal_score, importance_score)
        
        match_type = (
            MatchType.SEMANTIC if max_score == semantic_score
            else MatchType.TEMPORAL if max_score == temporal_score
            else MatchType.IMPORTANCE
        )
        
        logger.debug(f"Match type: {match_type} (scores: semantic={semantic_score:.3f}, temporal={temporal_score:.3f}, importance={importance_score:.3f})")
        return match_type