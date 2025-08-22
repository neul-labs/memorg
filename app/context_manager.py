from typing import List, Dict, Any, Protocol, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from openai import AsyncOpenAI
import tiktoken
import logging
from app.models import Exchange, Topic, Conversation, Entity
import json

# Configure logger
logger = logging.getLogger(__name__)

@dataclass
class CompressedEntity:
    """Represents a compressed version of an entity with metadata about the compression process.
    
    Attributes:
        original_id: Unique identifier of the original entity
        compressed_content: The summarized/compressed version of the content
        preserved_entities: List of important entities that were preserved during compression
        compression_ratio: Ratio of compressed size to original size (0-1)
    """
    original_id: str
    compressed_content: str
    preserved_entities: List[Entity]
    compression_ratio: float

@dataclass
class AllocationResult:
    """Represents the result of a memory allocation attempt.
    
    Attributes:
        allocation_id: Unique identifier for the allocation
        allocated: Whether the allocation was successful
        token_count: Number of tokens requested/allocated
    """
    allocation_id: str
    allocated: bool
    token_count: int

@dataclass
class MemoryUsage:
    """Represents the current state of memory usage.
    
    Attributes:
        used: Number of tokens currently in use
        available: Number of tokens still available
        allocations: Dictionary mapping allocation IDs to their token counts
    """
    used: int
    available: int
    allocations: Dict[str, int]

class PrioritizationStrategy(Protocol):
    """Protocol defining the interface for context prioritization strategies.
    
    This protocol ensures that all prioritization strategies implement methods
    for calculating importance scores and ranking context items.
    """
    def calculate_importance(self, exchange: Exchange, context: Dict[str, Any]) -> float:
        """Calculate the importance score for an exchange given the current context."""
        ...

    def rank_context_items(self, items: List[Any], max_items: int) -> List[Any]:
        """Rank and return the top N most important items from a list."""
        ...

class RecencyWeightedStrategy(PrioritizationStrategy):
    """Prioritization strategy that weights items based on recency and importance.
    
    This strategy applies an exponential decay to importance scores based on time,
    ensuring that recent items are given higher priority while still considering
    their base importance.
    """
    def __init__(self, decay_factor: float = 0.1):
        """Initialize the strategy with a decay factor for time-based weighting."""
        self.decay_factor = decay_factor
        logger.info(f"Initialized RecencyWeightedStrategy with decay_factor={decay_factor}")

    def calculate_importance(self, exchange: Exchange, context: Dict[str, Any]) -> float:
        """Calculate importance score by applying time-based decay to the base importance.
        
        The decay follows an exponential function where more recent items retain
        more of their original importance score.
        """
        # Calculate time-based decay
        now = datetime.now(timezone.utc)
        time_diff = (now - exchange.created_at).total_seconds()
        time_decay = math.exp(-self.decay_factor * time_diff)
        
        # Combine with existing importance score
        final_score = exchange.importance_score * time_decay
        logger.debug(f"Calculated importance score for exchange {exchange.id}: {final_score:.3f} (time_decay={time_decay:.3f})")
        return final_score

    def rank_context_items(self, items: List[Any], max_items: int) -> List[Any]:
        """Sort items by their importance scores and return the top N items."""
        # Sort items by importance score
        sorted_items = sorted(items, key=lambda x: x.importance_score, reverse=True)
        result = sorted_items[:max_items]
        logger.debug(f"Ranked {len(items)} items, returning top {len(result)} items")
        return result

class TopicCoherenceStrategy(PrioritizationStrategy):
    """Prioritization strategy that considers topic coherence and entity overlap.
    
    This strategy boosts the importance of items that share entities with the
    current topic, promoting contextually relevant information.
    """
    def calculate_importance(self, exchange: Exchange, context: Dict[str, Any]) -> float:
        """Calculate importance based on entity overlap with current topic.
        
        Combines base importance with a coherence score derived from the
        proportion of shared entities between the exchange and current topic.
        """
        # Calculate topic coherence based on entity overlap
        current_topic = context.get("current_topic")
        if not current_topic:
            logger.debug(f"No current topic in context for exchange {exchange.id}, using base importance score")
            return exchange.importance_score

        # Calculate entity overlap score
        current_entities = {e.name for e in current_topic.key_entities}
        exchange_entities = {e.name for e in exchange.user_message.parsed_content.entities}
        
        overlap = len(current_entities.intersection(exchange_entities))
        total = len(current_entities.union(exchange_entities))
        
        coherence_score = overlap / total if total > 0 else 0
        final_score = exchange.importance_score * (0.7 + 0.3 * coherence_score)
        
        logger.debug(f"Calculated coherence score for exchange {exchange.id}: {final_score:.3f} (overlap={overlap}/{total})")
        return final_score

    def rank_context_items(self, items: List[Any], max_items: int) -> List[Any]:
        """Sort items by their importance scores and return the top N items."""
        # Sort items by importance score
        sorted_items = sorted(items, key=lambda x: x.importance_score, reverse=True)
        result = sorted_items[:max_items]
        logger.debug(f"Ranked {len(items)} items, returning top {len(result)} items")
        return result

class CompressionStrategy(Protocol):
    """Protocol defining the interface for content compression strategies.
    
    Ensures that all compression strategies implement a method to compress
    entities while preserving important information.
    """
    async def compress(self, entity: Any) -> CompressedEntity:
        """Compress an entity while preserving its key information."""
        ...

class ExtractiveSummarization(CompressionStrategy):
    """Compression strategy that uses OpenAI to create extractive summaries.
    
    This strategy uses GPT-4 to create concise summaries while preserving
    important entities and their relationships.
    """
    def __init__(self, openai_client: AsyncOpenAI):
        """Initialize the strategy with an OpenAI client for API calls."""
        self.openai_client = openai_client
        logger.info("Initialized ExtractiveSummarization with OpenAI client")

    async def compress(self, entity: Any) -> CompressedEntity:
        """Create a compressed version of the entity using OpenAI's summarization.
        
        Uses GPT-4 to generate a concise summary that preserves important entities
        and their relationships. Falls back to basic summarization if the API call fails.
        """
        logger.info(f"Starting compression for entity {getattr(entity, 'id', 'unknown')}")
        system_prompt = """You are a summarization expert that helps compress content while preserving key information.
        Given a piece of content, create a concise summary that:
        1. Preserves all important entities and their relationships
        2. Maintains the core meaning and context
        3. Eliminates redundancy and unnecessary details
        4. Keeps the summary coherent and readable
        
        Return the summary in a JSON object with the following structure:
        {
            "summary": "your summary text here",
            "preserved_entities": ["entity1", "entity2", ...]
        }"""

        try:
            # Get the content to summarize
            content = entity.content if hasattr(entity, "content") else str(entity)
            
            # Get the entities to preserve
            entities = entity.key_entities if hasattr(entity, "key_entities") else []
            entity_names = [e.name for e in entities]
            
            logger.debug(f"Compressing content with {len(entity_names)} entities to preserve")
            
            # Create the user prompt with entity preservation instructions
            user_prompt = f"""Content to summarize:
{content}

Important entities to preserve:
{', '.join(entity_names)}

Please create a concise summary that preserves these entities and their relationships."""

            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            # Parse the response
            try:
                content = response.choices[0].message.content.strip()
                if not content:
                    raise ValueError("Empty response from OpenAI")
                
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError(f"Expected JSON object, got {type(parsed)}")
                
                summary = parsed.get("summary", "")
                preserved_entities = parsed.get("preserved_entities", [])
                
                if not summary:
                    raise ValueError("No summary found in response")
                
                # Calculate compression ratio
                original_length = len(content.split())
                summary_length = len(summary.split())
                compression_ratio = summary_length / original_length if original_length > 0 else 1.0
                
                logger.info(f"Successfully compressed content: {compression_ratio:.2f} compression ratio")
                
                return CompressedEntity(
                    original_id=entity.id if hasattr(entity, "id") else "",
                    compressed_content=summary,
                    preserved_entities=entities,  # Keep original entities
                    compression_ratio=compression_ratio
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise
            
        except Exception as e:
            # Fallback to basic summarization if OpenAI call fails
            logger.error(f"Error in OpenAI summarization: {e}", exc_info=True)
            return CompressedEntity(
                original_id=entity.id if hasattr(entity, "id") else "",
                compressed_content=entity.summary if hasattr(entity, "summary") else str(entity),
                preserved_entities=entity.key_entities if hasattr(entity, "key_entities") else [],
                compression_ratio=0.5
            )

class WorkingMemory:
    """Manages a fixed-size token budget for context items.
    
    This class handles allocation and deallocation of tokens for different
    context items, ensuring the total usage stays within capacity.
    """
    def __init__(self, capacity: int):
        """Initialize with a maximum token capacity."""
        self.capacity = capacity
        self.allocations: Dict[str, int] = {}
        self._next_allocation_id = 0
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        logger.info(f"Initialized WorkingMemory with capacity={capacity} tokens")

    def allocate_tokens(self, content: str, priority: float) -> AllocationResult:
        """Attempt to allocate tokens for content, with cleanup if necessary.
        
        If there isn't enough space, attempts to free up memory by removing
        low-priority allocations before making the new allocation.
        """
        # Count tokens using tiktoken
        estimated_tokens = len(self.encoding.encode(content))
        logger.debug(f"Requesting allocation of {estimated_tokens} tokens with priority {priority:.2f}")
        
        # Check if we have enough capacity
        current_usage = sum(self.allocations.values())
        if current_usage + estimated_tokens > self.capacity:
            # Try to free up space by removing low priority allocations
            logger.info(f"Insufficient memory ({current_usage}/{self.capacity}), attempting cleanup")
            self._cleanup_low_priority()
            current_usage = sum(self.allocations.values())
            
            if current_usage + estimated_tokens > self.capacity:
                logger.warning(f"Failed to allocate {estimated_tokens} tokens after cleanup")
                return AllocationResult(
                    allocation_id="",
                    allocated=False,
                    token_count=estimated_tokens
                )

        # Allocate tokens
        allocation_id = f"alloc_{self._next_allocation_id}"
        self._next_allocation_id += 1
        self.allocations[allocation_id] = estimated_tokens
        
        logger.info(f"Successfully allocated {estimated_tokens} tokens with id {allocation_id}")
        return AllocationResult(
            allocation_id=allocation_id,
            allocated=True,
            token_count=estimated_tokens
        )

    def release_tokens(self, allocation_id: str) -> None:
        """Release tokens associated with an allocation ID."""
        if allocation_id in self.allocations:
            tokens = self.allocations[allocation_id]
            del self.allocations[allocation_id]
            logger.info(f"Released {tokens} tokens from allocation {allocation_id}")
        else:
            logger.warning(f"Attempted to release non-existent allocation {allocation_id}")

    def get_current_usage(self) -> MemoryUsage:
        """Get the current state of memory usage."""
        used = sum(self.allocations.values())
        usage = MemoryUsage(
            used=used,
            available=self.capacity - used,
            allocations=self.allocations.copy()
        )
        logger.debug(f"Current memory usage: {used}/{self.capacity} tokens")
        return usage

    def _cleanup_low_priority(self) -> None:
        """Internal method to free up memory by removing oldest allocations."""
        # Simple cleanup strategy: remove oldest allocations
        if self.allocations:
            oldest_allocation = min(self.allocations.keys())
            tokens = self.allocations[oldest_allocation]
            del self.allocations[oldest_allocation]
            logger.info(f"Cleaned up allocation {oldest_allocation}, freed {tokens} tokens")

class ContextManager:
    """Manages context items using prioritization, compression, and memory management.
    
    This class coordinates between different strategies to maintain relevant
    context while staying within memory constraints.
    """
    def __init__(
        self,
        prioritization_strategy: PrioritizationStrategy,
        compression_strategy: CompressionStrategy,
        working_memory: WorkingMemory
    ):
        """Initialize with custom strategies for prioritization, compression, and memory management."""
        self.prioritization_strategy = prioritization_strategy
        self.compression_strategy = compression_strategy
        self.working_memory = working_memory
        logger.info("Initialized ContextManager with custom strategies")

    def update_importance(self, exchange: Exchange, context: Dict[str, Any]) -> float:
        """Update the importance score of an exchange based on current context."""
        importance = self.prioritization_strategy.calculate_importance(exchange, context)
        logger.debug(f"Updated importance score for exchange {exchange.id}: {importance:.3f}")
        return importance

    def rank_context(self, items: List[Any], max_items: int) -> List[Any]:
        """Rank and return the most important context items."""
        ranked_items = self.prioritization_strategy.rank_context_items(items, max_items)
        logger.debug(f"Ranked {len(items)} context items, returning top {len(ranked_items)}")
        return ranked_items

    async def compress_entity(self, entity: Any) -> CompressedEntity:
        """Create a compressed version of an entity using the compression strategy."""
        logger.info(f"Starting entity compression for {getattr(entity, 'id', 'unknown')}")
        compressed = await self.compression_strategy.compress(entity)
        logger.info(f"Completed entity compression with ratio {compressed.compression_ratio:.2f}")
        return compressed

    def allocate_memory(self, content: str, priority: float) -> AllocationResult:
        """Attempt to allocate memory for content with a given priority."""
        result = self.working_memory.allocate_tokens(content, priority)
        if result.allocated:
            logger.info(f"Successfully allocated {result.token_count} tokens")
        else:
            logger.warning(f"Failed to allocate {result.token_count} tokens")
        return result

    def release_memory(self, allocation_id: str) -> None:
        """Release memory associated with an allocation ID."""
        logger.info(f"Releasing memory allocation {allocation_id}")
        self.working_memory.release_tokens(allocation_id)

    def get_memory_usage(self) -> MemoryUsage:
        """Get the current state of memory usage."""
        usage = self.working_memory.get_current_usage()
        logger.debug(f"Current memory usage: {usage.used}/{usage.available + usage.used} tokens")
        return usage 