"""
Centralized error code registry and structured exception hierarchy for AXIOM.

Error Code Format: MODULE-XXX
- BUS-XXX: Event bus errors
- STATE-XXX: State management errors
- POLICY-XXX: Policy engine errors
- VA-XXX: Virtual assistant errors
- CONFIG-XXX: Configuration errors
- SYSTEM-XXX: System-level errors
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import traceback


class ErrorCode(Enum):
    """Centralized error codes with module prefixes."""
    
    # Event Bus Errors (BUS-XXX)
    BUS_EVENT_DELIVERY_FAILED = "BUS-001"
    BUS_INVALID_EVENT_TYPE = "BUS-002"
    BUS_UNREGISTERED_PUBLISHER = "BUS-003"
    BUS_QUEUE_FULL = "BUS-004"
    BUS_SUBSCRIBER_ERROR = "BUS-005"
    BUS_INITIALIZATION_FAILED = "BUS-006"
    
    # State Management Errors (STATE-XXX)
    STATE_DATABASE_CONNECTION_FAILED = "STATE-001"
    STATE_QUERY_FAILED = "STATE-002"
    STATE_MIGRATION_FAILED = "STATE-003"
    STATE_TRANSACTION_FAILED = "STATE-004"
    STATE_INVALID_MODEL = "STATE-005"
    STATE_INTEGRITY_ERROR = "STATE-006"
    
    # Policy Engine Errors (POLICY-XXX)
    POLICY_VALIDATION_FAILED = "POLICY-001"
    POLICY_NOT_FOUND = "POLICY-002"
    POLICY_REGISTRATION_FAILED = "POLICY-003"
    POLICY_EVALUATION_ERROR = "POLICY-004"
    POLICY_BLOCKED_CONTENT = "POLICY-005"
    POLICY_SQL_INJECTION_DETECTED = "POLICY-006"
    POLICY_INVALID_PATH = "POLICY-007"
    
    # Virtual Assistant Errors (VA-XXX)
    VA_INTENT_DETECTION_FAILED = "VA-001"
    VA_RESPONSE_GENERATION_FAILED = "VA-002"
    VA_DIALOG_MANAGER_ERROR = "VA-003"
    VA_PIPELINE_ERROR = "VA-004"
    VA_CONTEXT_ERROR = "VA-005"
    
    # Configuration Errors (CONFIG-XXX)
    CONFIG_LOAD_FAILED = "CONFIG-001"
    CONFIG_INVALID_VALUE = "CONFIG-002"
    CONFIG_MISSING_REQUIRED = "CONFIG-003"
    CONFIG_PARSE_ERROR = "CONFIG-004"
    CONFIG_FILE_NOT_FOUND = "CONFIG-005"
    
    # System Errors (SYSTEM-XXX)
    SYSTEM_INITIALIZATION_FAILED = "SYSTEM-001"
    SYSTEM_SHUTDOWN_FAILED = "SYSTEM-002"
    SYSTEM_HEALTH_CHECK_FAILED = "SYSTEM-003"
    SYSTEM_RESOURCE_EXHAUSTED = "SYSTEM-004"
    SYSTEM_TIMEOUT = "SYSTEM-005"


class AxiomError(Exception):
    """
    Base exception class for all AXIOM errors with structured information.
    
    Attributes:
        error_code: Standardized error code (e.g., "BUS-001")
        message: Human-readable error message
        details: Additional context and technical details
        timestamp: When the error occurred
        context: Execution context (module, function, etc.)
        user_message: Simplified message for end users
        retry_allowed: Whether this error can be automatically retried
    """
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        retry_allowed: bool = False,
        context: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code.value
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        self.context = context or {}
        self.user_message = user_message or self._generate_user_message()
        self.retry_allowed = retry_allowed
        self.traceback = traceback.format_exc()
        
        super().__init__(self.message)
    
    def _generate_user_message(self) -> str:
        """Generate a simplified user-friendly message."""
        prefix = self.error_code.split('-')[0]
        friendly_messages = {
            'BUS': "An internal communication error occurred.",
            'STATE': "There was an issue accessing stored data.",
            'POLICY': "Your request could not be processed due to policy restrictions.",
            'VA': "The assistant encountered an error processing your request.",
            'CONFIG': "There was a configuration problem.",
            'SYSTEM': "A system error occurred."
        }
        return friendly_messages.get(prefix, "An unexpected error occurred.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to structured dictionary for logging."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "context": self.context,
            "retry_allowed": self.retry_allowed,
            "traceback": self.traceback
        }
    
    def to_user_dict(self) -> Dict[str, Any]:
        """Convert error to simplified dictionary for user display."""
        return {
            "error": self.user_message,
            "error_code": self.error_code,
            "timestamp": self.timestamp
        }


# Module-specific exception classes

class EventBusError(AxiomError):
    """Base class for event bus errors."""
    pass


class StateError(AxiomError):
    """Base class for state management errors."""
    pass


class PolicyError(AxiomError):
    """Base class for policy engine errors."""
    pass


class VirtualAssistantError(AxiomError):
    """Base class for virtual assistant errors."""
    pass


class ConfigurationError(AxiomError):
    """Base class for configuration errors."""
    pass


class SystemError(AxiomError):
    """Base class for system-level errors."""
    pass


# Retry configuration
class RetryConfig:
    """Configuration for retry behavior."""
    
    MAX_ATTEMPTS = 3
    BACKOFF_BASE = 1.0  # seconds
    BACKOFF_MULTIPLIER = 2  # exponential: 1s, 2s, 4s
    
    # Error codes that allow automatic retry
    RETRYABLE_ERRORS = {
        ErrorCode.BUS_EVENT_DELIVERY_FAILED,
        ErrorCode.BUS_QUEUE_FULL,
        ErrorCode.STATE_DATABASE_CONNECTION_FAILED,
        ErrorCode.STATE_QUERY_FAILED,
        ErrorCode.SYSTEM_TIMEOUT,
        ErrorCode.SYSTEM_RESOURCE_EXHAUSTED
    }
    
    @classmethod
    def is_retryable(cls, error_code: str) -> bool:
        """Check if an error code allows retry."""
        try:
            code = ErrorCode(error_code)
            return code in cls.RETRYABLE_ERRORS
        except ValueError:
            return False
    
    @classmethod
    def get_backoff_time(cls, attempt: int) -> float:
        """Calculate backoff time for given attempt (1-indexed)."""
        return cls.BACKOFF_BASE * (cls.BACKOFF_MULTIPLIER ** (attempt - 1))
