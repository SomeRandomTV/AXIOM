"""Custom exceptions for the event bus system."""

class EventBusException(Exception):
    """Base exception for event bus related errors."""
    pass

class InvalidEventTypeError(EventBusException):
    """Raised when an invalid event type is used."""
    pass

class UnregisteredPublisherError(EventBusException):
    """Raised when an unregistered publisher tries to publish events."""
    pass

class EventDeliveryError(EventBusException):
    """Raised when event delivery fails."""
    pass

class EventValidationError(EventBusException):
    """Raised when event validation fails."""
    pass