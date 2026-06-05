# Memorg: Hierarchical Context Management System

Memorg is an external memory layer for Large Language Models. It stores, organizes, and retrieves context so an assistant can sustain longer, more coherent interactions than a raw context window allows.

It ships as a Python library, an interactive CLI (`memorg`), and a Model Context Protocol server (`memorg-mcp`).

## Why Memorg?

Large Language Models face fundamental limitations in managing context over extended conversations or complex workflows:

- **Context Window Limits** — model context windows are finite and fill up quickly
- **Information Loss** — important details from earlier turns get displaced or forgotten
- **Undifferentiated Context** — without filtering, every prior token is treated as equally relevant
- **Memory Fragmentation** — related information ends up scattered across turns without explicit structure

Memorg addresses these by deciding what is worth keeping, how to group it, and how to surface it back to the model on demand.

## Key Features

- **Hierarchical context** — Session > Conversation > Topic > Exchange, persisted in SQLite
- **Generic memory items** — store documents, notes, entities, or custom types alongside chat history
- **Hybrid retrieval** — combines USearch vector search (OpenAI embeddings) with SQLite FTS5 keyword search
- **Importance scoring** — exchanges are scored against current topic context
- **Window optimization** — progressive summarization plus `tiktoken`-based token budgeting
- **Tag-based search** — filter memory items by `tags` and `item_types`
- **Dual interface** — Python library or interactive CLI; MCP server for Claude Desktop and other MCP clients

## Quick Links

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [CLI Guide](guides/cli-guide.md)
- [Library Usage](guides/library-usage.md)
- [MCP Server](guides/mcp-server.md)
- [Architecture Overview](architecture/overview.md)

## At a Glance

```python
from memorg import MemorgSystem
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore
from openai import AsyncOpenAI

system = MemorgSystem(
    storage=SQLiteStorageAdapter("memorg.db"),
    vector_store=USearchVectorStore("memorg.db"),
    openai_client=AsyncOpenAI(),
)

session = await system.create_session("user_123", {"max_tokens": 4096})
conversation = await system.start_conversation(session.id)
topic = await system.context_store.create_topic(conversation.id, "Project Help")

await system.add_exchange(
    topic.id,
    user_message="How do I handle authentication?",
    system_message="You can use JWT tokens or session-based auth...",
)

results = await system.search_context("authentication")
```

## Architecture at a Glance

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│  MemorgSystem   │───▶│   ContextStore   │───▶│  SQLite (+ FTS5)   │
└────────┬────────┘    └────────┬─────────┘    └────────────────────┘
         │                      │
         │                      ▼
         │             ┌──────────────────┐    ┌────────────────────┐
         │             │ USearchVector-   │───▶│   .usearch index   │
         │             │     Store        │    │  (1536-dim, cos)   │
         │             └──────────────────┘    └────────────────────┘
         │
         ├─▶ ContextManager (prioritize + compress)
         ├─▶ RetrievalSystem (process + rank)
         ├─▶ ContextWindowOptimizer (summarize + budget)
         └─▶ Memory abstraction (HierarchicalMemoryStore + GenericMemoryManager)
```

See [Architecture Overview](architecture/overview.md) for the component breakdown and [Technical Specification](architecture/technical-spec.md) for protocols and storage schema.

## Install and Run

```bash
pip install memorg
export OPENAI_API_KEY="sk-..."
memorg
```

Follow the [Quick Start](getting-started/quickstart.md) for a guided walkthrough.

## Project

- Repository: [neul-labs/memorg](https://github.com/neul-labs/memorg)
- License: MIT
- Python: 3.11+
