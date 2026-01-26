from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid

class EntityType(Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    EVENT = "event"
    OTHER = "other"

class SearchScope(Enum):
    SESSION = "session"
    CONVERSATION = "conversation"
    TOPIC = "topic"
    ALL = "all"

class MatchType(Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    HYBRID = "hybrid"
    IMPORTANCE = "importance"

@dataclass
class Entity:
    name: str
    type: EntityType
    salience: float
    metadata: Dict[str, Any]

@dataclass
class ParsedContent:
    entities: List[Entity]
    intents: List[str]
    sentiment: Dict[str, float]

@dataclass
class Message:
    raw_content: str
    parsed_content: ParsedContent
    embedding: List[float]

@dataclass
class Exchange:
    id: str
    created_at: datetime
    updated_at: datetime
    user_message: Message
    system_message: Message
    importance_score: float
    embedding: List[float]
    metadata: Dict[str, Any]

@dataclass
class Topic:
    id: str
    created_at: datetime
    updated_at: datetime
    title: str
    summary: str
    exchanges: List[Exchange]
    embedding: List[float]
    key_entities: List[Entity]
    metadata: Dict[str, Any]

@dataclass
class Conversation:
    id: str
    created_at: datetime
    updated_at: datetime
    title: str
    summary: str
    topics: List[Topic]
    embedding: List[float]
    metadata: Dict[str, Any]

@dataclass
class Session:
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: str
    system_config: Dict[str, Any]
    conversations: List[Conversation]
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    entity: Any  # Can be Session, Conversation, Topic, or Exchange
    score: float
    match_type: MatchType 