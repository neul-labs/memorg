# API Reference

This page documents the public Python surface of Memorg. Type hints and field names match the source in `src/memorg/`.

## Top-Level Imports

Re-exported from `memorg/__init__.py`:

```python
from memorg import (
    MemorgSystem,
    Session, Conversation, Topic, Exchange, Entity,
    ContextStore, ContextManager,
    RetrievalSystem, ContextWindowOptimizer,
)
```

`memorg.__version__` is also exposed.

## `MemorgSystem`

The orchestrator that wires the four cooperating components plus the generic memory layer.

```python
from memorg import MemorgSystem

system = MemorgSystem(storage, vector_store, openai_client)
```

**Constructor**

| Parameter | Type | Notes |
|-----------|------|-------|
| `storage` | `StorageAdapter` | typically `SQLiteStorageAdapter` |
| `vector_store` | `VectorStore` | typically `USearchVectorStore` |
| `openai_client` | `openai.AsyncOpenAI` | used for embeddings and chat |

**Methods**

| Method | Returns |
|--------|---------|
| `create_session(user_id: str, config: Dict[str, Any])` | `Session` |
| `start_conversation(session_id: str)` | `Conversation` |
| `add_exchange(topic_id: str, user_message: str, system_message: str)` | `Exchange` |
| `search_context(query: str, scope: SearchScope = SearchScope.ALL, max_results: int = 10)` | `list[SearchResult]` |
| `optimize_context(content: str, entities: list[Entity], max_tokens: int)` | `str` (prompt template) |
| `get_memory_usage()` | `Dict[str, int]` |
| `create_memory_item(content, item_type, parent_id=None, metadata=None, tags=None)` | `MemoryItem` |
| `search_memory(query, scope="global", item_types=None, tags=None, limit=10)` | `list[SearchResult]` (memory) |
| `get_item_context(item_id, depth=3, include_siblings=False)` | `list[MemoryItem]` |
| `optimize_memory_context(item_ids, max_tokens)` | `list[MemoryItem]` |

All methods are coroutines.

### Component Attributes

`MemorgSystem` exposes the components it constructs so applications can call them directly:

| Attribute | Type |
|-----------|------|
| `context_store` | `ContextStore` |
| `context_manager` | `ContextManager` |
| `retrieval_system` | `RetrievalSystem` |
| `window_optimizer` | `ContextWindowOptimizer` |
| `memory_store` | `HierarchicalMemoryStore` |
| `memory_manager` | `GenericMemoryManager` |
| `openai_client` | `openai.AsyncOpenAI` |

`MemorgSystem.context_store.create_topic(conversation_id, title)` is the canonical way to create a topic, since `MemorgSystem` does not wrap it.

## Models

Located in `memorg.models`.

### `Session`

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

### `Conversation`

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

### `Topic`

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

### `Exchange`

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

### `Message` and `ParsedContent`

```python
@dataclass
class Message:
    raw_content: str
    parsed_content: ParsedContent
    embedding: List[float]

@dataclass
class ParsedContent:
    entities: List[Entity]
    intents: List[str]
    sentiment: Dict[str, float]
```

### `Entity`

```python
@dataclass
class Entity:
    name: str
    type: EntityType
    salience: float
    metadata: Dict[str, Any]
```

### `SearchResult`

```python
@dataclass
class SearchResult:
    entity: Any   # Session | Conversation | Topic | Exchange (or a dict, depending on source)
    score: float
    match_type: MatchType
```

## Enums

### `EntityType`

```python
class EntityType(Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    EVENT = "event"
    OTHER = "other"
```

### `SearchScope`

```python
class SearchScope(Enum):
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    ALL = "all"
```

### `MatchType`

```python
class MatchType(Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    HYBRID = "hybrid"
    IMPORTANCE = "importance"
```

## Memory Abstraction

Located under `memorg.memory`.

### `MemoryItem`

```python
@dataclass
class MemoryItem:
    id: str
    type: MemoryType
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    embedding: Optional[List[float]] = None
    importance_score: float = 0.0
    parent_id: Optional[str] = None
    tags: List[str] = None       # __post_init__ defaults to []
```

### `MemoryType`

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

### `MemoryScope`

```python
class MemoryScope(Enum):
    GLOBAL = "global"
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    CUSTOM = "custom"
```

### `MemoryQuery`

```python
@dataclass
class MemoryQuery:
    text: str
    scope: MemoryScope
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    include_metadata: bool = True
```

### `MemoryStore` and `MemoryManager`

`memorg.memory.core` defines two `Protocol`s for the storage and manager interfaces. The concrete implementations are:

- `memorg.memory.store.HierarchicalMemoryStore` — bridges memory items to the existing `StorageAdapter` and `VectorStore`.
- `memorg.memory.manager.GenericMemoryManager` — high-level CRUD, search, and context operations.

## Storage Layer

```python
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.storage.storage_adapter import StorageAdapter

from memorg.vector_store.usearch_vector_store import USearchVectorStore
from memorg.vector_store.vector_store import VectorStore
```

- `SQLiteStorageAdapter(db_path="memorg.db")` — creates tables and FTS5 mirrors for `sessions`, `conversations`, `topics`, `exchanges`.
- `USearchVectorStore(db_path="memorg.db", vector_dim=1536)` — `cos` metric, `f32` vectors, persisted to `<basename>.usearch` alongside the SQLite file.

Both implement their respective `Protocol` so you can substitute custom backends.

## MCP Server

```python
from memorg.mcp.server import MemorgMCP

server = MemorgMCP(db_path="memorg.db")
server.run(host="127.0.0.1", port=3000)
```

The CLI entry point is `memorg.mcp.cli:main`, invoked as `memorg-mcp`.

## CLI Reference

See [CLI Reference](cli.md) for `memorg` and `memorg-mcp` command-line usage.
