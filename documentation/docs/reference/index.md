# API Reference

This section provides detailed API documentation for Memorg.

## Core Classes

### MemorgSystem

The main orchestrator class that integrates all components.

```python
from memorg import MemorgSystem

system = MemorgSystem(storage, vector_store, openai_client)
```

**Key Methods:**

- `create_session(user_id, config)` - Create a new session
- `start_conversation(session_id)` - Start a conversation
- `add_exchange(topic_id, user_msg, system_msg)` - Add an exchange
- `search_context(query, scope, max_results)` - Search context
- `search_memory(query, scope, item_types, tags)` - Search memory
- `create_memory_item(content, item_type, ...)` - Create memory item
- `get_memory_usage()` - Get usage statistics
- `optimize_context(content, entities, max_tokens)` - Optimize context

### Models

```python
from memorg.models import (
    Session,
    Conversation,
    Topic,
    Exchange,
    Entity,
    SearchResult
)
```

### Storage

```python
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore
```

### Memory Abstraction

```python
from memorg.memory.core import MemoryItem, MemoryType, MemoryScope
from memorg.memory.store import HierarchicalMemoryStore
from memorg.memory.manager import GenericMemoryManager
```

## Data Models

### Session

```python
@dataclass
class Session:
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    system_config: Dict[str, Any]
    conversations: List[Conversation]
    metadata: Dict[str, Any]
```

### Conversation

```python
@dataclass
class Conversation:
    id: str
    created_at: datetime
    updated_at: datetime
    title: str
    summary: str
    topics: List[Topic]
    embedding: List[float]
    metadata: Dict[str, Any]
```

### Topic

```python
@dataclass
class Topic:
    id: str
    created_at: datetime
    updated_at: datetime
    title: str
    summary: str
    exchanges: List[Exchange]
    embedding: List[float]
    key_entities: List[Entity]
    metadata: Dict[str, Any]
```

### Exchange

```python
@dataclass
class Exchange:
    id: str
    created_at: datetime
    updated_at: datetime
    user_message: Message
    system_message: Message
    importance_score: float
    embedding: List[float]
    metadata: Dict[str, Any]
```

### MemoryItem

```python
@dataclass
class MemoryItem:
    id: str
    type: MemoryType
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    parent_id: Optional[str]
    embedding: Optional[List[float]]
    tags: List[str]
```

## Enums

### MemoryType

```python
class MemoryType(Enum):
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    EXCHANGE = "exchange"
    DOCUMENT = "document"
    ENTITY = "entity"
    CUSTOM = "custom"
```

### MemoryScope

```python
class MemoryScope(Enum):
    GLOBAL = "global"
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    CUSTOM = "custom"
```

### SearchScope

```python
class SearchScope(Enum):
    ALL = "all"
    SESSIONS = "sessions"
    CONVERSATIONS = "conversations"
    TOPICS = "topics"
    EXCHANGES = "exchanges"
```

## CLI Reference

See [CLI Reference](cli.md) for command-line documentation.
