from typing import List, Dict, Any
from abc import ABC, abstractmethod
import logging

from .events import Event

logger = logging.getLogger(__name__)

class EventHandler(ABC):
    """Base abstract class for event handlers."""
    """Will be extended to handle Auralens / Other events"""
    
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """
        Handle an event.
        
        Args:
            event: The event to handle
        """
        
        
        pass
    
    @abstractmethod
    def get_supported_events(self) -> List[str]:
        """
        Get the list of event types this handler supports.
        
        Returns:
            List of supported event types
        """
        pass

class SystemEventHandler(EventHandler):
    """Handler for system-level events like startup and shutdown."""
    
    def handle_event(self, event: Event) -> None:
        if event.event_type == "system.start":
            logger.info(f"System starting up with version {event.payload.get('version')}")
            # Initialize components based on configuration
            self._init_components(event.payload.get("configuration", {}))
        elif event.event_type == "system.shutdown":
            logger.info(f"System shutting down: {event.payload.get('reason')}")
            self._cleanup()
    
    def get_supported_events(self) -> List[str]:
        return ["system.start", "system.shutdown"]
    
    def _init_components(self, config: Dict[str, Any]) -> None:
        """Initialize system components with configuration."""
        try:
            # Component initialization logic here
            pass
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
    
    def _cleanup(self) -> None:
        """Cleanup resources during shutdown."""
        try:
            # Cleanup logic here
            pass
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

class ConversationEventHandler(EventHandler):
    """Handler for conversation-related events."""
    
    def handle_event(self, event: Event) -> None:
        if event.event_type == "conversation.turn":
            self._process_conversation_turn(event.payload)
    
    def get_supported_events(self) -> List[str]:
        return ["conversation.turn"]
    
    def _process_conversation_turn(self, payload: Dict[str, Any]) -> None:
        """Process a conversation turn event."""
        try:
            session_id = payload.get("session_id")
            user_input = payload.get("user_input")
            response = payload.get("assistant_response")
            processing_time = payload.get("processing_time")
            
            logger.info(
                f"Conversation turn in session {session_id} "
                f"processed in {processing_time}ms"
            )
            # Additional conversation processing logic here
        except Exception as e:
            logger.error(f"Error processing conversation turn: {e}")

class StateUpdateEventHandler(EventHandler):
    """Handler for state update events."""
    
    def handle_event(self, event: Event) -> None:
        if event.event_type == "state.updated":
            self._handle_state_update(event.payload)
    
    def get_supported_events(self) -> List[str]:
        return ["state.updated"]
    
    def _handle_state_update(self, payload: Dict[str, Any]) -> None:
        """Handle a state update event."""
        try:
            # State update logic here
            pass
        except Exception as e:
            logger.error(f"Error handling state update: {e}")
