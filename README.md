# Memorg

[![PyPI version](https://badge.fury.io/py/memorg.svg)](https://badge.fury.io/py/memorg)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/skelf-research/memorg/actions/workflows/publish.yml/badge.svg)](https://github.com/skelf-research/memorg/actions)

**Give your LLM a memory that actually works.**

Memorg is an external memory layer for LLMs. It stores, organizes, and retrieves context so your AI can have longer, smarter conversations without forgetting what happened 5 minutes ago.

## The Problem

LLMs forget. Context windows fill up. Important details get lost. Your chatbot asks the same questions twice.

## The Solution

```python
from memorg import MemorgSystem
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore
from openai import AsyncOpenAI

# Set up persistent memory
system = MemorgSystem(
    storage=SQLiteStorageAdapter("memory.db"),
    vector_store=USearchVectorStore("memory.db"),
    openai_client=AsyncOpenAI()
)

# Create a session and start remembering
session = await system.create_session("user_123", {})
conversation = await system.start_conversation(session.id)

# Later: find relevant context
results = await system.search_context("what did we discuss about the API?")
```

## Install

```bash
pip install memorg
```

## Quick Start

### Option 1: Use the CLI

```bash
export OPENAI_API_KEY="sk-..."
memorg
```

Then just chat. Memorg handles the memory.

```
You: I'm building a REST API for user management
AI: I can help with that! What framework are you using?

You: search
Enter search query: API
Score  Type        Content
0.95   SEMANTIC    I'm building a REST API for user management...
```

### Option 2: Use as a Library

```python
import asyncio
from memorg import MemorgSystem
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore
from openai import AsyncOpenAI

async def main():
    # Initialize
    system = MemorgSystem(
        storage=SQLiteStorageAdapter("memorg.db"),
        vector_store=USearchVectorStore("memorg.db"),
        openai_client=AsyncOpenAI()
    )

    # Create session
    session = await system.create_session("user_1", {"max_tokens": 4096})
    conversation = await system.start_conversation(session.id)
    topic = await system.context_store.create_topic(conversation.id, "Project Help")

    # Store an exchange
    await system.add_exchange(
        topic.id,
        user_message="How do I handle authentication?",
        system_message="You can use JWT tokens or session-based auth..."
    )

    # Search later
    results = await system.search_context("authentication")
    for r in results:
        print(f"{r.score:.2f}: {r.entity}")

asyncio.run(main())
```

## How It Works

Memorg organizes memory hierarchically:

```
Session (user's workspace)
└── Conversation (a chat thread)
    └── Topic (specific subject)
        └── Exchange (message pair)
```

Each piece gets:
- **Stored** in SQLite for persistence
- **Embedded** with OpenAI for semantic search
- **Indexed** with USearch for fast retrieval
- **Scored** by importance and recency

When you search, Memorg finds the most relevant context across all your history.

## Key Features

| Feature | What it does |
|---------|--------------|
| **Hierarchical Storage** | Organize by session → conversation → topic → exchange |
| **Semantic Search** | Find context by meaning, not just keywords |
| **Importance Scoring** | Prioritize recent and relevant information |
| **Token Optimization** | Fit more context into your LLM's window |
| **Memory Abstraction** | Store documents, notes, anything—not just chat |

## Beyond Chat: Store Anything

```python
# Store a document
doc = await system.create_memory_item(
    content="Meeting notes: decided to use PostgreSQL for prod",
    item_type="document",
    tags=["meeting", "database", "decisions"]
)

# Store a note
note = await system.create_memory_item(
    content="TODO: Review the auth implementation",
    item_type="note",
    tags=["todo", "auth"]
)

# Search across everything
results = await system.search_memory(
    query="database decisions",
    item_types=["document", "note"],
    tags=["decisions"]
)
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `help` | Show commands |
| `new` | Start new conversation |
| `search` | Search conversation history |
| `memsearch` | Search all memory items |
| `addnote` | Add a tagged note |
| `memory` | Show usage stats |
| `exit` | Quit |

## Configuration

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional
export MEMORG_DB_PATH="./data/memorg.db"
export MEMORG_LOG_LEVEL="INFO"
```

## Documentation

Full docs: [skelf-research.github.io/memorg](https://skelf-research.github.io/memorg/)

- [Installation](https://skelf-research.github.io/memorg/getting-started/installation/)
- [Quick Start](https://skelf-research.github.io/memorg/getting-started/quickstart/)
- [Library Guide](https://skelf-research.github.io/memorg/guides/library-usage/)
- [Architecture](https://skelf-research.github.io/memorg/architecture/overview/)

## Development

```bash
git clone https://github.com/skelf-research/memorg.git
cd memorg
poetry install
poetry run pytest
```

## Contributing

PRs welcome. Please open an issue first for major changes.

## License

MIT
