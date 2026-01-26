# Architecture Overview

This document provides a high-level overview of Memorg's architecture.

## System Components

Memorg consists of five main components:

### 1. Context Store

Manages the hierarchical data structure and persistence.

**Responsibilities:**

- Create and manage sessions, conversations, topics, exchanges
- Persist data to SQLite
- Generate and store vector embeddings
- Provide basic retrieval operations

**Key Classes:**

- `ContextStore` - Main store class
- `SQLiteStorageAdapter` - SQLite persistence
- `USearchVectorStore` - Vector similarity search

### 2. Context Manager

Handles prioritization, compression, and working memory.

**Responsibilities:**

- Prioritize information based on recency and importance
- Compress content while preserving key information
- Manage working memory allocation

**Key Classes:**

- `ContextManager` - Main manager class
- `RecencyWeightedStrategy` - Prioritization strategy
- `ExtractiveSummarization` - Compression strategy
- `WorkingMemory` - Memory allocation

### 3. Retrieval System

Provides intelligent search capabilities.

**Responsibilities:**

- Process search queries
- Perform semantic and keyword search
- Rank results by relevance

**Key Classes:**

- `RetrievalSystem` - Main retrieval class
- `SimpleQueryProcessor` - Query processing
- `MultiFactorScorer` - Relevance scoring

### 4. Context Window Optimizer

Manages token usage and prompt construction.

**Responsibilities:**

- Summarize content progressively
- Optimize token usage
- Create context-aware prompts

**Key Classes:**

- `ContextWindowOptimizer` - Main optimizer class
- `ProgressiveSummarization` - Summarization strategy
- `TokenOptimizer` - Token management

### 5. Memory Abstraction

Generic interface for non-chat workflows.

**Responsibilities:**

- Provide type-agnostic memory operations
- Support custom item types
- Enable tag-based organization

**Key Classes:**

- `MemoryItem` - Generic memory item
- `HierarchicalMemoryStore` - Memory storage
- `GenericMemoryManager` - High-level operations

## Data Model

### Hierarchy

```
Session (top-level container)
├── user_id
├── system_config
└── conversations[]
    ├── title
    ├── summary
    └── topics[]
        ├── title
        ├── summary
        └── exchanges[]
            ├── user_message
            ├── system_message
            └── importance_score
```

### Storage

- **SQLite**: Structured data (sessions, conversations, topics, exchanges)
- **USearch**: Vector embeddings for semantic search

## Request Flow

```
User Input
    │
    ▼
┌─────────────────┐
│   Main System   │ ← Entry point
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐  ┌─────────┐
│ Store  │  │ Search  │
└────┬───┘  └────┬────┘
     │           │
     ▼           ▼
┌─────────────────────┐
│     SQLite +        │
│     USearch         │
└─────────────────────┘
```

## Extension Points

### Custom Storage

Implement `StorageAdapter` protocol:

```python
class CustomStorage(StorageAdapter):
    async def write(self, collection, id, data): ...
    async def read(self, collection, id): ...
    async def query(self, collection, filter): ...
```

### Custom Prioritization

Implement `PrioritizationStrategy` protocol:

```python
class CustomStrategy(PrioritizationStrategy):
    def calculate_priority(self, entity, context): ...
```

### Custom Compression

Implement `CompressionStrategy` protocol:

```python
class CustomCompression(CompressionStrategy):
    async def compress(self, content, context): ...
```
