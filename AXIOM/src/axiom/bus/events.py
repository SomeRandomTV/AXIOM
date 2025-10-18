from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum, auto
import uuid
import json

class EventType(Enum):
    """Enumeration of supported event types in Phase 1."""
    SYSTEM_START = "system.start"
    SYSTEM_SHUTDOWN = "system.shutdown"
    CONVERSATION_TURN = "conversation.turn"
    STATE_UPDATED = "state.updated"
    
    @classmethod
    def values(cls) -> List[str]:
        """Get all valid event type strings."""
        return [e.value for e in cls]

@dataclass
class Event:
    @staticmethod
    def factory(event_type: str, payload: Dict[str, Any], source: str, correlation_id: Optional[str] = None) -> 'Event':
        """
        Factory method to create an Event with a specific correlation ID (optional).
        Args:
            event_type: The type of event (must be in EventType.values())
            payload: The event payload dictionary
            source: The event source string
            correlation_id: Optional correlation ID (if not provided, a new UUID is generated)
        Returns:
            Event instance
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        return Event(
            event_type=event_type,
            payload=payload,
            source=source,
            correlation_id=correlation_id
        )

    @staticmethod
    def correlate(event: 'Event', new_payload: Optional[Dict[str, Any]] = None, new_type: Optional[str] = None, new_source: Optional[str] = None) -> 'Event':
        """
        Create a new event correlated to an existing event (same correlation_id).
        Args:
            event: The original event to correlate with
            new_payload: Optional new payload (defaults to original)
            new_type: Optional new event type (defaults to original)
            new_source: Optional new source (defaults to original)
        Returns:
            Event instance with same correlation_id
        """
        return Event(
            event_type=new_type or event.event_type,
            payload=new_payload if new_payload is not None else event.payload,
            source=new_source or event.source,
            correlation_id=event.correlation_id
        )
    """Base event class for the event bus system."""
    event_type: str
    payload: Dict[str, Any]
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate event after initialization."""
        if self.event_type not in EventType.values():
            raise ValueError(f"Invalid event type: {self.event_type}")
        
        if not isinstance(self.payload, dict):
            raise TypeError("Payload must be a dictionary")
            
        if not self.source:
            raise ValueError("Source cannot be empty")

    def __str__(self) -> str:
        return f"{self.event_type} from {self.source} at {self.timestamp}"
    
    def to_json(self) -> str:
        """Serialize event to JSON string."""
        return json.dumps({
            "event_type": self.event_type,
            "payload": self.payload,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Create event from JSON string."""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class SystemStartEvent(Event):
    """Event emitted when the system starts."""
    def __init__(self, source: str, version: str, configuration: Dict[str, Any]):
        super().__init__(
            event_type=EventType.SYSTEM_START.value,
            source=source,
            payload={
                "version": version,
                "configuration": configuration,
                "components": []  # List of initialized components
            }
        )

@dataclass
class SystemShutdownEvent(Event):
    """Event emitted when the system is shutting down."""
    def __init__(self, source: str, reason: str, graceful: bool = True):
        super().__init__(
            event_type=EventType.SYSTEM_SHUTDOWN.value,
            source=source,
            payload={
                "reason": reason,
                "graceful": graceful
            }
        )

@dataclass
class ConversationTurnEvent(Event):
    """Event emitted for each conversation interaction."""
    def __init__(self, source: str, session_id: str, user_input: str, 
                 assistant_response: str, intent: Optional[Dict[str, Any]] = None,
                 processing_time: Optional[float] = None):
        super().__init__(
            event_type=EventType.CONVERSATION_TURN.value,
            source=source,
            payload={
                "session_id": session_id,
                "user_input": user_input,
                "assistant_response": assistant_response,
                "intent": intent,
                "processing_time": processing_time
            }
        )

@dataclass
class StateUpdatedEvent(Event):
    """Event emitted when system state is modified."""
    def __init__(self, source: str, changes: Dict[str, Any], 
                 entity_type: str, entity_id: str):
        super().__init__(
            event_type=EventType.STATE_UPDATED.value,
            source=source,
            payload={
                "changes": changes,
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        )
