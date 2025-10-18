"""Dialog Manager implementation."""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from ..bus.events import Event, ConversationTurnEvent
from ..bus.event_bus import EventBus
from .intents.base import Intent
from .intents.rules import RuleBasedIntentDetector
from .responses.templates import TemplateResponseGenerator

logger = logging.getLogger(__name__)

class DialogManager:
    """
    Manages conversation flow, intent detection, and response generation.
    Core component of the Virtual Assistant system.
    """

    def __init__(self, event_bus: EventBus, intent_config_path: Optional[str] = None, patterns_dict: Optional[dict] = None):
        """
        Initialize dialog manager.
        Args:
            event_bus: Event bus instance for publishing events
            intent_config_path: Path to intent patterns JSON config
            patterns_dict: (Testing) Dict of intent patterns
        """
        self._event_bus = event_bus
        self._intent_detector = RuleBasedIntentDetector(intent_config_path=intent_config_path, patterns_dict=patterns_dict)
        self._response_generator = TemplateResponseGenerator()
        self._session_context: Dict[str, Dict[str, Any]] = {}

        # Register as publisher for conversation events
        self._event_bus.register_publisher(
            "dialog_manager",
            ["conversation.turn"]
        )
    
    async def process_input(self, session_id: str, user_input: str) -> str:
        """
        Process user input and generate appropriate response.
        
        Args:
            session_id: Current conversation session ID
            user_input: Text input from user
            
        Returns:
            Assistant response text
        """
        start_time = datetime.now()
        
        try:
            # Initialize session context if needed
            if session_id not in self._session_context:
                self._session_context[session_id] = {
                    "turn_count": 0,
                    "last_intent": None,
                    "last_response": None
                }
            
            # Detect intent
            intent = self._detect_intent(user_input)
            
            # Generate response
            response = self._generate_response(
                intent,
                self._session_context[session_id]
            )
            
            # Update context
            self._update_context(session_id, intent, response)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
            
            # Publish conversation turn event
            await self._publish_turn_event(
                session_id, user_input, response, intent, processing_time
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            return "I apologize, but I encountered an error. Please try again."
    
    def _detect_intent(self, text: str) -> Optional[Intent]:
        """
        Detect intent from user input.
        
        Args:
            text: User input text
            
        Returns:
            Detected intent or None
        """
        try:
            return self._intent_detector.detect_intent(text)
        except Exception as e:
            logger.error(f"Error detecting intent: {e}")
            return None
    
    def _generate_response(
        self,
        intent: Optional[Intent],
        context: Dict[str, Any]
    ) -> str:
        """
        Generate response based on intent and context.
        
        Args:
            intent: Detected intent, if any
            context: Current session context
            
        Returns:
            Generated response text
        """
        try:
            if intent is None:
                return self._response_generator.generate_response(
                    "default", {}, context
                )
            
            return self._response_generator.generate_response(
                intent.name,
                intent.entities,
                context
            )
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm having trouble formulating a response. Please try again."
    
    def _update_context(
        self,
        session_id: str,
        intent: Optional[Intent],
        response: str
    ) -> None:
        """
        Update session context with latest interaction.
        
        Args:
            session_id: Current session ID
            intent: Detected intent
            response: Generated response
        """
        context = self._session_context[session_id]
        context["turn_count"] += 1
        context["last_intent"] = intent.name if intent else None
        context["last_response"] = response
    
    async def _publish_turn_event(
        self,
        session_id: str,
        user_input: str,
        response: str,
        intent: Optional[Intent],
        processing_time: float
    ) -> None:
        """
        Publish conversation turn event.
        
        Args:
            session_id: Current session ID
            user_input: Original user input
            response: Generated response
            intent: Detected intent
            processing_time: Processing time in milliseconds
        """
        event = ConversationTurnEvent(
            source="dialog_manager",
            session_id=session_id,
            user_input=user_input,
            assistant_response=response,
            intent={
                "name": intent.name,
                "confidence": intent.confidence,
                "entities": intent.entities
            } if intent else None,
            processing_time=processing_time
        )
        
        await self._event_bus.publish(event)