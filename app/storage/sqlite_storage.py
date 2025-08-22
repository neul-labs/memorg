import sqlite3
import json
from typing import Dict, Any, List, Optional
import aiosqlite
from datetime import datetime, timezone
from .storage_adapter import StorageAdapter
from ..models import Session, Conversation, Topic, Exchange, Entity, SearchResult, Message, ParsedContent

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Handle our custom model classes
        if isinstance(obj, (Session, Conversation, Topic, Exchange, Entity, SearchResult, Message, ParsedContent)):
            return obj.__dict__
        return super().default(obj)

class SQLiteStorageAdapter(StorageAdapter):
    def __init__(self, db_path: str = "memorg.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with necessary tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Create main tables
            for collection in ["sessions", "conversations", "topics", "exchanges"]:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {collection} (
                        id TEXT PRIMARY KEY,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create FTS5 virtual tables for full-text search
                conn.execute(f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS {collection}_fts 
                    USING fts5(
                        id,
                        content,
                        data
                    )
                """)
                
                # Create triggers to keep FTS tables in sync
                conn.execute(f"""
                    CREATE TRIGGER IF NOT EXISTS {collection}_ai AFTER INSERT ON {collection}
                    BEGIN
                        INSERT INTO {collection}_fts(id, content, data)
                        VALUES (
                            new.id,
                            json_extract(new.data, '$.content'),
                            new.data
                        );
                    END;
                """)
                
                conn.execute(f"""
                    CREATE TRIGGER IF NOT EXISTS {collection}_ad AFTER DELETE ON {collection}
                    BEGIN
                        DELETE FROM {collection}_fts WHERE id = old.id;
                    END;
                """)
                
                conn.execute(f"""
                    CREATE TRIGGER IF NOT EXISTS {collection}_au AFTER UPDATE ON {collection}
                    BEGIN
                        UPDATE {collection}_fts 
                        SET content = json_extract(new.data, '$.content'),
                            data = new.data
                        WHERE id = old.id;
                    END;
                """)

    async def write(self, collection: str, id: str, data: Any) -> None:
        """Write data to the specified collection."""
        async with aiosqlite.connect(self.db_path) as db:
            # Convert data to JSON string using custom encoder
            data_json = json.dumps(data, cls=DateTimeEncoder)
            now = datetime.now(timezone.utc).isoformat()
            
            # Check if record exists
            async with db.execute(
                f"SELECT id FROM {collection} WHERE id = ?",
                (id,)
            ) as cursor:
                exists = await cursor.fetchone()
            
            if exists:
                # Update existing record
                await db.execute(
                    f"UPDATE {collection} SET data = ?, updated_at = ? WHERE id = ?",
                    (data_json, now, id)
                )
            else:
                # Insert new record
                await db.execute(
                    f"INSERT INTO {collection} (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (id, data_json, now, now)
                )
            
            await db.commit()

    async def read(self, collection: str, id: str) -> Optional[Any]:
        """Read data from the specified collection by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"SELECT data FROM {collection} WHERE id = ?",
                (id,)
            ) as cursor:
                row = await cursor.fetchone()
                
            if row:
                return json.loads(row[0])
            return None

    async def query(self, collection: str, filter: Dict[str, Any]) -> List[Any]:
        """Query data from the specified collection with optional fulltext search."""
        async with aiosqlite.connect(self.db_path) as db:
            if "$text" in filter:
                # Perform fulltext search
                search_query = filter["$text"]["$search"]
                # Escape special characters and format for FTS5
                search_query = search_query.replace('"', '""').replace("'", "''")
                search_query = f'"{search_query}"'  # Wrap in quotes for exact phrase matching
                
                async with db.execute(
                    f"""
                    SELECT data FROM {collection}_fts 
                    WHERE {collection}_fts MATCH ?
                    ORDER BY rank
                    """,
                    (search_query,)
                ) as cursor:
                    rows = await cursor.fetchall()
            else:
                # Regular query
                conditions = []
                params = []
                for key, value in filter.items():
                    conditions.append(f"json_extract(data, '$.{key}') = ?")
                    params.append(json.dumps(value))
                
                query = f"SELECT data FROM {collection}"
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
            
            return [json.loads(row[0]) for row in rows]

    async def delete(self, collection: str, id: str) -> None:
        """Delete data from the specified collection."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"DELETE FROM {collection} WHERE id = ?",
                (id,)
            )
            await db.commit()

    async def get_stats(self) -> Dict[str, int]:
        """Get storage statistics."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                stats = {
                    "active_items": 0,
                    "compressed_items": 0
                }
                
                # Count items in each collection
                for collection in ["sessions", "conversations", "topics", "exchanges"]:
                    async with db.execute(f"SELECT COUNT(*) FROM {collection}") as cursor:
                        count = (await cursor.fetchone())[0]
                        stats["active_items"] += count
                
                return stats
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "active_items": 0,
                "compressed_items": 0
            } 