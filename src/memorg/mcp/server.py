"""
MCP Server implementation for the Memorg system.
This module exposes the Memorg functionality as an MCP (Model Context Protocol) server.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from fastmcp import FastMCP
from fastmcp.resources import FileResource
from openai import AsyncOpenAI
from dotenv import load_dotenv

from ..main import MemorgSystem
from ..storage.sqlite_storage import SQLiteStorageAdapter
from ..vector_store.usearch_vector_store import USearchVectorStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemorgMCP:
    """MCP Server wrapper for the Memorg system."""
    
    def __init__(self, db_path: str = "memorg.db"):
        """Initialize the Memorg MCP server."""
        self.db_path = db_path
        self.mcp = FastMCP("memorg")
        self.system: Optional[MemorgSystem] = None
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up MCP routes for Memorg functionality."""
        # System operations
        @self.mcp.tool(name="create_session", description="Create a new Memorg session")
        async def create_session(user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
            """Create a new Memorg session"""
            if not self.system:
                await self.initialize_system()
            
            try:
                session = await self.system.create_session(user_id, config)
                return {
                    "session_id": session.id,
                    "created_at": session.created_at.isoformat(),
                    "user_id": session.user_id,
                    "system_config": session.system_config
                }
            except Exception as e:
                logger.error(f"Error creating session: {e}")
                raise
        
        @self.mcp.tool(name="start_conversation", description="Start a new conversation in a session")
        async def start_conversation(session_id: str) -> Dict[str, Any]:
            """Start a new conversation in a session"""
            if not self.system:
                await self.initialize_system()
            
            try:
                conversation = await self.system.start_conversation(session_id)
                return {
                    "conversation_id": conversation.id,
                    "created_at": conversation.created_at.isoformat(),
                    "title": conversation.title,
                    "summary": conversation.summary
                }
            except Exception as e:
                logger.error(f"Error starting conversation: {e}")
                raise
        
        @self.mcp.tool(name="add_exchange", description="Add a new exchange to a topic")
        async def add_exchange(topic_id: str, user_message: str, system_message: str) -> Dict[str, Any]:
            """Add a new exchange to a topic"""
            if not self.system:
                await self.initialize_system()
            
            try:
                exchange = await self.system.add_exchange(topic_id, user_message, system_message)
                return {
                    "exchange_id": exchange.id,
                    "created_at": exchange.created_at.isoformat(),
                    "user_message": exchange.user_message.raw_content,
                    "system_message": exchange.system_message.raw_content,
                    "importance_score": exchange.importance_score
                }
            except Exception as e:
                logger.error(f"Error adding exchange: {e}")
                raise
        
        # Search operations
        @self.mcp.tool(name="search_context", description="Search through conversation history")
        async def search_context(query: str, scope: str = "ALL", max_results: int = 10) -> Dict[str, Any]:
            """Search through conversation history"""
            if not self.system:
                await self.initialize_system()
            
            try:
                from ..models import SearchScope
                search_scope = SearchScope[scope] if scope in SearchScope.__members__ else SearchScope.ALL
                results = await self.system.search_context(query, search_scope, max_results)
                
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "score": result.score,
                        "content": getattr(result.entity, 'content', getattr(result.entity, 'title', str(result.entity))),
                        "type": result.match_type.value
                    })
                
                return {
                    "query": query,
                    "results": formatted_results,
                    "total_results": len(formatted_results)
                }
            except Exception as e:
                logger.error(f"Error searching context: {e}")
                raise
        
        # Memory operations
        @self.mcp.tool(name="get_memory_usage", description="Get current memory usage statistics")
        async def get_memory_usage() -> Dict[str, Any]:
            """Get current memory usage statistics"""
            if not self.system:
                await self.initialize_system()
            
            try:
                usage = await self.system.get_memory_usage()
                return {
                    "total_tokens": usage.get("total_tokens", 0),
                    "active_items": usage.get("active_items", 0),
                    "compressed_items": usage.get("compressed_items", 0),
                    "vector_count": usage.get("vector_count", 0),
                    "index_size": usage.get("index_size", 0)
                }
            except Exception as e:
                logger.error(f"Error getting memory usage: {e}")
                raise
        
        # Optimization operations
        @self.mcp.tool(name="optimize_context", description="Optimize context for token efficiency")
        async def optimize_context(content: str, max_tokens: int) -> Dict[str, Any]:
            """Optimize context for token efficiency"""
            if not self.system:
                await self.initialize_system()
            
            try:
                # Create empty entities list for optimization
                entities = []
                result = await self.system.optimize_context(content, entities, max_tokens)
                return {
                    "optimized_content": result,
                    "original_length": len(content),
                    "optimized_length": len(result) if isinstance(result, str) else 0
                }
            except Exception as e:
                logger.error(f"Error optimizing context: {e}")
                raise
    
    async def initialize_system(self):
        """Initialize the Memorg system."""
        logger.info("Initializing Memorg system")
        try:
            # Initialize storage components
            storage = SQLiteStorageAdapter(self.db_path)
            vector_store = USearchVectorStore(self.db_path)
            
            # Initialize OpenAI client
            openai_client = AsyncOpenAI()
            
            # Create system instance
            self.system = MemorgSystem(storage, vector_store, openai_client)
            logger.info("Memorg system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Memorg system: {e}")
            raise
    
    
    
    def run(self, host: str = "127.0.0.1", port: int = 3000):
        """Run the MCP server."""
        logger.info(f"Starting Memorg MCP server on {host}:{port}")
        self.mcp.run(host=host, port=port)

# Create a default instance
memorg_mcp = MemorgMCP()

if __name__ == "__main__":
    # Run the server when executed directly
    memorg_mcp.run()