# CLI Guide

The `memorg` command is an interactive chat shell built with `rich`. It is implemented in `memorg.cli:MemorgCLI` and uses a fixed user id (`cli_user`), the database `memorg.db` in the current working directory, and the OpenAI chat model `gpt-4o-mini`.

## Starting the CLI

```bash
memorg
```

You'll see the welcome panel:

```
Welcome to Memorg CLI Chat!
Type 'help' for available commands or start chatting.
```

The CLI requires `OPENAI_API_KEY` either in the environment or in a `.env` file in the working directory. Missing key:

```
Please set OPENAI_API_KEY environment variable
```

## Commands

The CLI dispatches on the literal lowercased input. Anything other than a recognised command is treated as a chat message.

### `help`

Print the command list.

```
Available Commands:
- help: Show this help message
- new: Start a new conversation
- search: Search through conversation history
- memory: Show memory usage statistics
- memsearch: Search through all memory (not just conversations)
- addnote: Add a custom note to memory
- exit: Exit the chat
```

### `new`

Calls `system.start_conversation(current_session)` and sets it as the active conversation. The next chat message will auto-create a new `General Discussion` topic inside it.

### `search`

Prompts for a query, then calls `system.search_context(query)`. This runs the hybrid pipeline: embed the query, do a USearch nearest-neighbour lookup, fall back to FTS5 across `sessions/conversations/topics/exchanges`, and finally rank the merged results with `MultiFactorScorer`.

Output is rendered as a `rich` table with columns `Score`, `Type` (the `MatchType` value), and `Content` (truncated to 100 characters).

### `memsearch`

Prompts for a query, then calls `system.search_memory(query)` — the generic memory abstraction. Output includes a `Tags` column.

### `addnote`

Prompts for note content and an optional comma-separated tag list, then calls:

```python
system.create_memory_item(
    content=content,
    item_type="note",
    parent_id=current_session,
    tags=tags,
)
```

Output: `Added note with ID: <uuid>`.

### `memory`

Calls `system.get_memory_usage()` and prints:

- Total Tokens (roughly `len(content) // 4` summed across all stored items)
- Active Items
- Compressed Items
- Vector Count
- Index Size (formatted as B/KB/MB/GB)

### `exit`

Breaks out of the chat loop and returns to the shell.

## Interactive Chat

When the input isn't a command, the CLI:

1. Ensures `current_topic` is set, auto-creating a `General Discussion` topic if needed.
2. Calls `system.search_context(user_input)` to find relevant prior context.
3. Records the user message as an exchange.
4. Calls OpenAI `gpt-4o-mini` with a system prompt, the optimized context (`window_optimizer.optimize_context(..., max_tokens=8000)`), and the user message.
5. Records the AI response as an exchange.
6. Renders the response as Markdown.

```
You: What is the capital of France?

AI: The capital of France is Paris. It's the largest city in France and serves
    as the country's political, economic, and cultural center...
```

A `KeyboardInterrupt` is caught — use `exit` to actually quit.

## Tips

### Effective Searching

- Use specific phrases for better embeddings; FTS5 picks up the literal tokens too.
- Use `search` for chat history and `memsearch` for notes and documents.
- Tag consistently — e.g. always lowercase, hyphenated.

### Managing Topics

- Use `new` to start a new conversation when the subject shifts substantially.
- A single conversation can contain many topics, but the CLI only auto-creates one (`General Discussion`); call the library directly if you need finer-grained topic control.

### Organising with Tags

```
You: addnote
Enter note content: Project deadline is March 15th
Enter tags: project,deadline,march

You: addnote
Enter note content: Budget meeting rescheduled to March 20th
Enter tags: meeting,budget,march

You: memsearch
Enter memory search query: march
```

Both notes are returned because the `march` tag and content match.

## Reading the Database from Code

Anything stored by the CLI is visible to the library:

```python
from memorg import MemorgSystem
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore
from openai import AsyncOpenAI

system = MemorgSystem(
    storage=SQLiteStorageAdapter("memorg.db"),
    vector_store=USearchVectorStore("memorg.db"),
    openai_client=AsyncOpenAI(),
)
results = await system.search_memory("march", tags=["march"])
```
