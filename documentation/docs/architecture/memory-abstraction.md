# Memory Abstraction

The Memory Abstraction layer provides a generic interface for using Memorg's memory capabilities across different workflows beyond chat conversations.

## Overview

Originally designed for chat-based interactions, Memorg has evolved to support a wide range of workflows:

- Document analysis
- Research workflows
- Content creation
- Knowledge management
- Custom applications

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

### Memory Scopes

```python
class MemoryScope(Enum):
    GLOBAL = "global"
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    CUSTOM = "custom"
```

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
    parent_id: Optional[str]
    embedding: Optional[List[float]]
    tags: List[str]
```

## Key Components

### HierarchicalMemoryStore

Bridges the generic memory interface with the existing hierarchical storage system.

```python
from memorg.memory.store import HierarchicalMemoryStore

store = HierarchicalMemoryStore(storage, vector_store, openai_client)

# Store an item
item_id = await store.store(memory_item)

# Retrieve an item
item = await store.retrieve(item_id)

# Search items
results = await store.search(query)
```

### GenericMemoryManager

High-level interface for memory operations.

```python
from memorg.memory.manager import GenericMemoryManager

manager = GenericMemoryManager(store, openai_client)

# Create items
item = await manager.create_item(
    content="Research findings...",
    item_type=MemoryType.DOCUMENT,
    tags=["research", "analysis"]
)

# Search with filters
results = await manager.search(
    query="findings",
    scope=MemoryScope.GLOBAL,
    item_types=[MemoryType.DOCUMENT],
    tags=["research"]
)

# Get context
context = await manager.get_context(item.id, depth=3)

# Optimize for LLM
optimized = await manager.optimize_context(items, max_tokens=4000)
```

## Usage Examples

### Document Analysis Workflow

```python
async def analyze_documents():
    system = MemorgSystem(storage, vector_store, client)

    # Create a session for the workflow
    session = await system.create_session("analyst", {
        "workflow": "document_analysis"
    })

    # Add documents
    for doc in documents:
        await system.create_memory_item(
            content=doc.content,
            item_type="document",
            parent_id=session.id,
            metadata={"source": doc.source},
            tags=doc.tags
        )

    # Search across documents
    results = await system.search_memory(
        query="key findings",
        item_types=["document"],
        tags=["analysis"]
    )

    return results
```

### Research Workflow

```python
async def research_workflow():
    system = MemorgSystem(storage, vector_store, client)

    # Create research session
    session = await system.create_session("researcher", {})

    # Create topic
    topic = await system.create_memory_item(
        content="AI Ethics Research",
        item_type="topic",
        parent_id=session.id,
        tags=["ai", "ethics", "research"]
    )

    # Add notes
    await system.create_memory_item(
        content="Key insight: transparency is crucial",
        item_type="note",
        parent_id=topic.id,
        tags=["insight", "transparency"]
    )

    # Search related work
    results = await system.search_memory(
        query="transparency AI",
        scope="global"
    )
```

## Benefits

1. **Generic Memory Items** - Store any type of information, not just conversations
2. **Flexible Scopes** - Target operations to specific contexts
3. **Tag-Based Organization** - Organize and filter using custom tags
4. **Rich Metadata** - Attach arbitrary metadata to items
5. **Backward Compatibility** - Works alongside existing chat functionality

## Best Practices

### Consistent Tagging

Use a consistent tagging scheme:

```python
# Good
tags=["project-alpha", "research", "2024"]

# Avoid
tags=["Project Alpha", "Research!", "2024"]
```

### Hierarchical Organization

Leverage parent-child relationships:

```python
# Session -> Project -> Document -> Note
session = await create_memory_item(type="session", ...)
project = await create_memory_item(parent_id=session.id, ...)
document = await create_memory_item(parent_id=project.id, ...)
note = await create_memory_item(parent_id=document.id, ...)
```

### Scope-Based Search

Use appropriate scopes:

```python
# Global search
await search_memory(query, scope="global")

# Session-specific search
await search_memory(query, scope="session")
```
