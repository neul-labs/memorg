from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from openai import AsyncOpenAI

from app.memory.core import MemoryItem, MemoryType, MemoryScope, SearchResult, MemoryManager
from app.memory.store import HierarchicalMemoryStore
from app.context_manager import ContextManager, RecencyWeightedStrategy, ExtractiveSummarization, WorkingMemory
from app.retrieval import RetrievalSystem, SimpleQueryProcessor, MultiFactorScorer
from app.window_optimizer import ContextWindowOptimizer, ProgressiveSummarization, TokenOptimizer

class GenericMemoryManager(MemoryManager):
    """Generic memory manager that provides high-level memory operations."""
    
    def __init__(self, memory_store: HierarchicalMemoryStore, openai_client: AsyncOpenAI):
        self.memory_store = memory_store
        self.openai_client = openai_client
        
        # Initialize context management components
        self.context_manager = ContextManager(
            prioritization_strategy=RecencyWeightedStrategy(),
            compression_strategy=ExtractiveSummarization(openai_client),
            working_memory=WorkingMemory(capacity=4096)
        )
        
        # Initialize retrieval system
        self.retrieval_system = RetrievalSystem(
            query_processor=SimpleQueryProcessor(openai_client),
            relevance_scorer=MultiFactorScorer()
        )
        
        # Initialize window optimizer
        self.window_optimizer = ContextWindowOptimizer(
            summarization_strategy=ProgressiveSummarization(openai_client),
            token_optimization_strategy=TokenOptimizer(openai_client=openai_client)
        )
    
    async def create_item(
        self,
        content: str,
        item_type: MemoryType,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> MemoryItem:
        """Create a new memory item."""
        item = MemoryItem(
            id=str(uuid.uuid4()),
            type=item_type,
            content=content,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            parent_id=parent_id,
            tags=tags or []
        )
        
        # Generate embedding if we have content and OpenAI client
        if content and self.openai_client:
            try:
                embedding_response = await self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=content
                )
                item.embedding = embedding_response.data[0].embedding
            except Exception as e:
                # If embedding fails, we'll proceed without it
                pass
        
        # Store the item
        await self.memory_store.store(item)
        return item
    
    async def update_importance(self, item_id: str, importance_score: float) -> bool:
        """Update the importance score of a memory item."""
        return await self.memory_store.update(item_id, {"importance_score": importance_score})
    
    async def add_tags(self, item_id: str, tags: List[str]) -> bool:
        """Add tags to a memory item."""
        item = await self.memory_store.retrieve(item_id)
        if not item:
            return False
        
        # Add new tags (avoiding duplicates)
        existing_tags = set(item.tags)
        new_tags = set(tags)
        combined_tags = list(existing_tags.union(new_tags))
        
        return await self.memory_store.update(item_id, {"tags": combined_tags})
    
    async def remove_tags(self, item_id: str, tags: List[str]) -> bool:
        """Remove tags from a memory item."""
        item = await self.memory_store.retrieve(item_id)
        if not item:
            return False
        
        # Remove specified tags
        tags_to_remove = set(tags)
        filtered_tags = [tag for tag in item.tags if tag not in tags_to_remove]
        
        return await self.memory_store.update(item_id, {"tags": filtered_tags})
    
    async def search(
        self,
        query: str,
        scope: MemoryScope = MemoryScope.GLOBAL,
        item_types: Optional[List[MemoryType]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search memory for relevant items."""
        # Build filters based on search parameters
        filters = {}
        if item_types:
            filters["type"] = [t.value for t in item_types]
        if tags:
            filters["tags"] = tags
        
        # Create memory query
        memory_query = {
            "text": query,
            "scope": scope,
            "filters": filters,
            "limit": limit
        }
        
        # Use the retrieval system to process the query
        processed_query = await self.retrieval_system.process_query(query, {})
        
        # Get initial results from memory store
        initial_results = await self.memory_store.search(memory_query)
        
        # Score and rank results using the retrieval system
        context = {}  # Empty context for now
        ranked_results = await self.retrieval_system.rank_results(
            [result.item for result in initial_results],
            processed_query,
            context,
            limit
        )
        
        return ranked_results["results"]
    
    async def get_context(
        self,
        item_id: str,
        depth: int = 3,
        include_siblings: bool = False
    ) -> List[MemoryItem]:
        """Get contextual items related to a specific item."""
        context_items = []
        
        # Start with the item itself
        item = await self.memory_store.retrieve(item_id)
        if not item:
            return context_items
        
        context_items.append(item)
        
        # Get ancestors up to the specified depth
        current_item = item
        for _ in range(depth):
            if current_item.parent_id:
                parent = await self.memory_store.retrieve(current_item.parent_id)
                if parent:
                    context_items.append(parent)
                    current_item = parent
                else:
                    break
            else:
                break
        
        # Get children if requested
        if include_siblings:
            children = await self.memory_store.get_children(item_id)
            context_items.extend(children)
        
        # Rank context items by importance
        ranked_items = self.context_manager.rank_context(context_items, len(context_items))
        return ranked_items
    
    async def optimize_context(
        self,
        items: List[MemoryItem],
        max_tokens: int
    ) -> List[MemoryItem]:
        """Optimize a list of memory items to fit within token limits."""
        # Convert items to text for optimization
        content = "\n\n".join([f"{item.type.value}: {item.content}" for item in items])
        
        # Extract entities (simplified for now)
        entities = []
        for item in items:
            if hasattr(item, 'entities'):
                entities.extend(item.entities)
        
        # Optimize using window optimizer
        optimized = await self.window_optimizer.optimize_context(
            content,
            entities,
            max_tokens
        )
        
        # For now, we'll just return the original items
        # In a more sophisticated implementation, we might return compressed versions
        return items