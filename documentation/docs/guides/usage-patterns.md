# Usage Patterns

This page describes recurring scenarios for Memorg and how its components cooperate to handle them. Use these as a starting point when fitting Memorg into a larger system.

The patterns reference four cooperating components inside `MemorgSystem`:

- **Context Store** (`ContextStore`) — persists sessions/conversations/topics/exchanges and embeddings
- **Context Manager** (`ContextManager`) — prioritisation (`RecencyWeightedStrategy`) and compression (`ExtractiveSummarization`)
- **Retrieval System** (`RetrievalSystem`) — query processing and `MultiFactorScorer` ranking
- **Window Optimizer** (`ContextWindowOptimizer`) — `ProgressiveSummarization` and `TokenOptimizer`

## 1. Extended Multi-Topic Conversation

**Scenario.** A user engages in a long conversation that drifts through multiple subjects over hours or days.

**How Memorg helps.**

- Store each subject as a fresh `Topic` under the same `Conversation`.
- The Context Manager scores recent exchanges higher (`RecencyWeightedStrategy`), so the prompt always leans toward what just happened.
- When the user refers back to an earlier topic ("the timeline we discussed"), `search_context` finds the relevant exchanges via embedding similarity.
- `optimize_context` keeps the assembled prompt under a token budget.

**Sketch.**

```python
topic_a = await system.context_store.create_topic(conv.id, "Project Planning")
await system.add_exchange(topic_a.id, "Let's plan Q1...", "...")

# Subject shifts
topic_b = await system.context_store.create_topic(conv.id, "Technical Requirements")
await system.add_exchange(topic_b.id, "What database?", "...")

# Later — user references prior topic
results = await system.search_context("timeline we discussed", max_results=5)
```

## 2. Information-Dense Technical Support

**Scenario.** A user pastes long error logs and configuration files while troubleshooting.

**How Memorg helps.**

- Long pastes flow into exchanges; `ExtractiveSummarization` compresses verbose content while keeping the salient lines.
- The retrieval pipeline finds prior attempts by error message similarity.
- `optimize_context` keeps logs within the LLM's token budget.

**Sketch.**

```python
await system.add_exchange(topic.id, error_log, "")
await system.add_exchange(topic.id, "Tried X, didn't work", "")

# When the same error reappears later
results = await system.search_context("connection refused on 5432")
```

## 3. Document Analysis Workflow

**Scenario.** An analyst loads a batch of documents and runs queries across them.

**How Memorg helps.** Use the generic memory abstraction (`create_memory_item`) rather than the chat hierarchy.

```python
session = await system.create_session("analyst", {"workflow": "documents"})

for doc in documents:
    await system.create_memory_item(
        content=doc.text,
        item_type="document",
        parent_id=session.id,
        metadata={"source": doc.source},
        tags=doc.tags,
    )

results = await system.search_memory(
    query="customer churn drivers",
    item_types=["document"],
    tags=["q3", "customers"],
    limit=10,
)
```

## 4. Research Notebook

**Scenario.** A researcher accumulates notes, insights, and references over weeks.

**How Memorg helps.** Build a parent/child tree of memory items and rely on tag-based filtering.

```python
session = await system.create_session("researcher", {})

topic = await system.create_memory_item(
    content="AI Ethics Research",
    item_type="topic",
    parent_id=session.id,
    tags=["ai", "ethics"],
)

await system.create_memory_item(
    content="Key insight: transparency is crucial",
    item_type="note",
    parent_id=topic.id,
    tags=["insight", "transparency"],
)

context = await system.get_item_context(topic.id, depth=3, include_siblings=True)
```

## 5. Collaborative Writing/Editing

**Scenario.** A writer drafts and refines a document across multiple sessions and wants the assistant to remember stylistic choices.

**How Memorg helps.**

- Store style decisions as `note` memory items tagged `style`.
- Store draft sections as `document` memory items with `parent_id` set to the project.
- Before each generation, `search_memory(query=..., tags=["style"])` retrieves the conventions to honour.

## 6. Iterative Problem Solving

**Scenario.** Working through a hard problem across many turns, where intermediate hypotheses matter.

**How Memorg helps.**

- Each turn becomes an exchange with an importance score reflecting how relevant it remains to the current topic.
- `RecencyWeightedStrategy` keeps recent hypotheses near the top, while semantic search can still surface a forgotten earlier branch.
- `optimize_context` is invoked before each LLM call to fit the chain of reasoning into the model's window.

## Best Practices Across Patterns

### Organising Information

- One **session per workflow** (a user, a project, an analysis batch).
- One **topic per coherent subject** — switching subjects is cheaper than overloading one topic.
- Consistent **tag vocabulary** — lowercase, hyphenated, project-prefixed.

### Performance

- Call `get_memory_usage` periodically; the `vector_count` and `index_size` are the most informative numbers.
- For ingestion-heavy workloads, batch writes inside a single async task before searching.

### Search

- Use `search_context` for chat history (`Session/Conversation/Topic/Exchange`).
- Use `search_memory` for generic memory items, including documents and notes.
- Combine tags with the query to narrow results: filtering by tag is cheap, while embedding lookups grow with index size.
