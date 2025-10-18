"""Template-based response generation."""

import random
from typing import Dict, Any, Optional, List

from .base import ResponseGenerator

class TemplateResponseGenerator(ResponseGenerator):
    """
    Response generator using predefined templates.
    Supports basic variation and context-aware responses.
    """
    
    def __init__(self):
        # Response templates for each intent
        self._templates: Dict[str, List[str]] = {
            "time.query": [
                "It's {current_time}.",
                "The current time is {current_time}.",
                "Right now it's {current_time}."
            ],
            "date.query": [
                "Today is {weekday}, {formatted_date}.",
                "It's {weekday}, {formatted_date}.",
                "The date is {formatted_date}."
            ],
            "greeting": [
                "Good {time_of_day}! How can I help you today?",
                "Hello! Hope you're having a good {time_of_day}.",
                "Hi there! How may I assist you this {time_of_day}?"
            ],
            "farewell": [
                "Goodbye! Have a nice {time_of_day}.",
                "See you later! Enjoy your {time_of_day}.",
                "Bye for now! Take care."
            ],
            "help.request": [
                "I can help you with several things:\n- Checking the time and date\n- Basic conversation\n- Contacting your caregiver\n- Answering questions\nWhat would you like to know?",
                "Here's what I can do:\n- Tell you the time and date\n- Chat with you\n- Help you contact your caregiver\n- Answer your questions\nHow can I assist you?",
            ],
            "caregiver.notify": [
                "I'll notify your {role} right away.",
                "I'm contacting your {role} now.",
                "I'll get your {role} for you immediately."
            ],
            "smalltalk.how_are_you": [
                "I'm doing well, thank you for asking! How can I help you today?",
                "I'm functioning perfectly! What can I do for you?",
                "All systems operational! How may I assist you?"
            ],
            "default": [
                "I'm not sure I understood that. Could you please rephrase?",
                "I didn't quite catch that. Can you say it another way?",
                "I'm still learning. Could you try asking in a different way?"
            ]
        }
        
        # Keep track of last used template for each intent
        self._last_used: Dict[str, str] = {}
    
    def generate_response(
        self,
        intent_name: str,
        entities: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response using templates.
        
        Args:
            intent_name: Name of the detected intent
            entities: Extracted entities from intent detection
            context: Optional conversation context
            
        Returns:
            Generated response text
        """
        # Get templates for the intent, fallback to default if not found
        templates = self._templates.get(intent_name, self._templates["default"])
        
        # Filter out last used template if possible
        available_templates = [t for t in templates if t != self._last_used.get(intent_name)]
        if not available_templates:
            available_templates = templates
        
        # Select random template
        template = random.choice(available_templates)
        self._last_used[intent_name] = template
        
        try:
            # Format template with entities
            response = template.format(**entities)
        except KeyError:
            # Fallback if required entities are missing 
            response = random.choice(self._templates["default"])
            # response += llm call
        
        return response