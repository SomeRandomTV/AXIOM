"""Base response generator interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ResponseGenerator(ABC):
    """Abstract base class for response generation."""
    
    @abstractmethod
    def generate_response(
        self, 
        intent_name: str,
        entities: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response based on intent and entities.
        
        Args:
            intent_name: Name of the detected intent
            entities: Extracted entities from intent detection
            context: Optional conversation context
            
        Returns:
            Generated response text
        """
        pass