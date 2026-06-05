# Memory Abstraction

The Memory Abstraction layer provides a generic interface for using Memorg's memory capabilities across workflows beyond chat — document analysis, research notebooks, knowledge management, and custom applications.

Internally, it uses the same `StorageAdapter` and `VectorStore` as the chat hierarchy, so a single Memorg database holds both worlds side by side.

## Overview

Originally designed for chat-based interactions, Memorg has grown a generic abstraction that supports:

- Document analysis
- Research workflows
- Content creation
- Knowledge management
- Custom applications with arbitrary `item_type`

## Core Concepts

### Memory Types

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

When you pass an `item_type` string to `MemorgSystem.create_memory_item`, it is matched against `MemoryType` values. Unknown strings are stored as `MemoryType.CUSTOM` with the original label preserved at `metadata["custom_type"]`. So `item_type="note"` becomes `MemoryType.CUSTOM` with `metadata["custom_type"] = "note"`.

### Memory Scopes

```python
class MemoryScope(Enum):
    GLOBAL = "global"
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    CUSTOM = "custom"
```

Unknown scope strings fall back to `GLOBAL` in `MemorgSystem.search_memory`.

### Memory Item

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
    tags: List[str] = None        # defaults to [] via __post_init__
```

### Memory Query

```python
@dataclass
class MemoryQuery:
    text: str
    scope: MemoryScope
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    include_metadata: bool = True
```

### Search Result

```python
@dataclass
class SearchResult:
    item: MemoryItem
    score: float
    match_type: str
```

Note that this is a different `SearchResult` from `memorg.models.SearchResult` used by the chat hierarchy.

## Key Components

### `HierarchicalMemoryStore`

Bridges the generic memory interface (`MemoryStore` protocol) with the existing storage and vector layers.

```python
from memorg.memory.store import HierarchicalMemoryStore

store = HierarchicalMemoryStore(storage, vector_store, openai_client)

await store.store(memory_item)
item = await store.retrieve(item_id)
results = await store.search(memory_query)
children = await store.get_children(parent_id, item_type=MemoryType.DOCUMENT)
parent = await store.get_parent(item_id)
```

### `GenericMemoryManager`

High-level CRUD and search.

```python
from memorg.memory.manager import GenericMemoryManager

manager = GenericMemoryManager(store, openai_client)

item = await manager.create_item(
    content="Research findings...",
    item_type=MemoryType.DOCUMENT,
    tags=["research", "analysis"],
)

results = await manager.search(
    query="findings",
    scope=MemoryScope.GLOBAL,
    item_types=[MemoryType.DOCUMENT],
    tags=["research"],
)

context = await manager.get_context(item.id, depth=3, include_siblings=True)
optimized = await manager.optimize_context(items, max_tokens=4000)
```

In practice, you usually access these through `MemorgSystem.create_memory_item`, `search_memory`, `get_item_context`, and `optimize_memory_context`.

## Usage Examples

### Document Analysis Workflow

```python
async def analyze_documents(documents):
    system = MemorgSystem(storage, vector_store, client)

    session = await system.create_session("analyst", {
        "workflow": "document_analysis",
    })

    for doc in documents:
        await system.create_memory_item(
            content=doc.content,
            item_type="document",
            parent_id=session.id,
            metadata={"source": doc.source},
            tags=doc.tags,
        )

    return await system.search_memory(
        query="key findings",
        item_types=["document"],
        tags=["analysis"],
    )
```

### Research Workflow

```python
async def research_workflow():
    system = MemorgSystem(storage, vector_store, client)

    session = await system.create_session("researcher", {})

    topic = await system.create_memory_item(
        content="AI Ethics Research",
        item_type="topic",
        parent_id=session.id,
        tags=["ai", "ethics", "research"],
    )

    await system.create_memory_item(
        content="Key insight: transparency is crucial",
        item_type="note",
        parent_id=topic.id,
        tags=["insight", "transparency"],
    )

    return await system.search_memory(
        query="transparency AI",
        scope="global",
    )
```

### Token-Bounded Context Pack

```python
item_ids = [doc.id, summary.id, note.id]
optimized = await system.optimize_memory_context(item_ids, max_tokens=4000)
```

`optimize_memory_context` retrieves each item by id, silently skips missing ones, and passes the survivors to `GenericMemoryManager.optimize_context`.

## Benefits

1. **Generic items** — store any kind of information, not just conversation turns.
2. **Flexible scopes** — target operations to specific contexts.
3. **Tag-based organisation** — filter by `tags` alongside text and `item_types`.
4. **Rich metadata** — attach arbitrary JSON-serialisable metadata to items.
5. **Shared storage** — coexists with chat data in the same SQLite + USearch backing files.

## Best Practices

### Consistent Tagging

Use a consistent, lowercase, hyphenated tag vocabulary:

```python
# Good
tags=["project-alpha", "research", "2024"]

# Avoid
tags=["Project Alpha", "Research!", "2024"]
```

### Hierarchical Organisation

Leverage parent/child relationships to scope retrieval:

```python
session  = await system.create_memory_item(item_type="session", ...)
project  = await system.create_memory_item(parent_id=session.id, ...)
document = await system.create_memory_item(parent_id=project.id, ...)
note     = await system.create_memory_item(parent_id=document.id, ...)
```

### Scope-Based Search

```python
await system.search_memory(query, scope="global")
await system.search_memory(query, scope="session")
```

`global` searches all stored memory items; narrower scopes restrict to the indicated subtree.

### Mixing Chat and Memory

You can attach memory items to chat-level entities. The CLI's `addnote` command does exactly this: it passes the active `session_id` as `parent_id` for the new `note` item. The same pattern works for hooking documents to a topic, or notes to an exchange.
