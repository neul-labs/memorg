# MCP Server Guide

Memorg ships with a Model Context Protocol server, `memorg-mcp`, built on `fastmcp`. It exposes a subset of `MemorgSystem` as MCP tools so that clients like Claude Desktop can use Memorg as an external memory.

## Overview

The server is implemented in `memorg/mcp/server.py` as `MemorgMCP`, with the CLI entry point in `memorg/mcp/cli.py`. On startup it constructs a `MemorgSystem` with:

- `SQLiteStorageAdapter(db_path)`
- `USearchVectorStore(db_path)`
- `AsyncOpenAI()` (reads `OPENAI_API_KEY` from the environment, including `.env`)

## Starting the Server

```bash
memorg-mcp
```

With explicit options:

```bash
memorg-mcp --host 127.0.0.1 --port 3000 --db-path memorg.db --log-level INFO
```

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Host to bind |
| `--port` | `3000` | Port to bind |
| `--db-path` | `memorg.db` | SQLite + USearch base path |
| `--log-level` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

On `KeyboardInterrupt` the CLI prints `Shutting down Memorg MCP server...` and exits cleanly.

## Available MCP Tools

The server exposes six tools. Inputs and outputs are JSON.

### `create_session`

Create a new Memorg session.

**Input**

```json
{
  "user_id": "user123",
  "config": {"max_tokens": 4096}
}
```

**Output**

```json
{
  "session_id": "<uuid>",
  "created_at": "<iso-8601>",
  "user_id": "user123",
  "system_config": {"max_tokens": 4096}
}
```

### `start_conversation`

Start a new conversation in an existing session.

**Input**

```json
{"session_id": "<uuid>"}
```

**Output**

```json
{
  "conversation_id": "<uuid>",
  "created_at": "<iso-8601>",
  "title": "...",
  "summary": "..."
}
```

### `add_exchange`

Append an exchange to a topic.

**Input**

```json
{
  "topic_id": "<uuid>",
  "user_message": "Hello",
  "system_message": "Hi there!"
}
```

**Output**

```json
{
  "exchange_id": "<uuid>",
  "created_at": "<iso-8601>",
  "user_message": "Hello",
  "system_message": "Hi there!",
  "importance_score": 0.42
}
```

There is no MCP tool to create topics — call `add_exchange` with a topic id already created via the library or CLI, or open a feature request if you need topic creation exposed.

### `search_context`

Run the hybrid context search.

**Input**

```json
{
  "query": "search terms",
  "scope": "ALL",
  "max_results": 10
}
```

`scope` accepts the names of the `SearchScope` enum (`SESSION`, `CONVERSATION`, `TOPIC`, `ALL`). Unknown values default to `ALL`.

**Output**

```json
{
  "query": "search terms",
  "results": [
    {"score": 0.93, "content": "...", "type": "semantic"}
  ],
  "total_results": 1
}
```

### `get_memory_usage`

Return memory statistics.

**Input**

```json
{}
```

**Output**

```json
{
  "total_tokens": 0,
  "active_items": 0,
  "compressed_items": 0,
  "vector_count": 0,
  "index_size": 0
}
```

### `optimize_context`

Optimize free-form content for a token budget. The server passes an empty `entities` list to `MemorgSystem.optimize_context`.

**Input**

```json
{
  "content": "Long content...",
  "max_tokens": 4000
}
```

**Output**

```json
{
  "optimized_content": "...",
  "original_length": 5230,
  "optimized_length": 1843
}
```

## Claude Desktop Integration

Add the server to your Claude Desktop configuration. The exact path is platform-dependent (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS).

```json
{
  "mcpServers": {
    "memorg": {
      "command": "memorg-mcp",
      "args": ["--port", "3000"]
    }
  }
}
```

Restart Claude Desktop and the six tools above become available in chats.

## Example Conversation

```
Human: Remember that our project deadline is March 15th.

Claude: [calls create_session, start_conversation, add_exchange]
        I've stored that for you. The deadline is March 15th.
```

## Limitations

- `create_topic` is not exposed as an MCP tool; create topics from the library if you need finer-grained organisation than a single auto-created topic per conversation.
- The MCP server hard-codes an empty `entities` list when calling `optimize_context`, so importance-aware optimization isn't currently surfaced through MCP.
- The server reuses a single `MemorgSystem` instance per process; concurrent writes go through the same SQLite database.