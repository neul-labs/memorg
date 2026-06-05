# Quick Start

This page takes you from a clean install to your first stored exchange and your first search, in both the CLI and the library.

## Prerequisites

1. `pip install memorg` (see [Installation](installation.md))
2. `export OPENAI_API_KEY="sk-..."`

## CLI Quick Start

```bash
memorg
```

The CLI uses a fixed user id (`cli_user`) and a default database `memorg.db` in the working directory. On first input it auto-creates a session, a conversation, and a `General Discussion` topic — so you can just start typing.

```
Welcome to Memorg CLI Chat!
Type 'help' for available commands or start chatting.

You:
```

### Available Commands

These are the literal commands recognised by the CLI loop (`MemorgCLI.chat`):

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `new` | Start a new conversation in the current session |
| `search` | Search conversation history (`search_context`) |
| `memsearch` | Search across all memory items (`search_memory`) |
| `addnote` | Add a tagged note via `create_memory_item(item_type="note")` |
| `memory` | Print memory usage statistics |
| `exit` | Quit |

Any other input is treated as a chat message: the CLI searches for relevant prior context, calls `gpt-4o-mini` with that context prepended, prints the response, and stores both the user message and the AI response as exchanges on the current topic.

### Example Session

```
You: I'm working on a Python project that needs a memory layer.

AI: I'd be happy to help with your Python project! What kind of memory
    layer are you looking for — conversational history, embeddings, both?

You: search
Enter search query: Python project
Score  Type        Content
0.92   SEMANTIC    I'm working on a Python project that needs a memory layer...

You: memory

Memory Usage:
Total Tokens: 156
Active Items: 2
Compressed Items: 0
Vector Count: 2
Index Size: 0.12 MB
```

## Library Quick Start

### Minimal Setup

```python
import asyncio
from openai import AsyncOpenAI
from memorg import MemorgSystem
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore


async def main():
    system = MemorgSystem(
        storage=SQLiteStorageAdapter("memorg.db"),
        vector_store=USearchVectorStore("memorg.db"),
        openai_client=AsyncOpenAI(),
    )

    session = await system.create_session("user123", {"max_tokens": 4096})
    conversation = await system.start_conversation(session.id)
    topic = await system.context_store.create_topic(conversation.id, "Getting Started")

    await system.add_exchange(
        topic.id,
        user_message="What is Memorg?",
        system_message="Memorg is a hierarchical context management system for LLMs.",
    )

    results = await system.search_context("context management")
    for result in results:
        print(f"{result.score:.2f}  {result.match_type.value}  {result.entity}")


asyncio.run(main())
```

Note that `MemorgSystem.create_session` takes the `user_id` first and the `config` dict second; `start_conversation` takes a `session_id`; `create_topic` lives on the underlying `context_store` because there's no direct convenience wrapper on `MemorgSystem`.

### Memory Abstraction (Non-Chat Workflows)

The generic memory layer lets you store anything — documents, notes, custom types — under the same session hierarchy:

```python
# Within the same MemorgSystem as above
doc = await system.create_memory_item(
    content="Q3 revenue increased by 15%.",
    item_type="document",          # MemoryType.DOCUMENT
    parent_id=session.id,
    metadata={"source": "finance-deck.pdf"},
    tags=["finance", "q3", "revenue"],
)

results = await system.search_memory(
    query="revenue growth",
    item_types=["document"],
    tags=["finance"],
    limit=5,
)

for r in results:
    print(f"{r.score:.2f}: {r.item.content}")
```

Unknown `item_type` strings are stored as `MemoryType.CUSTOM` with the original label preserved in `metadata["custom_type"]`.

## MCP Quick Start

Start the FastMCP server:

```bash
memorg-mcp --host 127.0.0.1 --port 3000
```

See the [MCP Server guide](../guides/mcp-server.md) for the available tools and Claude Desktop wiring.

## What's Next?

- [CLI Guide](../guides/cli-guide.md) — every command in detail
- [Library Usage](../guides/library-usage.md) — sessions, topics, exchanges, memory items
- [Configuration](configuration.md) — environment variables and component overrides
- [Architecture Overview](../architecture/overview.md) — components and data flow
