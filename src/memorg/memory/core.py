from typing import List, Dict, Any, Optional, Protocol, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

class MemoryType(Enum):
    """Types of memory items that can be stored."""
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    EXCHANGE = "exchange"
    DOCUMENT = "document"
    ENTITY = "entity"
    CUSTOM = "custom"

class MemoryScope(Enum):
    """Scopes for memory operations."""
    GLOBAL = "global"
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    CUSTOM = "custom"

@dataclass
class MemoryItem:
    """Generic memory item that can represent any type of stored information."""
    id: str
    type: MemoryType
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    embedding: Optional[List[float]] = None
    importance_score: float = 0.0
    parent_id: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class SearchResult:
    """Result from a memory search operation."""
    item: MemoryItem
    score: float
    match_type: str

@dataclass
class MemoryQuery:
    """Structured query for memory search operations."""
    text: str
    scope: MemoryScope
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    include_metadata: bool = True

class MemoryStore(Protocol):
    """Protocol defining the interface for memory storage operations."""
    
    async def store(self, item: MemoryItem) -> str:
        """Store a memory item and return its ID."""
        ...
    
    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item by ID."""
        ...
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory item with new data."""
        ...
    
    async def delete(self, item_id: str) -> bool:
        """Delete a memory item."""
        ...
    
    async def search(self, query: MemoryQuery) -> List[SearchResult]:
        """Search for memory items based on a query."""
        ...
    
    async def get_children(self, parent_id: str, item_type: Optional[MemoryType] = None) -> List[MemoryItem]:
        """Get child items of a parent item."""
        ...
    
    async def get_parent(self, item_id: str) -> Optional[MemoryItem]:
        """Get the parent of an item."""
        ...

class MemoryManager(Protocol):
    """Protocol defining the interface for memory management operations."""
    
    async def create_item(
        self,
        content: str,
        item_type: MemoryType,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> MemoryItem:
        """Create a new memory item."""
        ...
    
    async def update_importance(self, item_id: str, importance_score: float) -> bool:
        """Update the importance score of a memory item."""
        ...
    
    async def add_tags(self, item_id: str, tags: List[str]) -> bool:
        """Add tags to a memory item."""
        ...
    
    async def remove_tags(self, item_id: str, tags: List[str]) -> bool:
        """Remove tags from a memory item."""
        ...
    
    async def search(
        self,
        query: str,
        scope: MemoryScope = MemoryScope.GLOBAL,
        item_types: Optional[List[MemoryType]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Search memory for relevant items."""
        ...
    
    async def get_context(
        self,
        item_id: str,
        depth: int = 3,
        include_siblings: bool = False
    ) -> List[MemoryItem]:
        """Get contextual items related to a specific item."""
        ...
    
    async def optimize_context(
        self,
        items: List[MemoryItem],
        max_tokens: int
    ) -> List[MemoryItem]:
        """Optimize a list of memory items to fit within token limits."""
        ...