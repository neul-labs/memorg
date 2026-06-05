# CLI Reference

Memorg installs two console scripts. This page documents both.

## `memorg`

Interactive chat CLI implemented in `memorg.cli:MemorgCLI` (entry point `memorg.cli_entry:main`).

### Synopsis

```bash
memorg
```

The CLI takes no command-line flags — it is configured purely via environment variables and the working directory. It writes to `memorg.db` (and `memorg.usearch`) in the directory where it is launched.

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key. May be supplied via `.env` (the CLI calls `dotenv.load_dotenv()` at import). |

Missing key behaviour: the CLI prints `Please set OPENAI_API_KEY environment variable` and exits.

### Interactive Commands

The chat loop dispatches on the literal lowercased input. Anything else is treated as a chat message.

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `new` | Start a new conversation |
| `search` | Prompt for a query, then run `search_context` |
| `memsearch` | Prompt for a query, then run `search_memory` |
| `addnote` | Prompt for content and tags, then create a `note` memory item |
| `memory` | Print memory usage stats from `get_memory_usage` |
| `exit` | Quit |

See [CLI Guide](../guides/cli-guide.md) for a walkthrough of each command.

### Examples

```bash
# Start the CLI
memorg

# With env var supplied inline
OPENAI_API_KEY=sk-... memorg

# Pointing at a project-specific database via working directory
cd ./projects/memorg-research && memorg
```

---

## `memorg-mcp`

MCP server implemented in `memorg.mcp.server:MemorgMCP` (entry point `memorg.mcp.cli:main`).

### Synopsis

```bash
memorg-mcp [--host HOST] [--port PORT] [--db-path PATH] [--log-level LEVEL]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Host to bind |
| `--port` | `3000` | Port to bind |
| `--db-path` | `memorg.db` | SQLite + USearch base path |
| `--log-level` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

### Log Levels

- `DEBUG`
- `INFO`
- `WARNING`
- `ERROR`
- `CRITICAL`

The chosen level is applied via `logging.basicConfig` at startup.

### Examples

```bash
# Start with defaults
memorg-mcp

# Custom host/port and database location
memorg-mcp --host 0.0.0.0 --port 8080 --db-path ./data/memorg.db

# Debug mode
memorg-mcp --log-level DEBUG
```

### Startup Output

```
Starting Memorg MCP server on 127.0.0.1:3000
Database path: memorg.db
Log level: INFO
```

### Exposed MCP Tools

| Tool | Purpose |
|------|---------|
| `create_session` | Create a session |
| `start_conversation` | Start a conversation |
| `add_exchange` | Append an exchange to a topic |
| `search_context` | Hybrid context search |
| `get_memory_usage` | Memory statistics |
| `optimize_context` | Optimize free-form content for a token budget |

Input/output schemas are documented in [MCP Server Guide](../guides/mcp-server.md). Topic creation is not exposed via MCP — use the library if you need it.

### Shutdown

`Ctrl+C` triggers a clean shutdown:

```
Shutting down Memorg MCP server...
```

Unhandled exceptions cause the CLI to exit with status `1`.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Unhandled exception (e.g. `memorg-mcp` failed to start) |
| `130` | Interrupted by `Ctrl+C` (standard Python behaviour) |
