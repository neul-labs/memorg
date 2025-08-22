import pytest
from datetime import datetime, timezone
from app.models import (
    EntityType, SearchScope, MatchType, Entity, ParsedContent, 
    Message, Exchange, Topic, Conversation, Session, SearchResult
)

class TestModels:
    def test_entity_creation(self):
        """Test Entity model creation."""
        entity = Entity(
            name="Test Entity",
            type=EntityType.PERSON,
            salience=0.8,
            metadata={"key": "value"}
        )
        assert entity.name == "Test Entity"
        assert entity.type == EntityType.PERSON
        assert entity.salience == 0.8
        assert entity.metadata == {"key": "value"}

    def test_parsed_content_creation(self):
        """Test ParsedContent model creation."""
        entity = Entity("Test", EntityType.PERSON, 0.5, {})
        parsed_content = ParsedContent(
            entities=[entity],
            intents=["greeting"],
            sentiment={"positive": 0.7}
        )
        assert len(parsed_content.entities) == 1
        assert parsed_content.intents == ["greeting"]
        assert parsed_content.sentiment == {"positive": 0.7}

    def test_message_creation(self):
        """Test Message model creation."""
        entity = Entity("Test", EntityType.PERSON, 0.5, {})
        parsed_content = ParsedContent(
            entities=[entity],
            intents=["greeting"],
            sentiment={"positive": 0.7}
        )
        message = Message(
            raw_content="Hello world",
            parsed_content=parsed_content,
            embedding=[0.1, 0.2, 0.3]
        )
        assert message.raw_content == "Hello world"
        assert message.parsed_content == parsed_content
        assert message.embedding == [0.1, 0.2, 0.3]

    def test_exchange_creation(self):
        """Test Exchange model creation."""
        entity = Entity("Test", EntityType.PERSON, 0.5, {})
        parsed_content = ParsedContent(
            entities=[entity],
            intents=["greeting"],
            sentiment={"positive": 0.7}
        )
        user_message = Message(
            raw_content="Hello",
            parsed_content=parsed_content,
            embedding=[0.1, 0.2, 0.3]
        )
        system_message = Message(
            raw_content="Hi there",
            parsed_content=parsed_content,
            embedding=[0.4, 0.5, 0.6]
        )
        
        exchange = Exchange(
            id="test-exchange-1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            user_message=user_message,
            system_message=system_message,
            importance_score=0.9,
            embedding=[0.7, 0.8, 0.9],
            metadata={"test": "data"}
        )
        
        assert exchange.id == "test-exchange-1"
        assert exchange.user_message == user_message
        assert exchange.system_message == system_message
        assert exchange.importance_score == 0.9
        assert exchange.embedding == [0.7, 0.8, 0.9]
        assert exchange.metadata == {"test": "data"}

    def test_topic_creation(self):
        """Test Topic model creation."""
        entity = Entity("Test", EntityType.PERSON, 0.5, {})
        topic = Topic(
            id="test-topic-1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            title="Test Topic",
            summary="Test summary",
            exchanges=[],
            embedding=[0.1, 0.2, 0.3],
            key_entities=[entity],
            metadata={"test": "data"}
        )
        
        assert topic.id == "test-topic-1"
        assert topic.title == "Test Topic"
        assert topic.summary == "Test summary"
        assert topic.exchanges == []
        assert topic.embedding == [0.1, 0.2, 0.3]
        assert topic.key_entities == [entity]
        assert topic.metadata == {"test": "data"}

    def test_conversation_creation(self):
        """Test Conversation model creation."""
        conversation = Conversation(
            id="test-conversation-1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            title="Test Conversation",
            summary="Test summary",
            topics=[],
            embedding=[0.1, 0.2, 0.3],
            metadata={"test": "data"}
        )
        
        assert conversation.id == "test-conversation-1"
        assert conversation.title == "Test Conversation"
        assert conversation.summary == "Test summary"
        assert conversation.topics == []
        assert conversation.embedding == [0.1, 0.2, 0.3]
        assert conversation.metadata == {"test": "data"}

    def test_session_creation(self):
        """Test Session model creation."""
        session = Session(
            id="test-session-1",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            user_id="test-user",
            system_config={"max_tokens": 4096},
            conversations=[],
            metadata={"test": "data"}
        )
        
        assert session.id == "test-session-1"
        assert session.user_id == "test-user"
        assert session.system_config == {"max_tokens": 4096}
        assert session.conversations == []
        assert session.metadata == {"test": "data"}

    def test_search_result_creation(self):
        """Test SearchResult model creation."""
        entity = Entity("Test", EntityType.PERSON, 0.5, {})
        search_result = SearchResult(
            entity=entity,
            score=0.95,
            match_type=MatchType.SEMANTIC
        )
        
        assert search_result.entity == entity
        assert search_result.score == 0.95
        assert search_result.match_type == MatchType.SEMANTIC

    def test_enums(self):
        """Test enum values."""
        # Test EntityType enum
        assert EntityType.PERSON.value == "person"
        assert EntityType.ORGANIZATION.value == "organization"
        assert EntityType.LOCATION.value == "location"
        assert EntityType.CONCEPT.value == "concept"
        assert EntityType.EVENT.value == "event"
        assert EntityType.OTHER.value == "other"
        
        # Test SearchScope enum
        assert SearchScope.SESSION.value == "session"
        assert SearchScope.CONVERSATION.value == "conversation"
        assert SearchScope.TOPIC.value == "topic"
        assert SearchScope.ALL.value == "all"
        
        # Test MatchType enum
        assert MatchType.KEYWORD.value == "keyword"
        assert MatchType.SEMANTIC.value == "semantic"
        assert MatchType.TEMPORAL.value == "temporal"
        assert MatchType.HYBRID.value == "hybrid"
        assert MatchType.IMPORTANCE.value == "importance"