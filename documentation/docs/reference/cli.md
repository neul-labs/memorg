# CLI Reference

Complete reference for Memorg command-line tools.

## memorg

Interactive CLI for Memorg.

### Synopsis

```bash
memorg [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version |

### Interactive Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `new` | Start a new conversation |
| `search` | Search conversation history |
| `memsearch` | Search all memory items |
| `addnote` | Add a note with tags |
| `memory` | Show memory usage |
| `exit` | Exit the CLI |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key |

### Examples

```bash
# Start the CLI
memorg

# With environment variable
OPENAI_API_KEY=sk-... memorg
```

---

## memorg-mcp

MCP server for Memorg.

### Synopsis

```bash
memorg-mcp [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host HOST` | `127.0.0.1` | Host to bind |
| `--port PORT` | `3000` | Port to bind |
| `--db-path PATH` | `memorg.db` | Database path |
| `--log-level LEVEL` | `INFO` | Log level |

### Log Levels

- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

### Examples

```bash
# Start with defaults
memorg-mcp

# Custom configuration
memorg-mcp --host 0.0.0.0 --port 8080 --db-path ./data/memorg.db

# Debug mode
memorg-mcp --log-level DEBUG
```

### MCP Tools

The server exposes these tools:

| Tool | Description |
|------|-------------|
| `create_session` | Create a new session |
| `start_conversation` | Start a conversation |
| `add_exchange` | Add an exchange |
| `search_context` | Search context |
| `get_memory_usage` | Get memory stats |
| `optimize_context` | Optimize content |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `130` | Interrupted (Ctrl+C) |
