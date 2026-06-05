# User Guides

Memorg exposes the same underlying system through three surfaces: a Python library, an interactive CLI, and an MCP server. These guides walk through each.

## Available Guides

- [CLI Guide](cli-guide.md) — every interactive command in `memorg`
- [Library Usage](library-usage.md) — sessions, conversations, topics, exchanges, and the memory abstraction
- [MCP Server](mcp-server.md) — `memorg-mcp` for Claude Desktop and other MCP clients
- [Usage Patterns](usage-patterns.md) — recurring scenarios and how the components cooperate to handle them

## Choosing the Right Surface

| Surface | Best for | Notes |
|---------|----------|-------|
| **CLI** (`memorg`) | Quick experimentation, single-user notebooks | Uses a fixed `cli_user`, writes to `memorg.db` in the working directory. |
| **Library** | Embedding memory in your own agent or service | Async-first; pass your own `AsyncOpenAI`, storage, and vector store. |
| **MCP server** (`memorg-mcp`) | Letting Claude Desktop or other MCP clients call Memorg as tools | Six tools exposed: `create_session`, `start_conversation`, `add_exchange`, `search_context`, `get_memory_usage`, `optimize_context`. |
| **Memory abstraction** (library) | Non-chat workflows — documents, notes, research, knowledge bases | `create_memory_item`, `search_memory`, `get_item_context`, `optimize_memory_context`. |

All four share the same SQLite + USearch backing files, so data written by one surface is visible to the others.

## Cross-Cutting Concepts

Before diving into a specific guide, it helps to know:

- A **session** is the top-level container; one session per user/workflow is typical.
- A **conversation** lives inside a session and groups related interactions.
- A **topic** lives inside a conversation and groups related exchanges.
- An **exchange** is a single `(user_message, system_message)` pair, stored with an importance score and an embedding.
- A **memory item** is a generic record (document, note, custom) that participates in the same hierarchy via `parent_id`.

See [Architecture Overview](../architecture/overview.md) for how the components interact.
