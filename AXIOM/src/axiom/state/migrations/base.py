"""Base migration interface."""

from abc import ABC, abstractmethod
import sqlite3
from typing import List

class Migration(ABC):
    """Abstract base class for database migrations."""
    
    @abstractmethod
    def version(self) -> int:
        """Get the migration version number."""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Get a description of what this migration does."""
        pass
    
    @abstractmethod
    def up(self, connection: sqlite3.Connection) -> None:
        """
        Apply the migration.
        
        Args:
            connection: Database connection to use
        """
        pass
    
    @abstractmethod
    def down(self, connection: sqlite3.Connection) -> None:
        """
        Revert the migration.
        
        Args:
            connection: Database connection to use
        """
        pass