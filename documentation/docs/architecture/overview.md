# Architecture Overview

This page introduces Memorg's components and how they cooperate inside `MemorgSystem`.

## System Components

Memorg has five logical components. The first four are the original "context management" pipeline; the fifth is the generic memory layer that sits alongside it.

### 1. Context Store

`memorg.context_store.ContextStore`

Manages the chat hierarchy and its persistence.

- Creates and retrieves `Session`, `Conversation`, `Topic`, `Exchange`
- Persists data via a `StorageAdapter`
- Generates and stores embeddings via a `VectorStore`
- Provides basic listing/retrieval operations

**Related classes**

- `memorg.storage.sqlite_storage.SQLiteStorageAdapter` (default storage)
- `memorg.vector_store.usearch_vector_store.USearchVectorStore` (default vectors)
- `memorg.storage.storage_adapter.StorageAdapter` (protocol)
- `memorg.vector_store.vector_store.VectorStore` (protocol)

### 2. Context Manager

`memorg.context_manager.ContextManager`

Handles prioritisation, compression, and working memory.

- Prioritise information by recency (`RecencyWeightedStrategy`)
- Compress content while preserving key information (`ExtractiveSummarization`)
- Manage a token-budgeted working-memory buffer (`WorkingMemory(capacity=4096)`)

In `MemorgSystem`, the working memory defaults to a 4096-token capacity.

### 3. Retrieval System

`memorg.retrieval.RetrievalSystem`

Provides intelligent search.

- `SimpleQueryProcessor` — turns the user query into an embedding plus parsed metadata
- `MultiFactorScorer` — ranks candidate items combining multiple signals
- Result match types: `KEYWORD`, `SEMANTIC`, `TEMPORAL`, `HYBRID`, `IMPORTANCE`

### 4. Context Window Optimizer

`memorg.window_optimizer.ContextWindowOptimizer`

Manages token usage and prompt construction.

- `ProgressiveSummarization` — collapses long content while keeping the head/tail intact
- `TokenOptimizer` — uses `tiktoken` (`cl100k_base`) to fit the result under a budget
- `create_prompt_template(optimized)` — turns the optimized payload into a template string

### 5. Memory Abstraction

`memorg.memory.store.HierarchicalMemoryStore` and `memorg.memory.manager.GenericMemoryManager`

Generic interface for non-chat workflows.

- Treat anything as a `MemoryItem` (`document`, `note`, `entity`, custom)
- Tag-based organisation, parent/child relationships, embeddings
- Reuses the same `StorageAdapter` and `VectorStore` as the chat hierarchy

See [Memory Abstraction](memory-abstraction.md) for details.

## Data Model

### Chat Hierarchy

```
Session (top-level container)
├── id, user_id, system_config, metadata
└── conversations[]
    ├── id, title, summary, embedding, metadata
    └── topics[]
        ├── id, title, summary, embedding, key_entities, metadata
        └── exchanges[]
            ├── id, importance_score, embedding, metadata
            ├── user_message: Message
            └── system_message: Message
```

`Message` carries `raw_content`, a parsed `ParsedContent` (entities, intents, sentiment), and an embedding.

### Storage Mapping

- **SQLite** — four collections (`sessions`, `conversations`, `topics`, `exchanges`), each backed by an FTS5 virtual table mirrored via triggers.
- **USearch** — 1536-dimensional `f32` index with cosine metric. Vector metadata (string id, raw vector, text content) lives in a `vector_metadata` table inside the same SQLite database.

## Request Flow

A typical add-then-search cycle:

```
User Input
    │
    ▼
┌─────────────────┐
│  MemorgSystem   │  ← public entry point
└────────┬────────┘
         │
   ┌─────┴─────┐
   ▼           ▼
┌────────┐ ┌─────────┐
│ Store  │ │ Search  │
└───┬────┘ └────┬────┘
    │           │
    ▼           ▼
┌─────────────────────┐
│ SQLite (+ FTS5)     │
│ USearch (.usearch)  │
└─────────────────────┘
```

When `search_context` is invoked:

1. The query is embedded by `SimpleQueryProcessor`.
2. USearch returns nearest neighbours (`max_results * 2` for headroom).
3. If fewer than `max_results` items are returned, an FTS5 keyword search runs across all four collections.
4. The merged candidate list is ranked by `MultiFactorScorer`.

## Extension Points

### Custom Storage

```python
from memorg.storage.storage_adapter import StorageAdapter

class CustomStorage(StorageAdapter):
    async def write(self, collection: str, id: str, data) -> None: ...
    async def read(self, collection: str, id: str): ...
    async def query(self, collection: str, filter): ...
    async def delete(self, collection: str, id: str) -> bool: ...
    async def get_stats(self): ...
```

Pass an instance to `MemorgSystem(storage=...)`.

### Custom Prioritization

```python
class CustomPriority:
    def calculate_priority(self, entity, context) -> float: ...
```

Plug into `ContextManager(prioritization_strategy=CustomPriority())` and construct `MemorgSystem` to use that manager (or replace `system.context_manager` after construction).

### Custom Compression

```python
class CustomCompression:
    async def compress(self, content, context): ...
```

### Custom Vector Store

```python
from memorg.vector_store.vector_store import VectorStore

class CustomVectorStore(VectorStore):
    async def add_vector(self, id, vector, metadata): ...
    async def search_nearest(self, vector, limit): ...
    async def delete_vector(self, id) -> bool: ...
    async def get_stats(self): ...
```

Pass an instance to `MemorgSystem(vector_store=...)`.

See [Technical Specification](technical-spec.md) for the full protocol definitions and storage schema.
