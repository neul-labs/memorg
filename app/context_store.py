from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Protocol
import uuid
import logging
from app.models import (
    Session, Conversation, Topic, Exchange,
    SearchScope, SearchResult, MatchType, Message, ParsedContent
)
from openai import AsyncOpenAI
from app.storage.storage_adapter import StorageAdapter
from app.vector_store.vector_store import VectorStore

# Configure logger
logger = logging.getLogger(__name__)

class ContextStore:
    """
    A class that manages the storage and retrieval of conversation context, including sessions,
    conversations, topics, and exchanges. It coordinates between persistent storage, vector storage,
    and OpenAI services to maintain and search through conversation history.
    """

    def __init__(self, storage: StorageAdapter, vector_store: VectorStore, openai_client: AsyncOpenAI):
        """
        Initialize the ContextStore with required dependencies.
        
        Args:
            storage: Adapter for persistent storage operations
            vector_store: Service for vector-based similarity search
            openai_client: Client for OpenAI API operations
        """
        self.storage = storage
        self.vector_store = vector_store
        self.openai_client = openai_client
        logger.info("Initialized ContextStore with storage, vector store, and OpenAI client")

    async def create_session(self, user_id: str, config: Dict[str, Any]) -> Session:
        """
        Create a new session for a user with specified configuration.
        
        This method initializes a new conversation session with a unique ID and stores it
        in persistent storage. Sessions serve as top-level containers for conversations.
        
        Args:
            user_id: Identifier for the user
            config: Configuration settings for the session
            
        Returns:
            Session: The newly created session object
        """
        logger.info(f"Creating new session for user_id={user_id}")
        session = Session(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            user_id=user_id,
            system_config=config,
            conversations=[],
            metadata={}
        )
        await self.storage.write("sessions", session.id, session.__dict__)
        logger.info(f"Created session with id={session.id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by its ID.
        
        Args:
            session_id: Unique identifier of the session
            
        Returns:
            Optional[Session]: The session if found, None otherwise
        """
        logger.debug(f"Retrieving session with id={session_id}")
        data = await self.storage.read("sessions", session_id)
        if not data:
            logger.warning(f"Session not found: {session_id}")
            return None
        return Session(**data)

    async def create_conversation(self, session_id: str) -> Conversation:
        """
        Create a new conversation within a session.
        
        This method creates a new conversation, stores it, and updates the parent session
        to include the new conversation. Conversations are the primary containers for
        topic-based discussions.
        
        Args:
            session_id: ID of the parent session
            
        Returns:
            Conversation: The newly created conversation object
        """
        logger.info(f"Creating new conversation for session_id={session_id}")
        conversation = Conversation(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            title="",
            summary="",
            topics=[],
            embedding=[],
            metadata={}
        )
        await self.storage.write("conversations", conversation.id, conversation.__dict__)
        logger.debug(f"Created conversation with id={conversation.id}")
        
        # Update session with new conversation
        session = await self.get_session(session_id)
        if session:
            session.conversations.append(conversation)
            session.updated_at = datetime.now(timezone.utc)
            await self.storage.write("sessions", session_id, session.__dict__)
            logger.debug(f"Updated session {session_id} with new conversation")
        else:
            logger.warning(f"Session {session_id} not found when updating with new conversation")
        
        return conversation

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by its ID.
        
        Args:
            conversation_id: Unique identifier of the conversation
            
        Returns:
            Optional[Conversation]: The conversation if found, None otherwise
        """
        logger.debug(f"Retrieving conversation with id={conversation_id}")
        data = await self.storage.read("conversations", conversation_id)
        if not data:
            logger.warning(f"Conversation not found: {conversation_id}")
            return None
        return Conversation(**data)

    async def create_topic(self, conversation_id: str, title: Optional[str] = None) -> Topic:
        """
        Create a new topic within a conversation.
        
        Topics represent distinct discussion subjects within a conversation. This method
        creates a new topic, stores it, and updates the parent conversation to include
        the new topic.
        
        Args:
            conversation_id: ID of the parent conversation
            title: Optional title for the topic
            
        Returns:
            Topic: The newly created topic object
        """
        logger.info(f"Creating new topic for conversation_id={conversation_id}")
        topic = Topic(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            title=title or "",
            summary="",
            exchanges=[],
            embedding=[],
            key_entities=[],
            metadata={}
        )
        await self.storage.write("topics", topic.id, topic.__dict__)
        logger.debug(f"Created topic with id={topic.id}")
        
        # Update conversation with new topic
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            conversation.topics.append(topic)
            conversation.updated_at = datetime.now(timezone.utc)
            await self.storage.write("conversations", conversation_id, conversation.__dict__)
            logger.debug(f"Updated conversation {conversation_id} with new topic")
        else:
            logger.warning(f"Conversation {conversation_id} not found when updating with new topic")
        
        return topic

    async def add_exchange(self, topic_id: str, user_message: str, system_message: str) -> Exchange:
        """
        Add a new exchange (user-system message pair) to a topic.
        
        This method creates a new exchange with embedded vector representations of the messages,
        stores it in both persistent storage and vector store for semantic search capabilities.
        It also updates the parent topic to include the new exchange.
        
        Args:
            topic_id: ID of the parent topic
            user_message: Message from the user
            system_message: Response from the system
            
        Returns:
            Exchange: The newly created exchange object
        """
        logger.info(f"Adding exchange to topic_id={topic_id}")
        
        # Generate embeddings for messages
        combined_text = f"User: {user_message}\nSystem: {system_message}"
        embedding_response = await self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=combined_text
        )
        embedding = embedding_response.data[0].embedding
        
        # Create message objects with embeddings
        user_msg = Message(
            raw_content=user_message,
            parsed_content=ParsedContent(entities=[], intents=[], sentiment=None),
            embedding=embedding  # Use the same embedding for now
        )
        
        system_msg = Message(
            raw_content=system_message,
            parsed_content=ParsedContent(entities=[], intents=[], sentiment=None),
            embedding=embedding  # Use the same embedding for now
        )
        
        # Create exchange with proper message objects
        exchange = Exchange(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            user_message=user_msg,
            system_message=system_msg,
            importance_score=0.0,
            embedding=embedding,
            metadata={}
        )
        
        # Store in SQLite
        await self.storage.write("exchanges", exchange.id, exchange.__dict__)
        logger.debug(f"Created exchange with id={exchange.id}")
        
        # Update topic with new exchange
        topic = await self.get_topic(topic_id)
        if topic:
            topic.exchanges.append(exchange)
            topic.updated_at = datetime.now(timezone.utc)
            await self.storage.write("topics", topic_id, topic.__dict__)
            logger.debug(f"Updated topic {topic_id} with new exchange")
        else:
            logger.warning(f"Topic {topic_id} not found when updating with new exchange")
        
        # Add to vector store
        await self.vector_store.add_vector(
            exchange.id,
            embedding,
            metadata={
                "text_content": combined_text,
                "type": "exchange",
                "topic_id": topic_id
            }
        )
        logger.debug(f"Added exchange {exchange.id} to vector store")
        
        return exchange

    async def get_topic(self, topic_id: str) -> Optional[Topic]:
        """
        Retrieve a topic by its ID.
        
        Args:
            topic_id: Unique identifier of the topic
            
        Returns:
            Optional[Topic]: The topic if found, None otherwise
        """
        logger.debug(f"Retrieving topic with id={topic_id}")
        data = await self.storage.read("topics", topic_id)
        if not data:
            logger.warning(f"Topic not found: {topic_id}")
            return None
        return Topic(**data)

    async def search_by_keyword(self, query: str, scope: SearchScope) -> List[SearchResult]:
        """
        Search for content using keyword-based matching.
        
        This method performs a text-based search across the specified scope (sessions,
        conversations, topics, or exchanges) using keyword matching.
        
        Args:
            query: Search query string
            scope: Scope of the search (ALL, SESSIONS, CONVERSATIONS, etc.)
            
        Returns:
            List[SearchResult]: List of matching results with relevance scores
        """
        logger.info(f"Performing keyword search with query='{query}', scope={scope}")
        # Implement keyword search based on scope
        results = []
        if scope == SearchScope.ALL:
            # Search across all collections
            for collection in ["sessions", "conversations", "topics", "exchanges"]:
                logger.debug(f"Searching in collection: {collection}")
                items = await self.storage.query(collection, {"$text": {"$search": query}})
                logger.debug(f"Found {len(items)} items in {collection}")
                for item in items:
                    results.append(SearchResult(
                        entity=item,
                        score=item.get("score", 0.0),
                        match_type=MatchType.KEYWORD
                    ))
        logger.info(f"Keyword search completed with {len(results)} results")
        return results

    async def search_by_semantic(self, embedding: List[float], scope: SearchScope) -> List[SearchResult]:
        """
        Search for content using semantic similarity.
        
        This method performs a vector-based similarity search using the provided embedding
        to find semantically similar content within the specified scope. It leverages the
        vector store for efficient similarity search.
        
        Args:
            embedding: Vector representation of the search query
            scope: Scope of the search (ALL, SESSIONS, CONVERSATIONS, etc.)
            
        Returns:
            List[SearchResult]: List of semantically similar results with similarity scores
        """
        logger.info(f"Performing semantic search with scope={scope}")
        # Implement semantic search using vector store
        results = []
        vector_results = await self.vector_store.search_nearest(embedding, limit=10)
        logger.debug(f"Found {len(vector_results)} nearest vectors")
        
        for result in vector_results:
            entity_id = result["id"]
            # Fetch full entity based on scope
            if scope == SearchScope.ALL:
                for collection in ["sessions", "conversations", "topics", "exchanges"]:
                    entity = await self.storage.read(collection, entity_id)
                    if entity:
                        results.append(SearchResult(
                            entity=entity,
                            score=result["score"],
                            match_type=MatchType.SEMANTIC
                        ))
                        logger.debug(f"Found matching entity in {collection}: {entity_id}")
                        break
        
        logger.info(f"Semantic search completed with {len(results)} results")
        return results