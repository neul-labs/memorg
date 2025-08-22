"""
Example demonstrating the new memory abstraction capabilities in Memorg.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.memory.core import MemoryItem, MemoryType, MemoryScope
from datetime import datetime

def demonstrate_memory_types():
    """Demonstrate the different types of memory items."""
    print("=== Memory Types Demo ===")
    
    # Different types of memory items
    types = [
        MemoryType.SESSION,
        MemoryType.CONVERSATION,
        MemoryType.TOPIC,
        MemoryType.EXCHANGE,
        MemoryType.DOCUMENT,
        MemoryType.ENTITY,
        MemoryType.CUSTOM
    ]
    
    for mem_type in types:
        print(f"- {mem_type.value}")

def demonstrate_memory_scopes():
    """Demonstrate the different memory scopes."""
    print("\n=== Memory Scopes Demo ===")
    
    # Different scopes for memory operations
    scopes = [
        MemoryScope.GLOBAL,
        MemoryScope.SESSION,
        MemoryScope.CONVERSATION,
        MemoryScope.TOPIC,
        MemoryScope.CUSTOM
    ]
    
    for scope in scopes:
        print(f"- {scope.value}")

def demonstrate_memory_item():
    """Demonstrate creating and using a MemoryItem."""
    print("\n=== Memory Item Demo ===")
    
    # Create a memory item
    item = MemoryItem(
        id="example-123",
        type=MemoryType.DOCUMENT,
        content="This is an example document for demonstrating Memorg's memory abstraction.",
        metadata={
            "author": "Memorg Team",
            "created_by": "example_script",
            "version": "1.0"
        },
        created_at=datetime.now(),
        updated_at=datetime.now(),
        tags=["example", "demo", "document"]
    )
    
    print(f"Created item:")
    print(f"  ID: {item.id}")
    print(f"  Type: {item.type.value}")
    print(f"  Content: {item.content}")
    print(f"  Tags: {item.tags}")
    print(f"  Metadata: {item.metadata}")

if __name__ == "__main__":
    demonstrate_memory_types()
    demonstrate_memory_scopes()
    demonstrate_memory_item()
    
    print("\n=== Summary ===")
    print("Memorg's new memory abstraction provides:")
    print("1. Generic memory items that can represent any type of information")
    print("2. Flexible memory scopes for targeted operations")
    print("3. Tag-based organization and filtering")
    print("4. Rich metadata support")
    print("5. Backward compatibility with existing chat-based functionality")
    print("\nThis enables Memorg to be used for document analysis, research workflows,")
    print("content creation, and other AI applications beyond conversation.")