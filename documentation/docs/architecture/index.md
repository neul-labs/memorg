# Architecture

Memorg is built around a small, modular core. This section explains how the pieces fit together so you can extend or replace parts of the system with confidence.

## Map of This Section

- [Architecture Overview](overview.md) — components, responsibilities, and key classes
- [Technical Specification](technical-spec.md) — protocols, storage schema, and implementation notes
- [Memory Abstraction](memory-abstraction.md) — the generic memory layer that sits alongside chat history

## Core Principles

### Hierarchical Organization

Chat data is organised in a strict tree:

```
Session
└── Conversation
    └── Topic
        └── Exchange
```

Each level has a UUID, timestamps, optional embedding, and a metadata dict. Children are not embedded directly in the parent's row — they live in their own table linked by id.

### Separation of Concerns

Each cooperating component has one job:

- **Context Store** — data persistence and retrieval
- **Context Manager** — prioritization (`RecencyWeightedStrategy`) and compression (`ExtractiveSummarization`)
- **Retrieval System** — query processing (`SimpleQueryProcessor`) and ranking (`MultiFactorScorer`)
- **Window Optimizer** — progressive summarization and `tiktoken`-based token budgeting

### Extensibility via Protocols

Most components are typed as `Protocol`s:

- `StorageAdapter`, `VectorStore` — backends
- `PrioritizationStrategy`, `CompressionStrategy` — context manager strategies
- `QueryProcessor`, `RelevanceScorer` — retrieval strategies
- `SummarizationStrategy` — window optimizer strategy

Swap any of them by passing a custom implementation when constructing the relevant component (or your own `MemorgSystem` subclass).

### Async-First

All I/O is `async`. SQLite I/O uses `aiosqlite`, OpenAI calls use `AsyncOpenAI`. The vector index (USearch) is synchronous but cheap enough that it is called directly from async code.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       MemorgSystem                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Context    │  │ Retrieval   │  │   Context Window    │  │
│  │  Manager    │  │  System     │  │     Optimizer       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                    │             │
│         └────────────────┼────────────────────┘             │
│                          ▼                                  │
│                  ┌─────────────┐                            │
│                  │   Context   │                            │
│                  │    Store    │                            │
│                  └─────────────┘                            │
│                          │                                  │
│           ┌──────────────┴──────────────┐                   │
│           ▼                             ▼                   │
│   ┌─────────────┐               ┌─────────────┐             │
│   │   SQLite    │               │   USearch   │             │
│   │  (+ FTS5)   │               │   index     │             │
│   └─────────────┘               └─────────────┘             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Memory abstraction:                                  │   │
│  │   HierarchicalMemoryStore + GenericMemoryManager     │   │
│  │   (reuses StorageAdapter and VectorStore)            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

A typical write/read cycle:

1. Caller invokes `MemorgSystem.add_exchange(topic_id, user_msg, system_msg)`.
2. `ContextStore` writes the exchange to SQLite, generates embeddings via OpenAI, and adds them to USearch.
3. `ContextManager.update_importance` scores the exchange against the current topic.
4. Later, `MemorgSystem.search_context(query)` embeds the query, runs USearch nearest-neighbour, falls back to FTS5 keyword search if needed, and the `RetrievalSystem` ranks the merged set.
5. Before calling the LLM, the caller passes the assembled content through `MemorgSystem.optimize_context` to fit the model's window.

See [Technical Specification](technical-spec.md) for the underlying protocols and storage schema.
