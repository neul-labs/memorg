from typing import Dict, Any, Optional, List
import asyncio
import logging
from datetime import datetime
from openai import AsyncOpenAI

from app.models import (
    Session, Conversation, Topic, Exchange,
    Entity, EntityType, SearchScope, SearchResult
)
from app.context_store import ContextStore, StorageAdapter, VectorStore
from app.context_manager import (
    ContextManager, RecencyWeightedStrategy,
    ExtractiveSummarization, WorkingMemory
)
from app.retrieval import (
    RetrievalSystem, SimpleQueryProcessor,
    MultiFactorScorer
)
from app.window_optimizer import (
    ContextWindowOptimizer, ProgressiveSummarization,
    TokenOptimizer
)
from app.storage.sqlite_storage import SQLiteStorageAdapter
from app.vector_store.usearch_vector_store import USearchVectorStore

# Import new memory components
from app.memory.core import MemoryType, MemoryScope
from app.memory.store import HierarchicalMemoryStore
from app.memory.manager import GenericMemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memorg.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MemorgSystem:
    """
    Main system class that orchestrates all components of the memory organization system.
    Integrates storage, context management, retrieval, and optimization components.
    """
    def __init__(
        self,
        storage: StorageAdapter,  # Handles persistent storage of data
        vector_store: VectorStore,  # Manages vector embeddings for semantic search
        openai_client: AsyncOpenAI  # OpenAI client for AI operations
    ):
        # Initialize OpenAI client for AI operations
        self.openai_client = openai_client
        
        # Initialize context store which manages data persistence and retrieval
        self.context_store = ContextStore(storage, vector_store, openai_client)
        
        # Initialize context manager which handles memory prioritization and compression
        self.context_manager = ContextManager(
            prioritization_strategy=RecencyWeightedStrategy(),  # Prioritizes recent information
            compression_strategy=ExtractiveSummarization(openai_client),  # Compresses information
            working_memory=WorkingMemory(capacity=4096)  # Manages active memory
        )
        
        # Initialize retrieval system for searching and ranking information
        self.retrieval_system = RetrievalSystem(
            query_processor=SimpleQueryProcessor(openai_client),  # Processes search queries
            relevance_scorer=MultiFactorScorer()  # Scores search results
        )
        
        # Initialize window optimizer for managing context size
        self.window_optimizer = ContextWindowOptimizer(
            summarization_strategy=ProgressiveSummarization(openai_client),  # Progressive summarization
            token_optimization_strategy=TokenOptimizer(openai_client=openai_client)  # Token management
        )
        
        # Initialize new memory components for broader workflow usage
        self.memory_store = HierarchicalMemoryStore(storage, vector_store, openai_client)
        self.memory_manager = GenericMemoryManager(self.memory_store, openai_client)
        
        logger.info("Initialized MemorgSystem with all components")

    async def create_session(self, user_id: str, config: Dict[str, Any]) -> Session:
        """
        Creates a new session for a user with specified configuration.
        A session represents a user's interaction period with the system.
        """
        logger.info("Creating new session for user_id=%s", user_id)
        try:
            session = await self.context_store.create_session(user_id, config)
            logger.info("Successfully created session with id=%s", session.id)
            return session
        except Exception as e:
            logger.error("Failed to create session: %s", str(e), exc_info=True)
            raise

    async def start_conversation(self, session_id: str) -> Conversation:
        """
        Starts a new conversation within a session.
        A conversation represents a continuous interaction thread.
        """
        logger.info("Starting new conversation for session_id=%s", session_id)
        try:
            conversation = await self.context_store.create_conversation(session_id)
            logger.info("Successfully created conversation with id=%s", conversation.id)
            return conversation
        except Exception as e:
            logger.error("Failed to create conversation: %s", str(e), exc_info=True)
            raise

    async def add_exchange(
        self,
        topic_id: str,
        user_message: str,
        system_message: str
    ) -> Exchange:
        """
        Adds a new exchange (interaction) to a topic.
        An exchange represents a single back-and-forth interaction.
        Also updates the importance score of the exchange.
        """
        logger.info("Adding exchange to topic_id=%s", topic_id)
        try:
            # Create the exchange in storage
            exchange = await self.context_store.add_exchange(
                topic_id,
                user_message,
                system_message
            )
            logger.debug("Exchange created with id=%s", exchange.id)
            
            # Update importance score based on context
            context = {"current_topic": await self.context_store.get_topic(topic_id)}
            exchange.importance_score = self.context_manager.update_importance(
                exchange,
                context
            )
            logger.debug("Updated importance score for exchange=%s: %f", 
                        exchange.id, exchange.importance_score)
            
            return exchange
        except Exception as e:
            logger.error("Failed to add exchange: %s", str(e), exc_info=True)
            raise

    async def search_context(
        self,
        query: str,
        scope: SearchScope = SearchScope.ALL,
        max_results: int = 10
    ) -> list:
        """
        Searches the context using both semantic and keyword-based approaches.
        Combines vector search with traditional keyword search for comprehensive results.
        """
        logger.info("Searching context with query='%s', scope=%s, max_results=%d", 
                   query, scope, max_results)
        try:
            # Process the query for both semantic and keyword search
            processed_query = await self.retrieval_system.process_query(query, {})
            logger.debug("Query processed: %s", processed_query)
            
            # Get items based on scope
            items = []
            if scope == SearchScope.ALL:
                # First try semantic search using vector store
                if processed_query.semantic_embedding:
                    vector_results = await self.context_store.vector_store.search_nearest(
                        processed_query.semantic_embedding,
                        max_results * 2  # Get more results to account for filtering
                    )
                    
                    # Process vector search results
                    for result in vector_results:
                        items.append({
                            "id": result["id"],
                            "content": result["text_content"],
                            "score": result["score"],
                            "metadata": result["metadata"]
                        })
                        logger.debug(f"Added vector result with id {result['id']} and score {result['score']}")
                
                # Fall back to keyword search if needed
                if len(items) < max_results:
                    for collection in ["sessions", "conversations", "topics", "exchanges"]:
                        collection_items = await self.context_store.storage.query(
                            collection,
                            {"$text": {"$search": query}}
                        )
                        items.extend(collection_items)
                        logger.debug("Retrieved %d items from collection %s", 
                                   len(collection_items), collection)
            
            # Rank and return final results
            ranked_results = await self.retrieval_system.rank_results(
                items,
                processed_query,
                {},
                max_results
            )
            logger.info("Search completed with %d results", len(ranked_results["results"]))
            
            print(ranked_results["results"])

            return ranked_results["results"]
        except Exception as e:
            logger.error("Search failed: %s", str(e), exc_info=True)
            raise

    async def optimize_context(
        self,
        content: str,
        entities: list[Entity],
        max_tokens: int
    ) -> str:
        """
        Optimizes the context by summarizing and managing token usage.
        Ensures the context fits within specified token limits while preserving important information.
        """
        logger.info("Optimizing context with %d entities, max_tokens=%d", 
                   len(entities), max_tokens)
        try:
            # Optimize the context using window optimizer
            optimized = await self.window_optimizer.optimize_context(
                content,
                entities,
                max_tokens
            )
            logger.debug("Context optimized, new length: %d", len(optimized.content))
            
            # Create a prompt template from optimized content
            template = self.window_optimizer.create_prompt_template(optimized)
            logger.info("Context optimization complete")
            return template
        except Exception as e:
            logger.error("Context optimization failed: %s", str(e), exc_info=True)
            raise

    async def get_memory_usage(self) -> Dict[str, int]:
        """
        Retrieves current memory usage statistics including token counts and storage metrics.
        Provides insights into system resource utilization.
        """
        try:
            # Get storage statistics
            storage_stats = await self.context_store.storage.get_stats()
            
            # Get vector store statistics
            vector_stats = await self.context_store.vector_store.get_stats()
            
            # Calculate total tokens across all collections
            total_tokens = 0
            for collection in ["sessions", "conversations", "topics", "exchanges"]:
                items = await self.context_store.storage.query(collection, {})
                for item in items:
                    if isinstance(item, dict) and "content" in item:
                        # Estimate tokens (roughly 4 characters per token)
                        total_tokens += len(item["content"]) // 4
            
            return {
                "total_tokens": total_tokens,
                "active_items": storage_stats.get("active_items", 0),
                "compressed_items": storage_stats.get("compressed_items", 0),
                "vector_count": vector_stats.get("vector_count", 0),
                "index_size": vector_stats.get("index_size", 0)
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {
                "total_tokens": 0,
                "active_items": 0,
                "compressed_items": 0,
                "vector_count": 0,
                "index_size": 0
            }

    # New methods for the generic memory abstraction
    async def create_memory_item(
        self,
        content: str,
        item_type: str,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Create a new memory item using the generic memory manager.
        This method allows for creating memory items outside of chat contexts.
        """
        # Convert string item_type to MemoryType enum
        try:
            memory_type = MemoryType(item_type)
        except ValueError:
            memory_type = MemoryType.CUSTOM
            if metadata is None:
                metadata = {}
            metadata["custom_type"] = item_type
        
        return await self.memory_manager.create_item(
            content=content,
            item_type=memory_type,
            parent_id=parent_id,
            metadata=metadata,
            tags=tags
        )

    async def search_memory(
        self,
        query: str,
        scope: str = "global",
        item_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ):
        """
        Search memory using the generic memory manager.
        This method provides a more flexible search interface than the chat-specific search_context.
        """
        # Convert string scope to MemoryScope enum
        try:
            memory_scope = MemoryScope(scope)
        except ValueError:
            memory_scope = MemoryScope.GLOBAL
        
        # Convert string item_types to MemoryType enums
        memory_types = None
        if item_types:
            memory_types = []
            for item_type in item_types:
                try:
                    memory_types.append(MemoryType(item_type))
                except ValueError:
                    # Skip invalid types
                    pass
        
        return await self.memory_manager.search(
            query=query,
            scope=memory_scope,
            item_types=memory_types,
            tags=tags,
            limit=limit
        )

    async def get_item_context(
        self,
        item_id: str,
        depth: int = 3,
        include_siblings: bool = False
    ):
        """
        Get contextual items related to a specific item.
        Useful for understanding the context around a piece of information.
        """
        return await self.memory_manager.get_context(
            item_id=item_id,
            depth=depth,
            include_siblings=include_siblings
        )

    async def optimize_memory_context(
        self,
        item_ids: List[str],
        max_tokens: int
    ):
        """
        Optimize a list of memory items to fit within token limits.
        Useful for preparing context for LLM interactions.
        """
        # Retrieve items by IDs
        items = []
        for item_id in item_ids:
            item = await self.memory_store.retrieve(item_id)
            if item:
                items.append(item)
        
        return await self.memory_manager.optimize_context(
            items=items,
            max_tokens=max_tokens
        )

# Example usage demonstrating the system's capabilities
async def main():
    logger.info("Starting MemorgSystem application")
    try:
        # Initialize storage with SQLite
        storage = SQLiteStorageAdapter("memorg.db")
        logger.info("Storage adapter initialized")

        # Initialize the complete system
        client = AsyncOpenAI(api_key="your-api-key")
        system = MemorgSystem(
            storage=SQLiteStorageAdapter("memorg.db"),
            vector_store=USearchVectorStore("memorg.db"),
            openai_client=client
        )
        logger.info("MemorgSystem initialized")
        
        # Demonstrate session creation
        session = await system.create_session("user123", {"max_tokens": 4096})
        logger.info("Created session: %s", session.id)
        
        # Demonstrate conversation creation
        conversation = await system.start_conversation(session.id)
        logger.info("Started conversation: %s", conversation.id)
        
        # Demonstrate topic creation
        topic = await system.context_store.create_topic(conversation.id, "Initial Discussion")
        logger.info("Created topic: %s", topic.id)
        
        # Demonstrate adding an exchange
        exchange = await system.add_exchange(
            topic.id,
            "Hello, how can you help me?",
            "I'm here to assist you with any questions or tasks you have."
        )
        logger.info("Added exchange: %s", exchange.id)
        
        # Demonstrate context search
        results = await system.search_context("help")
        logger.info("Search results count: %d", len(results))

        # Demonstrate memory usage tracking
        memory_usage = await system.get_memory_usage()
        logger.info("Memory usage: %s", memory_usage)
        
        # Demonstrate new generic memory capabilities
        logger.info("Demonstrating new generic memory capabilities")
        
        # Create a custom memory item
        document_item = await system.create_memory_item(
            content="This is a research document about AI advancements.",
            item_type="document",
            parent_id=topic.id,
            metadata={"author": "Research Team", "category": "AI"},
            tags=["research", "AI", "document"]
        )
        logger.info("Created document item: %s", document_item.id)
        
        # Search using the new memory system
        memory_results = await system.search_memory(
            query="AI research",
            item_types=["document"],
            tags=["research"],
            limit=5
        )
        logger.info("Memory search results count: %d", len(memory_results))
        
        logger.info("Application completed successfully")
    except Exception as e:
        logger.error("Application failed: %s", str(e), exc_info=True)
        raise

# Entry point for the application
if __name__ == "__main__":
    asyncio.run(main())
