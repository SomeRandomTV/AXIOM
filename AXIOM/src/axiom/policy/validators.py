"""Input/output validation utilities for policies."""
import re
from typing import Dict, Any
from .policies import Policy, PolicyContext, PolicyResult

class ContentFilterPolicy(Policy):
    """Blocks inappropriate or disallowed content."""
    def __init__(self, banned_words=None):
        self.banned_words = banned_words or [
            "damn", "hell", "stupid", "idiot", "hate", "kill", "die", "simon", ""
        ]
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        text = context.user_input or context.response or ""
        violations = {}
        for word in self.banned_words:
            if re.search(rf"\\b{re.escape(word)}\\b", text, re.I):
                violations[word] = True
        return PolicyResult(passed=(not violations), violations=violations)
    def get_name(self) -> str:
        return "ContentFilterPolicy"
    def get_description(self) -> str:
        return "Blocks inappropriate or disallowed content."

class ResponseLengthPolicy(Policy):
    """Validates response length against configured maximum."""
    def __init__(self, max_length=500):
        self.max_length = max_length
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        text = context.response or ""
        violations = {}
        if len(text) > self.max_length:
            violations["length"] = len(text)
        return PolicyResult(passed=(not violations), violations=violations)
    def get_name(self) -> str:
        return "ResponseLengthPolicy"
    def get_description(self) -> str:
        return f"Ensures response does not exceed {self.max_length} characters."

class InputSanitizationPolicy(Policy):
    """Sanitizes and validates user input."""
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        text = context.user_input or ""
        violations = {}
        # Example: block SQL injection patterns
        if re.search(r"(;|--|\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b)", text, re.I):
            violations["sql_injection"] = True
        # Example: block overly long input
        if len(text) > 1000:
            violations["length"] = len(text)
        return PolicyResult(passed=(not violations), violations=violations)
    def get_name(self) -> str:
        return "InputSanitizationPolicy"
    def get_description(self) -> str:
        return "Sanitizes and validates user input for safety."