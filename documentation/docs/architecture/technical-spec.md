# Technical Specification

Detailed technical specification for Memorg.

## System Architecture

```
┌─────────────────────────────────────┐
│           Client Interface          │
│   (CLI, library, MCP server)        │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│        MemorgSystem (orchestrator)  │
├─────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐  │
│  │   Context   │   │  Retrieval  │  │
│  │   Manager   │◄──►   System    │  │
│  └─────┬───────┘   └─────┬───────┘  │
│        │                 │          │
│  ┌─────▼───────┐   ┌─────▼───────┐  │
│  │   Window    │   │   Context   │  │
│  │  Optimizer  │   │    Store    │  │
│  └─────────────┘   └─────────────┘  │
│                                     │
│  ┌─────────────┐  ┌───────────────┐ │
│  │ Hierarchical│  │   Generic     │ │
│  │ MemoryStore │◄─┤ MemoryManager │ │
│  └─────────────┘  └───────────────┘ │
└─────────────────────────────────────┘
                │
┌───────────────▼─────────────────────┐
│   Storage backends                  │
│   SQLite (+ FTS5)   USearch index   │
└─────────────────────────────────────┘
                │
┌───────────────▼─────────────────────┐
│         OpenAI (embeddings, chat)   │
└─────────────────────────────────────┘
```

## Data Structures

### Context Hierarchy

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

@dataclass
class Entity:
    name: str
    type: EntityType
    salience: float
    metadata: Dict[str, Any]
```

### Search Types

```python
class SearchScope(Enum):
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    ALL = "all"

class MatchType(Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    HYBRID = "hybrid"
    IMPORTANCE = "importance"

@dataclass
class SearchResult:
    entity: Any
    score: float
    match_type: MatchType
```

## Component Specifications

### Context Store

**`StorageAdapter` protocol** (`memorg.storage.storage_adapter`):

```python
class StorageAdapter(Protocol):
    async def write(self, collection: str, id: str, data: Dict) -> None: ...
    async def read(self, collection: str, id: str) -> Optional[Dict]: ...
    async def query(self, collection: str, filter: Dict) -> List[Dict]: ...
    async def delete(self, collection: str, id: str) -> bool: ...
    async def get_stats(self) -> Dict[str, int]: ...
```

`SQLiteStorageAdapter` is the default implementation. It treats `data` as JSON, supports `$text: {$search: ...}` filters via FTS5, and uses `aiosqlite` for async access.

**`VectorStore` protocol** (`memorg.vector_store.vector_store`):

```python
class VectorStore(Protocol):
    async def add_vector(self, id: str, vector: List[float], metadata: Dict) -> None: ...
    async def search_nearest(self, vector: List[float], limit: int) -> List[Dict]: ...
    async def delete_vector(self, id: str) -> bool: ...
    async def get_stats(self) -> Dict[str, int]: ...
```

`USearchVectorStore` defaults to 1536-dimensional `f32` vectors with cosine metric, `connectivity=16`, `expansion_add=128`, `expansion_search=64`. The index is persisted to a `.usearch` file next to the SQLite database, and vector metadata is stored in a `vector_metadata` table inside the same SQLite file.

### Context Manager

**Prioritization Strategy:**

```python
class PrioritizationStrategy(Protocol):
    def calculate_priority(
        self,
        entity: Exchange,
        context: Dict[str, Any],
    ) -> float: ...
```

Default: `RecencyWeightedStrategy`.

**Compression Strategy:**

```python
class CompressionStrategy(Protocol):
    async def compress(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> CompressedEntity: ...
```

Default: `ExtractiveSummarization(openai_client)`.

**Working memory:** `WorkingMemory(capacity=4096)` in `MemorgSystem`.

### Retrieval System

**Query Processor:**

```python
class QueryProcessor(Protocol):
    async def process_query(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> ProcessedQuery: ...
```

Default: `SimpleQueryProcessor(openai_client)`. Produces a `ProcessedQuery` with at least a `semantic_embedding` field consumed by `MemorgSystem.search_context`.

**Relevance Scorer:**

```python
class RelevanceScorer(Protocol):
    def score(
        self,
        item: Dict[str, Any],
        query: ProcessedQuery,
    ) -> float: ...
```

Default: `MultiFactorScorer`.

### Window Optimizer

**Summarization Strategy:**

```python
class SummarizationStrategy(Protocol):
    async def summarize(
        self,
        content: str,
        entities: List[Entity],
        max_tokens: int,
    ) -> SummarizedContent: ...
```

Default: `ProgressiveSummarization(openai_client)`.

**Token Optimizer:** `TokenOptimizer(openai_client=openai_client)`, using `tiktoken` with the `cl100k_base` encoding.

## Storage Schema

### SQLite Tables (chat hierarchy)

For each of `sessions`, `conversations`, `topics`, `exchanges`:

```sql
CREATE TABLE <collection> (
    id          TEXT PRIMARY KEY,
    data        TEXT,                               -- JSON
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE <collection>_fts USING fts5(
    id,
    content,
    data
);
```

`AFTER INSERT/UPDATE/DELETE` triggers keep the FTS5 mirror in sync. The mirror's `content` column is `json_extract(data, '$.content')`, which is what `$text: {$search: ...}` filters search against.

### SQLite Tables (vectors)

```sql
CREATE TABLE vector_metadata (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    string_id    TEXT UNIQUE,
    vector_data  BLOB,
    metadata     TEXT,
    text_content TEXT,
    is_deleted   BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vector_metadata_string_id ON vector_metadata(string_id);
```

The USearch index file (`<basename>.usearch`) lives next to the database.

### USearch Index Parameters

| Parameter | Value |
|-----------|-------|
| `ndim` | 1536 |
| `metric` | `cos` |
| `dtype` | `f32` |
| `connectivity` | 16 |
| `expansion_add` | 128 |
| `expansion_search` | 64 |

## Implementation Notes

### Embedding Generation

Embeddings are generated using OpenAI's `text-embedding-ada-002` model (1536 dimensions). The `OPENAI_API_KEY` environment variable is expected to be set on the calling `AsyncOpenAI` client.

### Token Counting

`TokenOptimizer` uses `tiktoken` with the `cl100k_base` encoding. The CLI's coarse `total_tokens` estimate in `get_memory_usage` is computed as `len(content) // 4` summed across all collections, deliberately approximate and intended only as a quick gauge.

### Async Operations

All I/O is asynchronous (`asyncio`, `aiosqlite`, `openai.AsyncOpenAI`). USearch index operations are synchronous, but they are CPU-bound and called inline from async code.

### MCP Server

`memorg.mcp.server.MemorgMCP` wraps a single `MemorgSystem` instance and registers six FastMCP tools. The server constructs its components in `initialize_system()` lazily on first request and reuses them for the lifetime of the process.

### Concurrency

There is one `MemorgSystem` per process and one SQLite database file. Concurrent writes to that file go through SQLite's standard locking. The vector index is held in memory and persisted via `index.save(self.index_path)`.
