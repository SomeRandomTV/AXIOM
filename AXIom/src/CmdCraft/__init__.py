# src/cmdcraft/__init__.py
"""
CmdCraft - Command and Function Management Library for AXIOM
Handles NLP parsing, command execution, Ollama model management,
and a plugin system for new commands.
"""

from .ollama_manager import OllamaManager
from .CodeLogger import CodeLogger

__all__ = ["OllamaManager", "CodeLogger"]