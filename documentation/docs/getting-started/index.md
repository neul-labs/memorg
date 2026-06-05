# Getting Started

Memorg is distributed as the `memorg` package on PyPI. It bundles a Python library, an interactive CLI (`memorg`), and an MCP server (`memorg-mcp`).

## Prerequisites

- **Python 3.11 or 3.12** — declared in `pyproject.toml`
- **OpenAI API key** — used for embeddings (`text-embedding-ada-002`, 1536-dim) and chat completions

## Choose Your Interface

Memorg can be used in three different ways. Pick the one that matches your workflow:

| Interface | When to use it | Entry point |
|-----------|----------------|-------------|
| **CLI** (`memorg`) | Quick experimentation, single-user chat-with-memory | `memorg.cli_entry:main` |
| **Python library** | Embed memory in your own application or agent loop | `from memorg import MemorgSystem` |
| **MCP server** (`memorg-mcp`) | Expose memory to Claude Desktop or other MCP clients | `memorg.mcp.cli:main` |

All three interfaces sit on top of the same `MemorgSystem` core, so a database written by the CLI can be read by the library or the MCP server, and vice versa.

## Storage Footprint

A fresh Memorg install creates two artifacts on disk (default base name `memorg`):

- `memorg.db` — SQLite database holding sessions, conversations, topics, exchanges, and FTS5 indexes
- `memorg.usearch` — USearch vector index (1536-dimensional, cosine metric)

Both files share the same base path, so passing `--db-path ./data/memorg.db` writes `./data/memorg.usearch` next to it.

## Next Steps

1. [Installation](installation.md) — install from PyPI or source
2. [Quick Start](quickstart.md) — first session, conversation, topic, and search
3. [Configuration](configuration.md) — environment variables and component options

## Support

- Issues: [github.com/neul-labs/memorg/issues](https://github.com/neul-labs/memorg/issues)
- Architecture: [Overview](../architecture/overview.md), [Technical Specification](../architecture/technical-spec.md)
