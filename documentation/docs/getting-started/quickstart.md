# Quick Start

Get up and running with Memorg in 5 minutes.

## Prerequisites

1. Memorg installed (`pip install memorg`)
2. OpenAI API key set (`export OPENAI_API_KEY="..."`)

## CLI Quick Start

Start the interactive CLI:

```bash
memorg
```

You'll see:

```
Welcome to Memorg CLI Chat!
Type 'help' for available commands or start chatting.

You:
```

### Basic Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `new` | Start a new conversation |
| `search` | Search conversation history |
| `memsearch` | Search all memory |
| `addnote` | Add a note with tags |
| `memory` | Show memory usage |
| `exit` | Exit the CLI |

### Example Session

```
You: Hello! I'm working on a Python project.

AI: I'd be happy to help with your Python project! What are you working on?

You: search
Enter search query: Python project
Score  Type        Content
0.92   SEMANTIC    I'm working on a Python project...

You: memory
Memory Usage:
Total Tokens: 156
Active Items: 2
Compressed Items: 0
Vector Count: 2
Index Size: 0.12 MB
```

## Library Quick Start

### Basic Usage

```python
import asyncio
from memorg import MemorgSystem
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore
from openai import AsyncOpenAI

async def main():
    # Initialize components
    storage = SQLiteStorageAdapter("memorg.db")
    vector_store = USearchVectorStore("memorg.db")
    client = AsyncOpenAI()

    # Create the system
    system = MemorgSystem(storage, vector_store, client)

    # Create a session
    session = await system.create_session("user123", {"max_tokens": 4096})
    print(f"Created session: {session.id}")

    # Start a conversation
    conversation = await system.start_conversation(session.id)
    print(f"Started conversation: {conversation.id}")

    # Create a topic
    topic = await system.context_store.create_topic(
        conversation.id,
        "Getting Started"
    )

    # Add an exchange
    exchange = await system.add_exchange(
        topic.id,
        "What is Memorg?",
        "Memorg is a hierarchical context management system for LLMs."
    )

    # Search context
    results = await system.search_context("context management")
    for result in results:
        print(f"Found: {result.entity}")

asyncio.run(main())
```

### Memory Abstraction (Non-Chat Workflows)

```python
async def document_workflow():
    # Same initialization as above
    system = MemorgSystem(storage, vector_store, client)
    session = await system.create_session("analyst", {})

    # Create a document memory item
    doc = await system.create_memory_item(
        content="Q3 revenue increased by 15%",
        item_type="document",
        parent_id=session.id,
        tags=["finance", "q3", "revenue"]
    )

    # Search across all memory
    results = await system.search_memory(
        query="revenue growth",
        item_types=["document"],
        tags=["finance"]
    )

    for result in results:
        print(f"Score: {result.score:.2f} - {result.item.content}")
```

## What's Next?

- [CLI Guide](../guides/cli-guide.md) - Deep dive into CLI features
- [Library Usage](../guides/library-usage.md) - Advanced library patterns
- [Architecture](../architecture/overview.md) - Understand how Memorg works
