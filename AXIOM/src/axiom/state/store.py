"""SQLite-based state store implementation."""

import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from contextlib import contextmanager
from threading import Lock

from .models import ConversationTurn, SystemEvent, Alert
from .exceptions import (
    DatabaseConnectionError,
    DatabaseMigrationError,
    QueryExecutionError
)
from .queries import *

logger = logging.getLogger(__name__)

class StateStore:
    """
    SQLite-based persistent state store for the AXIOM system.
    Provides ACID-compliant storage with connection pooling.
    """
    
    def __init__(self, db_path: Union[str, Path], pool_size: int = 5):
        """
        Initialize the state store.
        
        Args:
            db_path: Path to SQLite database file
            pool_size: Maximum number of concurrent database connections
        """
        self._db_path = Path(db_path)
        self._pool_size = pool_size
        self._lock = Lock()
        self._connections: List[sqlite3.Connection] = []
        
        # Ensure database directory exists
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database schema if not exists."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create schema version table
                cursor.execute(CREATE_VERSION_TABLE)
                
                # Create core tables
                cursor.execute(CREATE_CONVERSATIONS_TABLE)
                cursor.execute(CREATE_CONVERSATIONS_INDEX)
                cursor.execute(CREATE_SYSTEM_EVENTS_TABLE)
                cursor.execute(CREATE_SYSTEM_EVENTS_INDEX)
                
                # Create future expansion tables
                cursor.execute(CREATE_SENSOR_DATA_TABLE)
                cursor.execute(CREATE_ALERTS_TABLE)
                
                conn.commit()
                
        except sqlite3.Error as e:
            raise DatabaseMigrationError(f"Failed to initialize database: {e}")
    
    @contextmanager
    def _get_connection(self):  # Type hint removed as it's a context manager
        """
        Get a database connection from the pool.
        
        Yields:
            sqlite3.Connection: A database connection from the pool
            
        Raises:
            DatabaseConnectionError: If no connection could be obtained
        """
        connection = None
        
        try:
            with self._lock:
                # Try to get an existing connection
                if self._connections:
                    connection = self._connections.pop()
                
                # Create new connection if needed
                if connection is None:
                    if len(self._connections) >= self._pool_size:
                        raise DatabaseConnectionError("Connection pool exhausted")
                    
                    connection = sqlite3.connect(
                        self._db_path,
                        detect_types=sqlite3.PARSE_DECLTYPES
                    )
                    connection.row_factory = sqlite3.Row
            
            yield connection
            
            # Return connection to pool
            with self._lock:
                if len(self._connections) < self._pool_size:
                    self._connections.append(connection)
                    connection = None
                
        finally:
            # Close connection if not returned to pool
            if connection is not None:
                connection.close()
    
    def log_conversation_turn(self, turn: ConversationTurn) -> None:
        """
        Log a conversation interaction.
        
        Args:
            turn: Conversation turn to log
            
        Raises:
            QueryExecutionError: If the insert fails
        """
        try:
            with self._get_connection() as conn:
                conn.execute(INSERT_CONVERSATION, turn.to_db_tuple())
                conn.commit()
        except sqlite3.Error as e:
            raise QueryExecutionError(f"Failed to log conversation turn: {e}")
    
    def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[ConversationTurn]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session to get history for
            limit: Maximum number of turns to retrieve
            
        Returns:
            List of conversation turns in reverse chronological order
            
        Raises:
            QueryExecutionError: If the query fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(GET_CONVERSATION_HISTORY, (session_id, limit))
                return [ConversationTurn.from_db_row(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise QueryExecutionError(f"Failed to get conversation history: {e}")
    
    def log_system_event(self, event: SystemEvent) -> None:
        """
        Log a system event.
        
        Args:
            event: System event to log
            
        Raises:
            QueryExecutionError: If the insert fails
        """
        try:
            with self._get_connection() as conn:
                conn.execute(INSERT_SYSTEM_EVENT, event.to_db_tuple())
                conn.commit()
        except sqlite3.Error as e:
            raise QueryExecutionError(f"Failed to log system event: {e}")
    
    def get_system_events(
        self, 
        event_type: str, 
        limit: int = 100
    ) -> List[SystemEvent]:
        """
        Get system events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            limit: Maximum number of events to retrieve
            
        Returns:
            List of system events in reverse chronological order
            
        Raises:
            QueryExecutionError: If the query fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(GET_SYSTEM_EVENTS, (event_type, limit))
                return [SystemEvent.from_db_row(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise QueryExecutionError(f"Failed to get system events: {e}")
    
    def cleanup_old_data(
        self, 
        conversation_days: int = 30, 
        event_days: int = 7
    ) -> None:
        """
        Clean up old data based on retention policy.
        
        Args:
            conversation_days: Days to retain conversation history
            event_days: Days to retain system events
            
        Raises:
            QueryExecutionError: If cleanup fails
        """
        try:
            with self._get_connection() as conn:
                conn.execute(CLEANUP_OLD_CONVERSATIONS, (conversation_days,))
                conn.execute(CLEANUP_OLD_EVENTS, (event_days,))
                conn.commit()
        except sqlite3.Error as e:
            raise QueryExecutionError(f"Failed to clean up old data: {e}")
    
    def backup_database(self, backup_path: Union[str, Path]) -> None:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path to write backup file
            
        Raises:
            DatabaseConnectionError: If backup fails
        """
        backup_path = Path(backup_path)
        try:
            with self._get_connection() as conn:
                backup = sqlite3.connect(backup_path)
                conn.backup(backup)
                backup.close()
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"Failed to create database backup: {e}")
    
    def execute_query(
        self, 
        query: str, 
        params: tuple = ()
    ) -> List[Dict[str, Any]]:
        """
        Execute a custom query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of query results as dictionaries
            
        Raises:
            QueryExecutionError: If query fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            raise QueryExecutionError(f"Failed to execute query: {e}")
    
    def close(self) -> None:
        """Close all database connections."""
        with self._lock:
            for conn in self._connections:
                conn.close()
            self._connections.clear()