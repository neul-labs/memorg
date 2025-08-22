# Memorg: Hierarchical Context Management System

## Why Memorg?

Large Language Models (LLMs) have revolutionized how we interact with AI, but they face fundamental limitations in managing context over extended conversations or complex workflows. As conversations grow longer or tasks become more intricate, LLMs struggle with:

- **Context Window Limits**: Most LLMs have finite context windows that fill up quickly with lengthy conversations
- **Information Loss**: Important details from earlier in a conversation can be forgotten as new information is added
- **Irrelevant Information**: Without intelligent filtering, LLMs process all context equally, leading to inefficiency
- **Memory Fragmentation**: Related information gets scattered across different parts of a conversation without proper organization

Memorg addresses these challenges by providing a sophisticated hierarchical context management system that acts as an external memory layer for LLMs. It intelligently stores, organizes, retrieves, and optimizes contextual information, allowing LLMs to maintain coherent, long-term interactions while staying within token limits.

Think of Memorg as a "smart memory manager" for LLMs - it decides what information is important to keep, how to organize it for efficient retrieval, and how to present it optimally to the model.

## What is Memorg?

Memorg is a sophisticated context management system designed to enhance the capabilities of Large Language Models (LLMs) by providing efficient context management, retrieval, and optimization. It serves as an external memory layer that helps LLMs maintain context over extended interactions, manage information hierarchically, and optimize token usage for better performance.

Originally designed for chat-based interactions, Memorg has evolved to support a wide range of workflows beyond conversation, including document analysis, research, content creation, and more.

Memorg can be used both as a **Python library** for integration into your applications and as a **command-line interface (CLI)** for standalone use.

## Features

- **Hierarchical Context Storage**: Organizes information in a Session → Conversation → Topic → Exchange hierarchy
- **Intelligent Context Management**: Prioritizes and compresses information based on relevance and importance
- **Efficient Retrieval**: Combines keyword, semantic, and temporal search capabilities
- **Context Window Optimization**: Manages token usage and creates optimized prompts
- **Working Memory Management**: Efficiently allocates and manages token budgets
- **Generic Memory Abstraction**: Use memory management capabilities across different workflows, not just chat
- **Flexible Tagging System**: Organize and search memory items using custom tags
- **Dual Interface**: Available as both a Python library and a standalone CLI

## Architecture Overview

Memorg follows a modular architecture designed for extensibility and efficiency:

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Main System   │────│  Context Store   │────│   SQLite Storage   │
└─────────────────┘    └──────────────────┘    └────────────────────┘
                              │                         │
                              ▼                         ▼
                   ┌──────────────────┐    ┌────────────────────┐
                   │ Vector Store     │    │   USearch Index    │
                   └──────────────────┘    └────────────────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │ OpenAI Client    │
                   └──────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│ Context Manager │    │ Retrieval System │    │ Window Optimizer   │
└─────────────────┘    └──────────────────┘    └────────────────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │ Memory Abstraction│
                   └──────────────────┘

```

- **Context Store**: Manages the hierarchical data structure (Session → Conversation → Topic → Exchange)
- **Storage Layer**: Uses SQLite for structured data and USearch for vector embeddings
- **Context Manager**: Handles prioritization, compression, and working memory allocation
- **Retrieval System**: Provides intelligent search capabilities across different dimensions
- **Window Optimizer**: Ensures efficient token usage and prompt construction
- **Memory Abstraction**: Generic interface for using memory capabilities across different workflows

## Installation

Install Memorg using pip:

```bash
pip install memorg
```

Or install from source using Poetry:

```bash
git clone https://github.com/skelf-research/memorg.git
cd memorg
poetry install
```

## Quick Start

### As a Python Library

Memorg can be easily integrated into your Python projects:

```python
from app.main import MemorgSystem
from app.storage.sqlite_storage import SQLiteStorageAdapter
from app.vector_store.usearch_vector_store import USearchVectorStore
from openai import AsyncOpenAI

# Initialize the system
storage = SQLiteStorageAdapter("memorg.db")
vector_store = USearchVectorStore("memorg.db")
openai_client = AsyncOpenAI()
system = MemorgSystem(storage, vector_store, openai_client)

# Start using it!
session = await system.create_session("user123", {"max_tokens": 4096})
```

### As a Command-Line Interface

Memorg also provides a powerful CLI for standalone use:

1. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

2. Run the CLI:
```bash
memorg
```

Or if installed from source:
```bash
poetry run python -m app.cli
```

## Specifications

For detailed specifications, please refer to:
- [Technical Specification](specifications/technical.md) - Core architecture and implementation details
- [Usage Guide](specifications/usage.md) - Detailed usage patterns and examples
- [Analysis](specifications/analysis.md) - System analysis and design decisions

## Use Cases & Benefits

Memorg is particularly valuable for:

### **Long Conversations**
- Maintain context across extended dialogues without losing important details
- Automatically prioritize recent and relevant information
- Prevent context window overflow with intelligent compression

### **Complex Workflows**
- Track multi-step processes with hierarchical organization
- Preserve key decisions and parameters throughout a workflow
- Enable context-aware decision making at each step

### **Research & Analysis**
- Organize findings and insights by topic and relevance
- Quickly retrieve relevant information from large datasets
- Maintain research context across multiple sessions

### **Customer Support**
- Keep conversation history for personalized service
- Escalate complex issues with complete context preservation
- Ensure consistency across support agent interactions

### **Content Creation**
- Manage research and drafts in organized topics
- Track content evolution and key revisions
- Optimize token usage for efficient generation

## Key Benefits

- **Reduced Token Costs**: Intelligent context management minimizes unnecessary token usage
- **Improved Accuracy**: Relevant context is always available when needed
- **Better User Experience**: More coherent and contextually appropriate responses
- **Scalable Memory**: Handle conversations of any length without performance degradation
- **Extensible Design**: Modular architecture allows for custom components and integrations

## Library Usage

Memorg can be used as a library in your Python projects. Here's how to integrate it:

```python
from app.main import MemorgSystem
from app.storage.sqlite_storage import SQLiteStorageAdapter
from app.vector_store.usearch_vector_store import USearchVectorStore
from openai import AsyncOpenAI

async def setup_memorg():
    # Initialize components
    storage = SQLiteStorageAdapter("memorg.db")
    vector_store = USearchVectorStore("memorg.db")
    openai_client = AsyncOpenAI()
    
    # Create system instance
    system = MemorgSystem(storage, vector_store, openai_client)
    
    # Create a session with token budget
    session = await system.create_session("user123", {"max_tokens": 4096})
    
    # Start a conversation
    conversation = await system.start_conversation(session.id)
    
    # Create a topic
    topic = await system.context_store.create_topic(conversation.id, "Project Discussion")
    
    # Add an exchange (interaction)
    exchange = await system.add_exchange(
        topic.id,
        "What are the key features?",
        "The system provides hierarchical storage, intelligent context management, and efficient retrieval."
    )
    
    # Search through context
    results = await system.search_context("key features")
    
    # Monitor memory usage
    memory_usage = await system.get_memory_usage()
    return system, session, conversation, topic

# Generic Memory Usage (for non-chat workflows)
async def document_analysis_workflow():
    # Initialize the same way as above
    storage = SQLiteStorageAdapter("memorg.db")
    vector_store = USearchVectorStore("memorg.db")
    openai_client = AsyncOpenAI()
    system = MemorgSystem(storage, vector_store, openai_client)
    
    # Create a session for document analysis
    session = await system.create_session("analyst_123", {"workflow": "document_analysis"})
    
    # Create custom memory items for documents
    document_item = await system.create_memory_item(
        content="This is a research document about AI advancements.",
        item_type="document",  # Can be any type, not just conversation-related
        parent_id=session.id,
        metadata={"author": "Research Team", "category": "AI"},
        tags=["research", "AI", "document"]
    )
    
    # Search across all memory, not just conversations
    results = await system.search_memory(
        query="AI research",
        item_types=["document"],  # Filter by type
        tags=["research"],        # Filter by tags
        limit=5
    )
    
    return results
```

## CLI Usage

The CLI provides an interactive way to explore and manage your memory system:

```bash
# Start the CLI
memorg
```

Available commands in the CLI:
- `help`: Show available commands
- `new`: Start a new conversation
- `search`: Search through conversation history
- `memsearch`: Search through all memory (documents, notes, etc.)
- `addnote`: Add a custom note to memory with tags
- `memory`: Show memory usage statistics
- `exit`: Exit the chat

Example CLI session:
```bash
$ memorg
Welcome to Memorg CLI Chat!
Type 'help' for available commands or start chatting.

You: help
Available Commands:
- help: Show this help message
- new: Start a new conversation
- search: Search through conversation history
- memsearch: Search through all memory (documents, notes, etc.)
- addnote: Add a custom note to memory with tags
- memory: Show memory usage statistics
- exit: Exit the chat

You: memory
Memory Usage:
Total Tokens: 1,234
Active Items: 50
Compressed Items: 10
Vector Count: 60
Index Size: 2.5 MB

You: search
Enter search query: key features
Score  Type        Content
0.92   SEMANTIC    The system provides hierarchical storage...
0.85   KEYWORD     Intelligent context management and...

You: addnote
Enter note content: Remember to review the quarterly reports
Enter tags (comma-separated, optional): reports,quarterly,review
Added note with ID: 123e4567-e89b-12d3-a456-426614174000

You: memsearch
Enter memory search query: quarterly reports
Score  Type        Content                          Tags
0.95   note        Remember to review the...        reports,quarterly,review
```

## Components

### Context Store

The Context Store manages the hierarchical storage of context data:
- Sessions: Top-level containers for user interactions
- Conversations: Groups of related exchanges
- Topics: Specific subjects within conversations
- Exchanges: Individual message pairs

### Memory Abstraction

The Memory Abstraction provides a generic interface for using memory capabilities across different workflows:
- **Memory Items**: Generic representation of any stored information
- **Memory Store**: Interface for storing and retrieving memory items
- **Memory Manager**: High-level interface for memory operations
- **Flexible Types**: Support for custom item types beyond conversation elements
- **Tagging System**: Organize and filter memory items using tags

### Context Manager

The Context Manager handles:
- Prioritization of information based on recency and importance
- Compression of content while preserving key information
- Working memory allocation and management

### Context Manager

The Context Manager handles:
- Prioritization of information based on recency and importance
- Compression of content while preserving key information
- Working memory allocation and management

### Retrieval System

The Retrieval System provides:
- Query processing with entity recognition
- Multi-factor relevance scoring
- Hybrid search capabilities

### Context Window Optimizer

The Context Window Optimizer:
- Summarizes content while preserving important entities
- Optimizes token usage
- Creates context-aware prompt templates

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- mypy for type checking

Run the formatters:
```bash
poetry run black .
poetry run isort .
poetry run mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Conclusion

Memorg represents a significant step forward in making LLMs more practical for real-world applications that require long-term context management. By providing a robust external memory system, it enables developers to build more sophisticated AI applications that can maintain context over extended interactions while optimizing for performance and cost.

Whether you're building customer support systems, research assistants, content creation tools, or complex workflow automation, Memorg provides the foundation for creating more intelligent and context-aware AI applications.

## Citation

If you use Memorg in your research or project, please cite it as follows:

```bibtex
@software{memorg,
  author = {Dipankar Sarkar},
  title = {Memorg: Hierarchical Context Management System},
  year = {2024},
  url = {https://github.com/skelf-research/memorg},
  note = {A sophisticated context management system for enhancing LLM capabilities}
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.