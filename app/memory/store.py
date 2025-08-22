from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from openai import AsyncOpenAI

from app.memory.core import MemoryItem, MemoryType, MemoryScope, SearchResult, MemoryQuery, MemoryStore
from app.storage.storage_adapter import StorageAdapter
from app.vector_store.vector_store import VectorStore
from app.models import Session, Conversation, Topic, Exchange, Message, ParsedContent, Entity, EntityType

class HierarchicalMemoryStore(MemoryStore):
    """Implementation of MemoryStore using the existing hierarchical storage system."""
    
    def __init__(self, storage: StorageAdapter, vector_store: VectorStore, openai_client: AsyncOpenAI):
        self.storage = storage
        self.vector_store = vector_store
        self.openai_client = openai_client
    
    async def store(self, item: MemoryItem) -> str:
        """Store a memory item in the appropriate collection."""
        # Convert MemoryItem to the appropriate model based on type
        if item.type == MemoryType.SESSION:
            session = Session(
                id=item.id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                user_id=item.metadata.get("user_id", ""),
                system_config=item.metadata.get("config", {}),
                conversations=[],
                metadata=item.metadata
            )
            await self.storage.write("sessions", item.id, session.__dict__)
        elif item.type == MemoryType.CONVERSATION:
            conversation = Conversation(
                id=item.id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                title=item.metadata.get("title", ""),
                summary=item.metadata.get("summary", ""),
                topics=[],
                embedding=item.embedding or [],
                metadata=item.metadata
            )
            await self.storage.write("conversations", item.id, conversation.__dict__)
        elif item.type == MemoryType.TOPIC:
            topic = Topic(
                id=item.id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                title=item.metadata.get("title", ""),
                summary=item.metadata.get("summary", ""),
                exchanges=[],
                embedding=item.embedding or [],
                key_entities=[],
                metadata=item.metadata
            )
            await self.storage.write("topics", item.id, topic.__dict__)
        elif item.type == MemoryType.EXCHANGE:
            # For exchanges, we need to create Message objects
            user_msg = Message(
                raw_content=item.content,
                parsed_content=ParsedContent(entities=[], intents=[], sentiment=None),
                embedding=item.embedding or []
            )
            system_msg = Message(
                raw_content="",
                parsed_content=ParsedContent(entities=[], intents=[], sentiment=None),
                embedding=item.embedding or []
            )
            exchange = Exchange(
                id=item.id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                user_message=user_msg,
                system_message=system_msg,
                importance_score=item.importance_score,
                embedding=item.embedding or [],
                metadata=item.metadata
            )
            await self.storage.write("exchanges", item.id, exchange.__dict__)
            
            # Add to vector store if we have an embedding
            if item.embedding:
                await self.vector_store.add_vector(
                    item.id,
                    item.embedding,
                    metadata={
                        "text_content": item.content,
                        "type": "exchange",
                        "parent_id": item.parent_id
                    }
                )
        else:
            # For custom types, store in a generic collection
            await self.storage.write("custom_memory", item.id, {
                "id": item.id,
                "type": item.type.value,
                "content": item.content,
                "metadata": item.metadata,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "embedding": item.embedding,
                "importance_score": item.importance_score,
                "parent_id": item.parent_id,
                "tags": item.tags
            })
        
        # Update parent relationship if needed
        if item.parent_id:
            await self._update_parent_relationship(item.parent_id, item.id, item.type)
        
        return item.id
    
    async def _update_parent_relationship(self, parent_id: str, child_id: str, child_type: MemoryType):
        """Update the parent item to include the new child."""
        # This would need to be implemented based on the specific parent type
        # For now, we'll leave it as a placeholder
        pass
    
    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item by ID."""
        # Try to find the item in each collection
        for collection in ["sessions", "conversations", "topics", "exchanges", "custom_memory"]:
            data = await self.storage.read(collection, item_id)
            if data:
                return self._convert_to_memory_item(data, collection)
        return None
    
    def _convert_to_memory_item(self, data: Dict[str, Any], collection: str) -> MemoryItem:
        """Convert stored data to a MemoryItem."""
        # Handle datetime conversion
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        
        # Create MemoryItem based on collection type
        item_type = MemoryType(collection.rstrip('s')) if collection in ["sessions", "conversations", "topics", "exchanges"] else MemoryType(data.get("type", "custom"))
        
        return MemoryItem(
            id=data["id"],
            type=item_type,
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
            embedding=data.get("embedding"),
            importance_score=data.get("importance_score", 0.0),
            parent_id=data.get("parent_id"),
            tags=data.get("tags", [])
        )
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory item with new data."""
        item = await self.retrieve(item_id)
        if not item:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)
            elif key in item.metadata:
                item.metadata[key] = value
            else:
                item.metadata[key] = value
        
        # Update the stored item
        item.updated_at = datetime.utcnow()
        return await self.store(item) is not None
    
    async def delete(self, item_id: str) -> bool:
        """Delete a memory item."""
        # Try to delete from each collection
        for collection in ["sessions", "conversations", "topics", "exchanges", "custom_memory"]:
            try:
                await self.storage.delete(collection, item_id)
                return True
            except:
                continue
        return False
    
    async def search(self, query: MemoryQuery) -> List[SearchResult]:
        """Search for memory items based on a query."""
        results = []
        
        # If we have an embedding, do semantic search
        if query.text and self.openai_client:
            try:
                embedding_response = await self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=query.text
                )
                embedding = embedding_response.data[0].embedding
                
                # Search in vector store
                vector_results = await self.vector_store.search_nearest(embedding, query.limit)
                
                for result in vector_results:
                    item_id = result["id"]
                    item = await self.retrieve(item_id)
                    if item:
                        results.append(SearchResult(
                            item=item,
                            score=result["score"],
                            match_type="semantic"
                        ))
            except Exception as e:
                # Fallback to keyword search if semantic search fails
                pass
        
        # If we don't have enough results or semantic search failed, do keyword search
        if len(results) < query.limit:
            # Search in each collection
            for collection in ["sessions", "conversations", "topics", "exchanges", "custom_memory"]:
                try:
                    items = await self.storage.query(collection, {"$text": {"$search": query.text}})
                    for item_data in items:
                        item = self._convert_to_memory_item(item_data, collection)
                        # Check if this item matches our filters
                        if self._matches_filters(item, query.filters):
                            results.append(SearchResult(
                                item=item,
                                score=0.5,  # Default score for keyword matches
                                match_type="keyword"
                            ))
                except:
                    continue
        
        # Sort by score and limit results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:query.limit]
    
    def _matches_filters(self, item: MemoryItem, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if a memory item matches the given filters."""
        if not filters:
            return True
        
        for key, value in filters.items():
            if key in item.metadata:
                if item.metadata[key] != value:
                    return False
            elif hasattr(item, key):
                if getattr(item, key) != value:
                    return False
            else:
                return False
        return True
    
    async def get_children(self, parent_id: str, item_type: Optional[MemoryType] = None) -> List[MemoryItem]:
        """Get child items of a parent item."""
        # This would need to be implemented based on how parent-child relationships are stored
        # For now, we'll return an empty list
        return []
    
    async def get_parent(self, item_id: str) -> Optional[MemoryItem]:
        """Get the parent of an item."""
        item = await self.retrieve(item_id)
        if item and item.parent_id:
            return await self.retrieve(item.parent_id)
        return None