"""Models for the state store component."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class AlertSeverity(Enum):
    """Severity levels for alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ConversationTurn:
    """Represents a single conversation interaction."""
    session_id: str
    user_input: str
    assistant_response: str
    detected_intent: Optional[Dict[str, Any]]
    processing_time: Optional[int]  # in milliseconds
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def to_db_tuple(self) -> tuple:
        """Convert to database tuple format."""
        return (
            self.session_id,
            self.user_input,
            self.assistant_response,
            str(self.detected_intent) if self.detected_intent else None,
            self.processing_time,
            self.timestamp.isoformat(),
            str(self.metadata) if self.metadata else None
        )

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'ConversationTurn':
        """Create instance from database row."""
        return cls(
            session_id=row['session_id'],
            user_input=row['user_input'],
            assistant_response=row['assistant_response'],
            detected_intent=eval(row['detected_intent']) if row['detected_intent'] else None,
            processing_time=row['processing_time'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            metadata=eval(row['metadata']) if row['metadata'] else None
        )

@dataclass
class SystemEvent:
    """Represents a system event record."""
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    source: str
    correlation_id: Optional[str] = None

    def to_db_tuple(self) -> tuple:
        """Convert to database tuple format."""
        return (
            self.event_type,
            str(self.payload),
            self.timestamp.isoformat(),
            self.source,
            self.correlation_id
        )

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'SystemEvent':
        """Create instance from database row."""
        return cls(
            event_type=row['event_type'],
            payload=eval(row['payload']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            source=row['source'],
            correlation_id=row['correlation_id']
        )

@dataclass
class Alert:
    """Represents a system alert."""
    alert_type: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_db_tuple(self) -> tuple:
        """Convert to database tuple format."""
        return (
            self.alert_type,
            self.severity.value,
            self.message,
            self.timestamp.isoformat(),
            self.resolved_at.isoformat() if self.resolved_at else None,
            str(self.metadata) if self.metadata else None
        )

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Alert':
        """Create instance from database row."""
        return cls(
            alert_type=row['alert_type'],
            severity=AlertSeverity(row['severity']),
            message=row['message'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            resolved_at=datetime.fromisoformat(row['resolved_at']) if row['resolved_at'] else None,
            metadata=eval(row['metadata']) if row['metadata'] else None
        )