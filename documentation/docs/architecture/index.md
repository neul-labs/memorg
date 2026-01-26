# Architecture

Understanding Memorg's architecture and design.

## Overview

Memorg is built on a modular architecture designed for extensibility and efficiency. This section covers:

- [Architecture Overview](overview.md) - High-level system design
- [Technical Specification](technical-spec.md) - Detailed implementation
- [Memory Abstraction](memory-abstraction.md) - Generic memory layer

## Core Principles

### Hierarchical Organization

Information is organized in a clear hierarchy:

```
Session
└── Conversation
    └── Topic
        └── Exchange
```

### Separation of Concerns

Each component has a single responsibility:

- **Context Store** - Data persistence and retrieval
- **Context Manager** - Prioritization and compression
- **Retrieval System** - Search and ranking
- **Window Optimizer** - Token management

### Extensibility

The system is designed to be extended:

- Custom storage adapters
- Custom prioritization strategies
- Custom compression algorithms
- Custom search processors

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      MemorgSystem                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Context   │  │  Retrieval  │  │  Context Window     │ │
│  │   Manager   │  │   System    │  │     Optimizer       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │                │                    │             │
│         └────────────────┼────────────────────┘             │
│                          │                                  │
│                          ▼                                  │
│                  ┌─────────────┐                            │
│                  │   Context   │                            │
│                  │    Store    │                            │
│                  └─────────────┘                            │
│                          │                                  │
│           ┌──────────────┴──────────────┐                   │
│           │                             │                   │
│           ▼                             ▼                   │
│   ┌─────────────┐               ┌─────────────┐             │
│   │   SQLite    │               │   USearch   │             │
│   │   Storage   │               │   Vector    │             │
│   └─────────────┘               └─────────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

1. User input received
2. Context Store persists the exchange
3. Vector embeddings generated and stored
4. Context Manager updates importance scores
5. On retrieval, Retrieval System searches both stores
6. Window Optimizer prepares context for LLM
