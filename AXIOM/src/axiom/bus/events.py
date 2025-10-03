from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class Intent:
    name: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    session_id: str
    user_input: str
    assistant_response: str
    detected_intent: Optional[Intent] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0


@dataclass
class Event:
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    correlation_id: Optional[str] = None
    exit_code: int = field(default=0, init=False)


@dataclass
class SystemStartEvent(Event):
    initiator: str = "system"
    config_version: str = "v1.0"
    message: str = "System startup initiated."

    def __post_init__(self):
        self.event_type = "system.start"
        self.source = self.initiator
        self.payload = {
            "config_version": self.config_version,
            "message": self.message
        }


@dataclass
class SystemShutdownEvent(Event):
    initiator: str = "system"
    config_version: str = "v1.0"
    message: str = "System shutdown initiated."
    forced_shutdown: int = field(default=0, init=False)

    def __post_init__(self):
        self.event_type = "system.shutdown"
        self.source = self.initiator
        self.payload = {
            "config_version": self.config_version,
            "message": self.message,
            "forced_shutdown": self.forced_shutdown
        }


@dataclass
class SystemRestartEvent(Event):
    initiator: str = "system"
    config_version: str = "v1.0"
    message: str = "System restart initiated."

    def __post_init__(self):
        self.event_type = "system.restart"
        self.source = self.initiator
        self.payload = {
            "config_version": self.config_version,
            "message": self.message
        }


@dataclass
class SystemErrorEvent(Event):
    initiator: str = "system"
    config_version: str = "v1.0"
    message: str = "System error."
    error_type: str = "unknown"
    error_message: str = "An unknown error occurred."
    traceback: str = ""

    def __post_init__(self):
        self.event_type = "system.error"
        self.source = self.initiator
        self.payload = {
            "config_version": self.config_version,
            "message": self.message,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "traceback": self.traceback
        }
