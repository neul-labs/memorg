# Library Usage Guide

How to integrate Memorg into your Python applications.

## Basic Setup

```python
import asyncio
from memorg import MemorgSystem
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore
from openai import AsyncOpenAI

async def setup():
    # Initialize components
    storage = SQLiteStorageAdapter("memorg.db")
    vector_store = USearchVectorStore("memorg.db")
    client = AsyncOpenAI()

    # Create the system
    system = MemorgSystem(storage, vector_store, client)
    return system
```

## Session Management

Sessions are top-level containers for user interactions:

```python
# Create a session
session = await system.create_session("user123", {
    "max_tokens": 4096,
    "preferences": {"language": "en"}
})

print(f"Session ID: {session.id}")
print(f"Created at: {session.created_at}")
```

## Conversation Flow

### Starting Conversations

```python
# Start a new conversation
conversation = await system.start_conversation(session.id)

# Create a topic within the conversation
topic = await system.context_store.create_topic(
    conversation.id,
    "Project Planning"
)
```

### Adding Exchanges

```python
# Add a user-system exchange
exchange = await system.add_exchange(
    topic.id,
    user_message="What features should we prioritize?",
    system_message="Based on user feedback, I recommend focusing on..."
)

print(f"Exchange importance: {exchange.importance_score}")
```

## Search Operations

### Context Search

Search within conversation context:

```python
from memorg.models import SearchScope

# Search all context
results = await system.search_context(
    query="prioritize features",
    scope=SearchScope.ALL,
    max_results=10
)

for result in results:
    print(f"Score: {result.score:.2f}")
    print(f"Type: {result.match_type}")
    print(f"Content: {result.entity}")
```

### Memory Search

Search across all memory items:

```python
results = await system.search_memory(
    query="project planning",
    scope="global",
    item_types=["document", "note"],
    tags=["project"],
    limit=5
)

for result in results:
    print(f"{result.score:.2f}: {result.item.content}")
```

## Memory Abstraction

Use Memorg for non-chat workflows:

### Creating Memory Items

```python
from memorg.memory.core import MemoryType

# Create a document
doc = await system.create_memory_item(
    content="Research findings on user behavior...",
    item_type="document",
    parent_id=session.id,
    metadata={
        "source": "user_study_2024.pdf",
        "author": "Research Team"
    },
    tags=["research", "user-behavior", "2024"]
)

# Create a custom item type
note = await system.create_memory_item(
    content="Key insight: Users prefer simple interfaces",
    item_type="note",
    parent_id=doc.id,
    tags=["insight", "ux"]
)
```

### Getting Context

```python
# Get contextual items around a specific item
context = await system.get_item_context(
    item_id=doc.id,
    depth=3,
    include_siblings=True
)

for item in context:
    print(f"{item.type}: {item.content[:50]}...")
```

### Optimizing for LLM Context

```python
# Prepare items for LLM context window
item_ids = [doc.id, note.id, ...]
optimized = await system.optimize_memory_context(
    item_ids=item_ids,
    max_tokens=4000
)
```

## Context Optimization

### Manual Optimization

```python
from memorg.models import Entity, EntityType

# Define important entities
entities = [
    Entity(name="Project Alpha", type=EntityType.PROJECT, salience=0.9),
    Entity(name="Q1 Deadline", type=EntityType.DATE, salience=0.8)
]

# Optimize context
optimized = await system.optimize_context(
    content="Long content to optimize...",
    entities=entities,
    max_tokens=2000
)

print(f"Optimized content: {optimized}")
```

## Memory Usage Tracking

```python
usage = await system.get_memory_usage()

print(f"Total tokens: {usage['total_tokens']:,}")
print(f"Active items: {usage['active_items']}")
print(f"Compressed items: {usage['compressed_items']}")
print(f"Vector count: {usage['vector_count']}")
print(f"Index size: {usage['index_size'] / 1024:.2f} KB")
```

## Error Handling

```python
try:
    session = await system.create_session("user", {})
except Exception as e:
    logger.error(f"Failed to create session: {e}")
    raise
```

## Best Practices

1. **Reuse sessions** for related interactions
2. **Use topics** to organize conversations by subject
3. **Tag memory items** consistently for better search
4. **Monitor memory usage** to avoid performance issues
5. **Optimize context** before sending to LLMs
