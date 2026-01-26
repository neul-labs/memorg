# Memorg: Hierarchical Context Management System

Memorg is a sophisticated context management system designed to enhance the capabilities of Large Language Models (LLMs) by providing efficient context management, retrieval, and optimization.

## Why Memorg?

Large Language Models face fundamental limitations in managing context over extended conversations or complex workflows:

- **Context Window Limits**: Most LLMs have finite context windows that fill up quickly
- **Information Loss**: Important details from earlier conversations can be forgotten
- **Irrelevant Information**: Without intelligent filtering, LLMs process all context equally
- **Memory Fragmentation**: Related information gets scattered without proper organization

Memorg addresses these challenges by acting as a "smart memory manager" for LLMs - deciding what information is important, how to organize it, and how to present it optimally to the model.

## Key Features

- **Hierarchical Context Storage** - Organizes information in Session > Conversation > Topic > Exchange hierarchy
- **Intelligent Context Management** - Prioritizes and compresses information based on relevance
- **Efficient Retrieval** - Combines keyword, semantic, and temporal search capabilities
- **Context Window Optimization** - Manages token usage and creates optimized prompts
- **Generic Memory Abstraction** - Use memory capabilities across different workflows
- **Flexible Tagging System** - Organize and search memory items using custom tags
- **Dual Interface** - Available as both Python library and CLI

## Quick Links

- [Installation Guide](getting-started/installation.md)
- [Quick Start Tutorial](getting-started/quickstart.md)
- [CLI Reference](reference/cli.md)
- [Architecture Overview](architecture/overview.md)

## Use Cases

### Long Conversations
Maintain context across extended dialogues without losing important details.

### Complex Workflows
Track multi-step processes with hierarchical organization.

### Research & Analysis
Organize findings and insights by topic and relevance.

### Customer Support
Keep conversation history for personalized service.

### Content Creation
Manage research and drafts in organized topics.

## Architecture Overview

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

## Getting Started

```bash
# Install via pip
pip install memorg

# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Run the CLI
memorg
```

See the [Quick Start Guide](getting-started/quickstart.md) for more details.
