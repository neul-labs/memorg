# Configuration

Memorg can be configured through environment variables and code options.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `MEMORG_DB_PATH` | Path to SQLite database | `memorg.db` |
| `MEMORG_LOG_LEVEL` | Logging level | `INFO` |

### Setting Environment Variables

Create a `.env` file in your project root:

```
OPENAI_API_KEY=sk-...
MEMORG_DB_PATH=./data/memorg.db
MEMORG_LOG_LEVEL=DEBUG
```

## Session Configuration

When creating a session, you can pass configuration options:

```python
session = await system.create_session("user123", {
    "max_tokens": 4096,        # Token budget for this session
    "workflow": "chat",        # Workflow type
    "custom_key": "value"      # Any custom metadata
})
```

## Storage Configuration

### SQLite Storage

```python
from memorg.storage.sqlite_storage import SQLiteStorageAdapter

# Default - creates file in current directory
storage = SQLiteStorageAdapter("memorg.db")

# Custom path
storage = SQLiteStorageAdapter("/path/to/data/memorg.db")

# In-memory (for testing)
storage = SQLiteStorageAdapter(":memory:")
```

### Vector Store

```python
from memorg.vector_store.usearch_vector_store import USearchVectorStore

# Uses same base path as SQLite (creates .usearch file)
vector_store = USearchVectorStore("memorg.db")
```

## Context Manager Options

The Context Manager can be customized when initializing the system:

```python
from memorg.context_manager import (
    ContextManager,
    RecencyWeightedStrategy,
    ExtractiveSummarization,
    WorkingMemory
)

context_manager = ContextManager(
    prioritization_strategy=RecencyWeightedStrategy(),
    compression_strategy=ExtractiveSummarization(openai_client),
    working_memory=WorkingMemory(capacity=8192)  # Custom capacity
)
```

## CLI Configuration

The CLI accepts command-line arguments:

```bash
memorg --help
```

For the MCP server:

```bash
memorg-mcp --host 127.0.0.1 --port 3000 --db-path ./data/memorg.db --log-level DEBUG
```
