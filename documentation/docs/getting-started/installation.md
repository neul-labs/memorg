# Installation

Memorg targets Python 3.11+ and is published to PyPI as `memorg`.

## From PyPI (Recommended)

```bash
pip install memorg
```

This installs the library along with two console scripts:

| Script | Module | Purpose |
|--------|--------|---------|
| `memorg` | `memorg.cli_entry:main` | Interactive chat CLI |
| `memorg-mcp` | `memorg.mcp.cli:main` | MCP server for Claude Desktop, etc. |

## From Source (Development)

Memorg is managed with Poetry. To work on it locally:

```bash
git clone https://github.com/neul-labs/memorg.git
cd memorg
poetry install
```

Run the test suite:

```bash
poetry run pytest
```

Tests use `pytest-asyncio` in `auto` mode and live under `tests/`.

## Verify Installation

CLI:

```bash
memorg
```

You should see the `Welcome to Memorg CLI Chat!` panel. Type `exit` to quit.

Python:

```python
from memorg import MemorgSystem
print(MemorgSystem)
```

Top-level re-exports (from `memorg/__init__.py`):

- `MemorgSystem`
- `ContextStore`, `ContextManager`, `RetrievalSystem`, `ContextWindowOptimizer`
- `Session`, `Conversation`, `Topic`, `Exchange`, `Entity`

## Dependencies

The runtime dependencies pinned in `pyproject.toml`:

| Package | Purpose |
|---------|---------|
| `openai` (^1.79) | Embeddings + chat completions |
| `rich` (^14) | Terminal output for the CLI |
| `tiktoken` (^0.9) | Token counting in the window optimizer |
| `aiosqlite` (^0.21) | Async SQLite I/O |
| `numpy` (^2.2) | Vector arithmetic |
| `usearch` (^2.17) | On-disk vector index |
| `python-dotenv` (^1.1) | Loads `.env` for the CLI and MCP server |
| `fastmcp` (^0.1) | MCP server implementation |

## Optional: Documentation Dependencies

To build this documentation site locally:

```bash
poetry install --with docs
poetry run mkdocs serve -f documentation/mkdocs.yml
```

The `docs` group pins `mkdocs ^1.5` and `mkdocs-material ^9.5`.

## Environment Setup

Memorg expects `OPENAI_API_KEY` to be available — either exported or loaded from a `.env` file in the working directory (`python-dotenv` is loaded by the CLI and the MCP server at startup).

=== "Linux/macOS"
    ```bash
    export OPENAI_API_KEY="sk-..."
    ```

=== "Windows (PowerShell)"
    ```powershell
    $env:OPENAI_API_KEY="sk-..."
    ```

=== ".env file"
    ```
    OPENAI_API_KEY=sk-...
    ```

If the key is missing, the CLI prints `Please set OPENAI_API_KEY environment variable` and exits.
