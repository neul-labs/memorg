import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
import aiosqlite
import numpy as np
from usearch.index import Index
from .vector_store import VectorStore
import logging

logger = logging.getLogger(__name__)

class USearchVectorStore(VectorStore):
    def __init__(self, db_path: str = "memorg.db", vector_dim: int = 1536):
        self.db_path = db_path
        self.vector_dim = vector_dim
        # Use the same name as the db file but with .usearch extension
        db_name = os.path.basename(db_path)
        index_name = os.path.splitext(db_name)[0] + ".usearch"
        self.index_path = os.path.join(os.path.dirname(db_path), index_name)
        self._init_db()
        self._init_usearch()

    def _init_db(self):
        """Initialize the SQLite database with vector metadata table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    string_id TEXT UNIQUE,
                    vector_data BLOB,
                    metadata TEXT,
                    text_content TEXT,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Create index on string_id for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_metadata_string_id 
                ON vector_metadata(string_id)
            """)

    def _init_usearch(self):
        """Initialize the USearch index."""
        try:
            if os.path.exists(self.index_path):
                logger.info(f"Loading existing USearch index from {self.index_path}")
                self.index = Index.restore(self.index_path)
            else:
                logger.info("Creating new USearch index")
                self.index = Index(
                    ndim=self.vector_dim,
                    metric='cos',  # Cosine similarity
                    dtype='f32',   # 32-bit float vectors
                    connectivity=16,  # Graph connectivity
                    expansion_add=128,  # Control recall during indexing
                    expansion_search=64  # Control quality of search
                )
                self._persist_index()
        except Exception as e:
            logger.error(f"Error initializing USearch index: {e}")
            # Create a new index if loading fails
            self.index = Index(
                ndim=self.vector_dim,
                metric='cos',
                dtype='f32',
                connectivity=16,
                expansion_add=128,
                expansion_search=64
            )
            self._persist_index()

    def _persist_index(self):
        """Persist the current index to disk."""
        try:
            logger.info(f"Saving USearch index to {self.index_path}")
            self.index.save(self.index_path)
        except Exception as e:
            logger.error(f"Error saving USearch index: {e}")

    async def add_vector(self, string_id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a vector to both SQLite and USearch."""
        try:
            # Convert vector to numpy array and then to bytes for SQLite storage
            vector_array = np.array(vector, dtype=np.float32)
            vector_bytes = vector_array.tobytes()
            
            async with aiosqlite.connect(self.db_path) as db:
                # First check if the string_id already exists
                async with db.execute(
                    "SELECT id FROM vector_metadata WHERE string_id = ?",
                    (string_id,)
                ) as cursor:
                    existing = await cursor.fetchone()
                    
                if existing:
                    # Update existing vector
                    numeric_id = existing[0]
                    await db.execute(
                        """
                        UPDATE vector_metadata 
                        SET vector_data = ?, metadata = ?, text_content = ?, is_deleted = FALSE, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (vector_bytes, json.dumps(metadata or {}), metadata.get("text_content", "") if metadata else "", numeric_id)
                    )
                    # Remove the old vector from USearch index and add the new one
                    # USearch doesn't allow duplicate keys, so we need to remove first
                    self.index.remove(numeric_id)
                    self.index.add(numeric_id, vector_array)
                else:
                    # Insert new vector
                    cursor = await db.execute(
                        """
                        INSERT INTO vector_metadata 
                        (string_id, vector_data, metadata, text_content)
                        VALUES (?, ?, ?, ?)
                        """,
                        (string_id, vector_bytes, json.dumps(metadata or {}), metadata.get("text_content", "") if metadata else "")
                    )
                    numeric_id = cursor.lastrowid
                    self.index.add(numeric_id, vector_array)
                
                await db.commit()
            
            self._persist_index()  # Save after each addition
            logger.info(f"Added vector with string_id {string_id} (numeric_id: {numeric_id}) to store")
        except Exception as e:
            logger.error(f"Error adding vector: {e}")
            raise

    async def search_nearest(self, vector: List[float], limit: int) -> List[Dict[str, Any]]:
        """Search for nearest vectors using USearch, filtering out deleted items."""
        try:
            # Convert vector to numpy array
            vector_array = np.array(vector, dtype=np.float32)
            
            # Search in USearch
            matches = self.index.search(vector_array, limit * 2)  # Get more results to account for deleted items
            
            # Filter out deleted items and get metadata
            results = []
            # Use sync database access as a workaround for async issues
            with sqlite3.connect(self.db_path) as conn:
                for match in matches:
                    # Convert numpy.uint64 to Python int for proper parameter binding
                    key_as_int = int(match.key)
                    # Check if item is deleted using numeric_id
                    cursor = conn.execute(
                        "SELECT string_id, metadata, text_content FROM vector_metadata WHERE id = ? AND is_deleted = FALSE",
                        (key_as_int,)
                    )
                    row = cursor.fetchone()
                    if row:
                        string_id, metadata, text_content = row
                        results.append({
                            "id": string_id,
                            "score": float(match.distance),
                            "metadata": json.loads(metadata),
                            "text_content": text_content
                        })
                        if len(results) >= limit:
                            break
            
            logger.info(f"Found {len(results)} nearest vectors")
            return results
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []

    async def delete_vector(self, string_id: str) -> None:
        """Soft delete a vector by marking it as deleted in SQLite."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE vector_metadata SET is_deleted = TRUE WHERE string_id = ?",
                (string_id,)
            )
            await db.commit()

    async def reindex(self) -> None:
        """Reindex the USearch index by removing soft-deleted items."""
        # Get all non-deleted vectors from SQLite
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, vector_data FROM vector_metadata WHERE is_deleted = FALSE"
            ) as cursor:
                valid_entries = await cursor.fetchall()
        
        # Create new index
        new_index = Index(
            ndim=self.vector_dim,
            metric='cos',
            dtype='f32',
            connectivity=16,
            expansion_add=128,
            expansion_search=64
        )
        
        # Re-add all valid vectors
        for numeric_id, vector_bytes in valid_entries:
            vector_array = np.frombuffer(vector_bytes, dtype=np.float32)
            new_index.add(numeric_id, vector_array)
        
        # Replace old index with new one
        self.index = new_index
        self._persist_index()

    def save_index(self, path: str = None) -> None:
        """Save the USearch index to disk."""
        if path is None:
            path = self.index_path
        self.index.save(path)

    def load_index(self, path: str = None) -> None:
        """Load the USearch index from disk."""
        if path is None:
            path = self.index_path
        self.index = Index.restore(path)

    async def get_stats(self) -> Dict[str, int]:
        """Get vector store statistics."""
        try:
            # Get total vectors in index
            vector_count = len(self.index)
            
            # Get index size in bytes
            index_size = os.path.getsize(self.index_path) if os.path.exists(self.index_path) else 0
            
            # Get metadata count from SQLite
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT COUNT(*) FROM vector_metadata WHERE is_deleted = FALSE") as cursor:
                    metadata_count = (await cursor.fetchone())[0]
            
            return {
                "vector_count": vector_count,
                "metadata_count": metadata_count,
                "index_size": index_size
            }
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {
                "vector_count": 0,
                "metadata_count": 0,
                "index_size": 0
            } 