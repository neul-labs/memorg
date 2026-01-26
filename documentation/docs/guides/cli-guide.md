# CLI Guide

Complete guide to the Memorg command-line interface.

## Starting the CLI

```bash
memorg
```

You'll see the welcome message:

```
Welcome to Memorg CLI Chat!
Type 'help' for available commands or start chatting.
```

## Commands

### help

Display all available commands:

```
You: help

Available Commands:
- help: Show this help message
- new: Start a new conversation
- search: Search through conversation history
- memsearch: Search through all memory
- addnote: Add a custom note to memory
- memory: Show memory usage statistics
- exit: Exit the chat
```

### new

Start a new conversation within the current session:

```
You: new
Started new conversation: 123e4567-e89b-12d3-a456-426614174000
```

### search

Search through your conversation history:

```
You: search
Enter search query: context management

Score  Type        Content
0.95   SEMANTIC    The system provides hierarchical context management...
0.87   KEYWORD     Context management features include...
```

### memsearch

Search across all memory items (not just conversations):

```
You: memsearch
Enter memory search query: quarterly reports

Score  Type        Content                              Tags
0.95   note        Remember to review the...            reports,quarterly,review
0.82   document    Q3 financial summary...              finance,q3
```

### addnote

Add a custom note to memory with optional tags:

```
You: addnote
Enter note content: Important meeting tomorrow at 10am
Enter tags (comma-separated, optional): meeting,reminder
Added note with ID: 456e7890-...
```

### memory

View current memory usage statistics:

```
You: memory

Memory Usage:
Total Tokens: 2,456
Active Items: 45
Compressed Items: 12
Vector Count: 57
Index Size: 1.23 MB
```

### exit

Exit the CLI:

```
You: exit
```

## Interactive Chat

Any input that isn't a command is treated as a chat message:

```
You: What is the capital of France?

AI: The capital of France is Paris. It's the largest city in France and serves as
the country's political, economic, and cultural center...
```

The CLI automatically:

1. Searches for relevant context from previous conversations
2. Sends the context along with your message to the AI
3. Stores the exchange in memory for future reference

## Tips and Tricks

### Effective Searching

- Use specific keywords for better results
- Combine `search` (conversations) and `memsearch` (all memory) as needed
- Tags help organize and filter notes

### Managing Context

- Use `new` to start fresh topics
- The system automatically prioritizes recent and relevant context
- Check `memory` periodically to understand usage

### Organizing with Tags

When using `addnote`, use consistent tags:

```
You: addnote
Enter note content: Project deadline is March 15th
Enter tags: project,deadline,march

You: addnote
Enter note content: Budget meeting rescheduled to March 20th
Enter tags: meeting,budget,march
```

Then search by tag:

```
You: memsearch
Enter memory search query: march
```
