# MCP Server Guide

Using Memorg as a Model Context Protocol (MCP) server.

## Overview

Memorg can run as an MCP server, allowing integration with Claude Desktop and other MCP-compatible clients.

## Starting the Server

```bash
memorg-mcp
```

With options:

```bash
memorg-mcp --host 127.0.0.1 --port 3000 --db-path memorg.db --log-level INFO
```

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Host to bind the server |
| `--port` | `3000` | Port to bind the server |
| `--db-path` | `memorg.db` | Path to database file |
| `--log-level` | `INFO` | Logging level |

## Available MCP Tools

The MCP server exposes these tools:

### create_session

Create a new session for a user.

```json
{
  "user_id": "user123",
  "config": {"max_tokens": 4096}
}
```

### start_conversation

Start a new conversation in a session.

```json
{
  "session_id": "session-uuid"
}
```

### add_exchange

Add an exchange to a topic.

```json
{
  "topic_id": "topic-uuid",
  "user_message": "Hello",
  "system_message": "Hi there!"
}
```

### search_context

Search through context.

```json
{
  "query": "search terms",
  "max_results": 10
}
```

### get_memory_usage

Get current memory statistics.

```json
{}
```

### optimize_context

Optimize content for token limits.

```json
{
  "content": "Long content...",
  "max_tokens": 4000
}
```

## Claude Desktop Integration

Add to your Claude Desktop configuration:

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

## Example Usage

Once connected, Claude can use Memorg tools:

```
Human: Remember that our project deadline is March 15th.

Claude: I'll store that information for you.
[Uses add_exchange tool to store the information]