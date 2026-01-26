# Technical Specification

Detailed technical specification for Memorg.

## System Architecture

```
┌─────────────────────────────────────┐
│           Client Interface          │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│        Context Service Layer        │
├─────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐  │
│  │   Context   │   │  Retrieval  │  │
│  │   Manager   │◄──►   Service   │  │
│  └─────┬───────┘   └─────┬───────┘  │
│        │                 │          │
│  ┌─────▼───────┐   ┌─────▼───────┐  │
│  │   Window    │   │   Context   │  │
│  │  Optimizer  │   │    Store    │  │
│  └─────────────┘   └─────────────┘  │
└─────────────────────────────────────┘
                │
┌───────────────▼─────────────────────┐
│         LLM Integration Layer       │
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
```

## Component Specifications

### Context Store

**Storage Interface:**

```python
class StorageAdapter(Protocol):
    async def write(self, collection: str, id: str, data: Dict) -> None: ...
    async def read(self, collection: str, id: str) -> Optional[Dict]: ...
    async def query(self, collection: str, filter: Dict) -> List[Dict]: ...
    async def delete(self, collection: str, id: str) -> bool: ...
    async def get_stats(self) -> Dict[str, int]: ...
```

**Vector Store Interface:**

```python
class VectorStore(Protocol):
    async def add_vector(self, id: str, vector: List[float], metadata: Dict) -> None: ...
    async def search_nearest(self, vector: List[float], limit: int) -> List[Dict]: ...
    async def delete_vector(self, id: str) -> bool: ...
    async def get_stats(self) -> Dict[str, int]: ...
```

### Context Manager

**Prioritization Strategy:**

```python
class PrioritizationStrategy(Protocol):
    def calculate_priority(
        self,
        entity: Exchange,
        context: Dict[str, Any]
    ) -> float: ...
```

**Compression Strategy:**

```python
class CompressionStrategy(Protocol):
    async def compress(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> CompressedEntity: ...
```

### Retrieval System

**Query Processor:**

```python
class QueryProcessor(Protocol):
    async def process_query(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> ProcessedQuery: ...
```

**Relevance Scorer:**

```python
class RelevanceScorer(Protocol):
    def score(
        self,
        item: Dict[str, Any],
        query: ProcessedQuery
    ) -> float: ...
```

### Window Optimizer

**Summarization Strategy:**

```python
class SummarizationStrategy(Protocol):
    async def summarize(
        self,
        content: str,
        entities: List[Entity],
        max_tokens: int
    ) -> SummarizedContent: ...
```

## Storage Schema

### SQLite Tables

**sessions:**
- id (TEXT PRIMARY KEY)
- user_id (TEXT)
- system_config (JSON)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- metadata (JSON)

**conversations:**
- id (TEXT PRIMARY KEY)
- session_id (TEXT FK)
- title (TEXT)
- summary (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- metadata (JSON)

**topics:**
- id (TEXT PRIMARY KEY)
- conversation_id (TEXT FK)
- title (TEXT)
- summary (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- metadata (JSON)

**exchanges:**
- id (TEXT PRIMARY KEY)
- topic_id (TEXT FK)
- user_message (JSON)
- system_message (JSON)
- importance_score (REAL)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- metadata (JSON)

### Vector Index

- USearch index with 1536-dimensional vectors
- Cosine similarity metric
- Metadata storage for each vector

## Implementation Notes

### Embedding Generation

Embeddings are generated using OpenAI's `text-embedding-ada-002` model (1536 dimensions).

### Token Counting

Token counting uses `tiktoken` with the `cl100k_base` encoding.

### Async Operations

All I/O operations are async using `asyncio` and `aiosqlite`.
