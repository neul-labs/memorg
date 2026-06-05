# Configuration

Memorg has very few required knobs: an OpenAI key and a database path. Everything else is wired in code when constructing `MemorgSystem` or its component strategies.

## Environment Variables

| Variable | Required | Read by | Notes |
|----------|----------|---------|-------|
| `OPENAI_API_KEY` | Yes | CLI, MCP server | The CLI loads `.env` via `python-dotenv`; exits with a message if missing. |

The CLI loads `.env` at import time (`from dotenv import load_dotenv; load_dotenv()`), so any variables defined there are picked up automatically.

```
# .env
OPENAI_API_KEY=sk-...
```

If you are embedding Memorg as a library, the OpenAI key is whatever you pass to `AsyncOpenAI(...)`. The library itself does not read environment variables.

## Database Paths

The two storage backends share a base path.

```python
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore

storage = SQLiteStorageAdapter("memorg.db")
vector_store = USearchVectorStore("memorg.db")
```

- `SQLiteStorageAdapter(db_path)` creates the SQLite file at `db_path` and initializes the four collections (`sessions`, `conversations`, `topics`, `exchanges`) plus FTS5 mirrors.
- `USearchVectorStore(db_path, vector_dim=1536)` uses the same SQLite file for vector metadata, and writes a sibling `.usearch` index alongside it (`memorg.usearch` for `memorg.db`).

In-memory mode is useful for tests:

```python
storage = SQLiteStorageAdapter(":memory:")
```

## Session Configuration

Sessions carry an opaque `system_config` dict that the application can use to record per-session preferences. Memorg itself does not interpret these fields — they are stored as JSON alongside the session.

```python
session = await system.create_session("user123", {
    "max_tokens": 4096,
    "workflow": "chat",
    "preferences": {"language": "en"},
})
```

## Component Overrides

`MemorgSystem.__init__` wires defaults for the four cooperating components. To override them, instantiate the component yourself and use its protocol directly.

### Context Manager

```python
from memorg.context_manager import (
    ContextManager,
    RecencyWeightedStrategy,
    ExtractiveSummarization,
    WorkingMemory,
)

context_manager = ContextManager(
    prioritization_strategy=RecencyWeightedStrategy(),
    compression_strategy=ExtractiveSummarization(openai_client),
    working_memory=WorkingMemory(capacity=8192),  # default in MemorgSystem is 4096
)
```

### Retrieval System

```python
from memorg.retrieval import (
    RetrievalSystem,
    SimpleQueryProcessor,
    MultiFactorScorer,
)

retrieval = RetrievalSystem(
    query_processor=SimpleQueryProcessor(openai_client),
    relevance_scorer=MultiFactorScorer(),
)
```

### Window Optimizer

```python
from memorg.window_optimizer import (
    ContextWindowOptimizer,
    ProgressiveSummarization,
    TokenOptimizer,
)

window_optimizer = ContextWindowOptimizer(
    summarization_strategy=ProgressiveSummarization(openai_client),
    token_optimization_strategy=TokenOptimizer(openai_client=openai_client),
)
```

`MemorgSystem` constructs the above with default strategies; if you need custom ones, build your own `MemorgSystem` subclass or instantiate `ContextStore`, `ContextManager`, etc. directly.

## CLI Flags

The interactive CLI itself does not accept flags beyond standard Python interpreter behaviour — it reads `OPENAI_API_KEY` from the environment and writes to `memorg.db` in the current directory.

The MCP server is fully configurable from the command line:

```bash
memorg-mcp \
  --host 127.0.0.1 \
  --port 3000 \
  --db-path ./data/memorg.db \
  --log-level DEBUG
```

See [memorg-mcp options](../reference/cli.md#memorg-mcp) for the full list.

## Logging

`MemorgSystem` configures Python's `logging` at import-time:

- Level: `INFO`
- Handlers: rotating to `memorg.log` in the working directory **and** stdout

Override before importing `memorg.main` to use your own configuration (for example, in a larger application that already configures logging).

The MCP server CLI also accepts `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`.
