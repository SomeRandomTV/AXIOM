"""Base classes for policy evaluation."""

from abc import ABC, abstractmethod
from typing import Any, Dict

class PolicyResult:
    """Result of a policy evaluation."""
    def __init__(self, passed: bool, violations: Dict[str, Any] = None):
        self.passed = passed
        self.violations = violations or {}

class PolicyContext:
    """Context for policy evaluation."""
    def __init__(self, user_input: str = None, response: str = None):
        self.user_input = user_input
        self.response = response

class Policy(ABC):
    """Abstract base class for policies."""
    @abstractmethod
    def evaluate(self, context: PolicyContext) -> PolicyResult:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        pass