"""
Example usage of the Memorg memory system in different workflows.

This example demonstrates how to use the memory system outside of chat contexts,
such as for document analysis, research workflows, or other AI applications.
"""

import asyncio
from datetime import datetime
from openai import AsyncOpenAI

from memorg.memory.core import MemoryType, MemoryScope
from memorg.memory.store import HierarchicalMemoryStore
from memorg.memory.manager import GenericMemoryManager
from memorg.storage.sqlite_storage import SQLiteStorageAdapter
from memorg.vector_store.usearch_vector_store import USearchVectorStore

async def document_analysis_workflow():
    """Example workflow for analyzing documents using the memory system."""
    print("=== Document Analysis Workflow ===")
    
    # Initialize components
    storage = SQLiteStorageAdapter("memorg.db")
    vector_store = USearchVectorStore("memorg.db")
    openai_client = AsyncOpenAI()  # In practice, you'd pass an API key
    
    # Create memory store and manager
    memory_store = HierarchicalMemoryStore(storage, vector_store, openai_client)
    memory_manager = GenericMemoryManager(memory_store, openai_client)
    
    # Create a session for this workflow
    session = await memory_manager.create_item(
        content="Document Analysis Session",
        item_type=MemoryType.SESSION,
        metadata={
            "user_id": "analyst_123",
            "workflow": "document_analysis",
            "created_by": "example_script"
        }
    )
    print(f"Created session: {session.id}")
    
    # Create a project within the session
    project = await memory_manager.create_item(
        content="Q3 Financial Analysis",
        item_type=MemoryType.CONVERSATION,
        parent_id=session.id,
        metadata={
            "title": "Q3 Financial Analysis",
            "description": "Analysis of Q3 financial documents"
        },
        tags=["finance", "analysis", "q3"]
    )
    print(f"Created project: {project.id}")
    
    # Add some documents to analyze
    doc1 = await memory_manager.create_item(
        content="Company revenue increased by 15% compared to Q2, driven by strong performance in the European market.",
        item_type=MemoryType.DOCUMENT,
        parent_id=project.id,
        metadata={
            "source": "q3_report.pdf",
            "page": 5
        },
        tags=["revenue", "growth", "europe"]
    )
    
    doc2 = await memory_manager.create_item(
        content="Operating expenses rose by 8% due to increased marketing spend and new office locations.",
        item_type=MemoryType.DOCUMENT,
        parent_id=project.id,
        metadata={
            "source": "q3_report.pdf",
            "page": 7
        },
        tags=["expenses", "marketing", "office"]
    )
    
    doc3 = await memory_manager.create_item(
        content="Customer satisfaction scores improved to 4.7/5, up from 4.3 in Q2.",
        item_type=MemoryType.DOCUMENT,
        parent_id=project.id,
        metadata={
            "source": "customer_survey.pdf",
            "page": 3
        },
        tags=["customers", "satisfaction", "survey"]
    )
    
    print(f"Added documents: {doc1.id}, {doc2.id}, {doc3.id}")
    
    # Search for relevant information
    results = await memory_manager.search(
        query="revenue growth",
        scope=MemoryScope.SESSION,
        tags=["finance"],
        limit=5
    )
    
    print("\nSearch results for 'revenue growth':")
    for result in results:
        print(f"- {result.item.content} (score: {result.score:.2f})")
    
    # Add tags to an item
    await memory_manager.add_tags(doc1.id, ["positive", "financial_performance"])
    print(f"\nAdded tags to document {doc1.id}")
    
    # Get context for a specific item
    context = await memory_manager.get_context(doc1.id, depth=2)
    print(f"\nContext for document {doc1.id}:")
    for item in context:
        print(f"- {item.type.value}: {item.content[:50]}...")

async def research_workflow():
    """Example workflow for academic research."""
    print("\n=== Research Workflow ===")
    
    # Initialize components
    storage = SQLiteStorageAdapter("memorg.db")
    vector_store = USearchVectorStore("memorg.db")
    openai_client = AsyncOpenAI()  # In practice, you'd pass an API key
    
    # Create memory store and manager
    memory_store = HierarchicalMemoryStore(storage, vector_store, openai_client)
    memory_manager = GenericMemoryManager(memory_store, openai_client)
    
    # Create a research session
    session = await memory_manager.create_item(
        content="Machine Learning Research",
        item_type=MemoryType.SESSION,
        metadata={
            "user_id": "researcher_456",
            "domain": "machine_learning",
            "institution": "Example University"
        }
    )
    print(f"Created research session: {session.id}")
    
    # Create a research topic
    topic = await memory_manager.create_item(
        content="Transformer Architecture Improvements",
        item_type=MemoryType.TOPIC,
        parent_id=session.id,
        metadata={
            "focus": "attention mechanisms",
            "keywords": ["transformers", "attention", "efficiency"]
        },
        tags=["ml", "nlp", "transformers"]
    )
    print(f"Created research topic: {topic.id}")
    
    # Add research notes
    note1 = await memory_manager.create_item(
        content="Attention is All You Need paper introduced the transformer architecture in 2017.",
        item_type=MemoryType.DOCUMENT,
        parent_id=topic.id,
        tags=["foundational", "paper"]
    )
    
    note2 = await memory_manager.create_item(
        content="Recent work has focused on making transformers more efficient through sparse attention.",
        item_type=MemoryType.DOCUMENT,
        parent_id=topic.id,
        tags=["efficiency", "sparse_attention"]
    )
    
    print(f"Added research notes: {note1.id}, {note2.id}")
    
    # Search for related work
    results = await memory_manager.search(
        query="transformer efficiency",
        scope=MemoryScope.GLOBAL,
        item_types=[MemoryType.DOCUMENT],
        limit=3
    )
    
    print("\nSearch results for 'transformer efficiency':")
    for result in results:
        print(f"- {result.item.content} (score: {result.score:.2f})")

if __name__ == "__main__":
    # Run the examples
    asyncio.run(document_analysis_workflow())
    asyncio.run(research_workflow())