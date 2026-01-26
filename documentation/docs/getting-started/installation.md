# Installation

## From PyPI (Recommended)

Install Memorg using pip:

```bash
pip install memorg
```

## From Source (Development)

For development or to get the latest changes:

```bash
git clone https://github.com/skelf-research/memorg.git
cd memorg
poetry install
```

## Verify Installation

After installation, verify it works:

```bash
memorg --help
```

Or in Python:

```python
from memorg import MemorgSystem
print("Memorg installed successfully!")
```

## Dependencies

Memorg automatically installs these dependencies:

| Package | Purpose |
|---------|---------|
| `openai` | OpenAI API for embeddings and chat |
| `rich` | Beautiful terminal output |
| `tiktoken` | Token counting |
| `aiosqlite` | Async SQLite storage |
| `numpy` | Numerical operations |
| `usearch` | Vector similarity search |
| `python-dotenv` | Environment variable management |
| `fastmcp` | MCP server support |

## Optional: Documentation Dependencies

To build the documentation locally:

```bash
poetry install --with docs
```

## Environment Setup

Set your OpenAI API key:

=== "Linux/macOS"
    ```bash
    export OPENAI_API_KEY="your-api-key-here"
    ```

=== "Windows"
    ```powershell
    $env:OPENAI_API_KEY="your-api-key-here"
    ```

Or create a `.env` file in your project directory:

```
OPENAI_API_KEY=your-api-key-here
```
