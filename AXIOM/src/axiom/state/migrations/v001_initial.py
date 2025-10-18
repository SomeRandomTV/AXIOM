"""Initial database schema migration."""

from datetime import datetime
import sqlite3

from .base import Migration

class InitialMigration(Migration):
    """Creates the initial database schema."""
    
    def version(self) -> int:
        return 1
    
    def description(self) -> str:
        return "Initial schema creation"
    
    def up(self, connection: sqlite3.Connection) -> None:
        cursor = connection.cursor()
        
        # Create schema version table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL,
            description TEXT NOT NULL
        );
        """)
        
        # Create conversations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_input TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            detected_intent TEXT,
            processing_time INTEGER,
            timestamp TEXT NOT NULL,
            metadata JSON,
            CONSTRAINT idx_session_timestamp UNIQUE (session_id, timestamp)
        );
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp);
        """)
        
        # Create system_events table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload JSON,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            correlation_id TEXT,
            CONSTRAINT idx_event_type_timestamp UNIQUE (event_type, timestamp)
        );
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_correlation_id ON system_events(correlation_id);
        """)
        
        # Record migration
        cursor.execute(
            "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
            (self.version(), datetime.now().isoformat(), self.description())
        )
        
        connection.commit()
    
    def down(self, connection: sqlite3.Connection) -> None:
        cursor = connection.cursor()
        
        # Drop all tables
        cursor.execute("DROP TABLE IF EXISTS conversations;")
        cursor.execute("DROP TABLE IF EXISTS system_events;")
        cursor.execute("DROP TABLE IF EXISTS schema_version;")
        
        connection.commit()