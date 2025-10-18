"""Base classes for intent detection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class Intent:
    """Represents a detected intent with confidence and entities."""
    name: str
    confidence: float
    entities: Dict[str, Any]

class IntentDetector(ABC):
    """Abstract base class for intent detection implementations."""
    
    @abstractmethod
    def detect_intent(self, text: str) -> Optional[Intent]:
        """
        Detect the intent from user input text.
        
        Args:
            text: User input text
            
        Returns:
            Intent if detected, None otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_intents(self) -> list[str]:
        """
        Get list of intents supported by this detector.
        
        Returns:
            List of supported intent names
        """
        pass