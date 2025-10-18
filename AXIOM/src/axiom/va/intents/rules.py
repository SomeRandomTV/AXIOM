"""Rule-based intent detection implementation."""

import re
from datetime import datetime
from typing import Dict, Any, Optional, Pattern

from .base import Intent, IntentDetector

import json
from pathlib import Path

class RuleBasedIntentDetector(IntentDetector):
    """
    Intent detector using regex patterns and rules.
    Loads patterns from external config (JSON) for flexibility.
    """

    def __init__(self, intent_config_path: Optional[str] = None, patterns_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize the intent detector.
        Args:
            intent_config_path: Path to JSON file with intent patterns.
            patterns_dict: (For testing/DI) Dict of intent patterns.
        """
        if patterns_dict is not None:
            patterns_data = patterns_dict
        elif intent_config_path is not None:
            config_path = Path(intent_config_path)
            if not config_path.exists():
                raise FileNotFoundError(f"Intent config file not found: {intent_config_path}")
            with config_path.open("r") as f:
                patterns_data = json.load(f)
        else:
            raise ValueError("Must provide either intent_config_path or patterns_dict.")

        self._patterns: Dict[str, list[Pattern]] = {}
        for intent, entry in patterns_data.items():
            regexes = entry["patterns"] if isinstance(entry, dict) and "patterns" in entry else entry
            self._patterns[intent] = [re.compile(pat, re.I) for pat in regexes]
    
    def detect_intent(self, text: str) -> Optional[Intent]:
        """
        Detect intent using regex pattern matching.
        
        Args:
            text: User input text
            
        Returns:
            Intent with highest confidence, or None if no match
        """
        best_match = None
        highest_confidence = 0.0
        
        for intent_name, patterns in self._patterns.items():
            # Check each pattern for the intent
            for pattern in patterns:
                if match := pattern.search(text):
                    # Calculate confidence based on match length and position
                    match_length = match.end() - match.start()
                    text_coverage = match_length / len(text)
                    position_factor = 1.0 if match.start() == 0 else 0.8
                    confidence = text_coverage * position_factor
                    
                    if confidence > highest_confidence:
                        entities = self._extract_entities(intent_name, text, match)
                        best_match = Intent(
                            name=intent_name,
                            confidence=confidence,
                            entities=entities
                        )
                        highest_confidence = confidence
        
        return best_match
    
    def get_supported_intents(self) -> list[str]:
        """Get list of supported intent names."""
        return list(self._patterns.keys())
    
    def _extract_entities(self, intent_name: str, text: str, match: re.Match) -> Dict[str, Any]:
        """
        Extract entities based on intent type and matched text.
        
        Args:
            intent_name: Name of the detected intent
            text: Original input text
            match: Regex match object
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        if intent_name == "time.query":
            entities["current_time"] = datetime.now().strftime("%I:%M %p")
            
        elif intent_name == "date.query":
            current_date = datetime.now()
            entities.update({
                "date": current_date.strftime("%Y-%m-%d"),
                "weekday": current_date.strftime("%A"),
                "formatted_date": current_date.strftime("%B %d, %Y")
            })
            
        elif intent_name in ["greeting", "farewell"]:
            # Extract time of day for appropriate response
            hour = datetime.now().hour
            if hour < 12:
                entities["time_of_day"] = "morning"
            elif hour < 17:
                entities["time_of_day"] = "afternoon"
            else:
                entities["time_of_day"] = "evening"
                
        elif intent_name == "caregiver.notify":
            # Try to extract specific caregiver role if mentioned
            role_pattern = re.compile(r"(?:caregiver|nurse|doctor)")
            if role_match := role_pattern.search(text):
                entities["role"] = role_match.group()
        
        return entities