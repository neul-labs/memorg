# Library Usage Guide

How to integrate Memorg into your own Python application or agent loop.

Memorg is async-first — all public methods on `MemorgSystem` are coroutines. The recommended entry point is `MemorgSystem`, which composes `ContextStore`, `ContextManager`, `RetrievalSystem`, `ContextWindowOptimizer`, and the generic memory layer.

## Basic Setup

```python
import asyncio
from openai import AsyncOpenAI
from memorg import MemorgSystem
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore


async def build_system() -> MemorgSystem:
    return MemorgSystem(
        storage=SQLiteStorageAdapter("memorg.db"),
        vector_store=USearchVectorStore("memorg.db"),
        openai_client=AsyncOpenAI(),  # picks up OPENAI_API_KEY from env
    )
```

`SQLiteStorageAdapter` initializes four tables (`sessions`, `conversations`, `topics`, `exchanges`) plus FTS5 mirrors and update triggers on first construction. `USearchVectorStore` creates or restores `memorg.usearch` next to the SQLite file.

## Sessions, Conversations, Topics, Exchanges

The hierarchy is `Session > Conversation > Topic > Exchange`. Each level has a UUID, timestamps, an embedding (where applicable), and a `metadata` dict.

```python
session = await system.create_session("user123", {
    "max_tokens": 4096,
    "preferences": {"language": "en"},
})

conversation = await system.start_conversation(session.id)

topic = await system.context_store.create_topic(
    conversation.id,
    "Project Planning",
)

exchange = await system.add_exchange(
    topic.id,
    user_message="What features should we prioritize?",
    system_message="Based on user feedback, I recommend focusing on...",
)

print(exchange.importance_score)  # set by ContextManager.update_importance
```

Note: there is no convenience method for `create_topic` on `MemorgSystem` itself — go through `system.context_store.create_topic(conversation_id, title)`.

`add_exchange` writes the exchange via `ContextStore`, then updates `importance_score` using `ContextManager.update_importance(exchange, {"current_topic": topic})`.

## Searching Context

`search_context` runs a hybrid pipeline: semantic search via USearch nearest-neighbour over the OpenAI embedding of the query, followed by FTS5 keyword fallback if not enough results, then ranking with `MultiFactorScorer`.

```python
from memorg.models import SearchScope

results = await system.search_context(
    query="prioritize features",
    scope=SearchScope.ALL,
    max_results=10,
)

for result in results:
    print(result.score, result.match_type.value, result.entity)
```

`SearchScope` values are `SESSION`, `CONVERSATION`, `TOPIC`, and `ALL`. The default in `MemorgSystem.search_context` is `SearchScope.ALL`. `MatchType` values returned in results are `KEYWORD`, `SEMANTIC`, `TEMPORAL`, `HYBRID`, and `IMPORTANCE`.

## Generic Memory Items

Beyond chat, Memorg supports arbitrary memory items via `HierarchicalMemoryStore` and `GenericMemoryManager`. The high-level methods on `MemorgSystem` are:

```python
# Create
doc = await system.create_memory_item(
    content="Research findings on user behavior...",
    item_type="document",                 # MemoryType.DOCUMENT
    parent_id=session.id,
    metadata={"source": "user_study_2024.pdf"},
    tags=["research", "user-behavior", "2024"],
)

note = await system.create_memory_item(
    content="Key insight: users prefer simple interfaces",
    item_type="note",                     # stored as MemoryType.CUSTOM with
                                          # metadata["custom_type"] = "note"
    parent_id=doc.id,
    tags=["insight", "ux"],
)
```

`item_type` is mapped to `MemoryType` if it matches one of: `session`, `conversation`, `topic`, `exchange`, `document`, `entity`, `custom`. Anything else is recorded as `MemoryType.CUSTOM` and the original string is preserved in `metadata["custom_type"]` — so `"note"` is technically a custom type.

### Search Memory

```python
results = await system.search_memory(
    query="user behavior",
    scope="global",                 # MemoryScope.GLOBAL
    item_types=["document"],
    tags=["research"],
    limit=5,
)

for r in results:
    print(f"{r.score:.2f}  {r.item.type.value}  {r.item.content[:80]}")
```

`scope` accepts the string form of `MemoryScope` (`global`, `session`, `conversation`, `topic`, `custom`); unknown values fall back to `GLOBAL`. Each result is a `SearchResult` wrapping a `MemoryItem`.

### Contextual Retrieval

```python
context_items = await system.get_item_context(
    item_id=doc.id,
    depth=3,
    include_siblings=True,
)

for item in context_items:
    print(item.type.value, item.content[:60])
```

### Token-Bounded Context

```python
optimized_items = await system.optimize_memory_context(
    item_ids=[doc.id, note.id],
    max_tokens=4000,
)
```

The method retrieves each item by id, drops any missing ones, and delegates to `GenericMemoryManager.optimize_context`.

## Manual Context Optimization

`MemorgSystem.optimize_context` exposes the window optimizer directly for ad-hoc content (not necessarily backed by stored items):

```python
from memorg.models import Entity, EntityType

entities = [
    Entity(name="Project Alpha", type=EntityType.CONCEPT, salience=0.9, metadata={}),
    Entity(name="Q1 Deadline", type=EntityType.EVENT, salience=0.8, metadata={}),
]

prompt_template = await system.optimize_context(
    content="Long content to optimize...",
    entities=entities,
    max_tokens=2000,
)
```

`EntityType` is one of `PERSON`, `ORGANIZATION`, `LOCATION`, `CONCEPT`, `EVENT`, `OTHER`. The return value is a prompt template string built from the optimized content (`ProgressiveSummarization` + `TokenOptimizer` under the hood).

## Memory Usage Tracking

```python
usage = await system.get_memory_usage()
# {
#   "total_tokens": int,       # rough estimate: len(content) // 4
#   "active_items": int,
#   "compressed_items": int,
#   "vector_count": int,
#   "index_size": int,
# }
```

`total_tokens` is a coarse heuristic (4 chars per token across all stored content), useful as a quick gauge rather than a precise accounting.

## Error Handling

All methods log errors via the `memorg` logger before re-raising. Wrap calls in `try/except` if you need to recover:

```python
try:
    session = await system.create_session("user", {})
except Exception as exc:
    logger.exception("Failed to create session: %s", exc)
    raise
```

## Best Practices

1. **One session per user/workflow** — sessions are the natural unit of isolation.
2. **One topic per subject** — keeps importance scoring focused.
3. **Tag memory items consistently** — lowercase, hyphenated, project-scoped.
4. **Check `get_memory_usage` periodically** — large `vector_count` values are the first sign of growth.
5. **Optimize before prompting** — call `optimize_context` (or `optimize_memory_context`) when feeding context to your own LLM call.
