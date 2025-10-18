"""Future expansion schema migration."""

from datetime import datetime
import sqlite3

from .base import Migration

class FutureExpansionMigration(Migration):
    """Adds tables for future expansion (Phase 2+)."""
    
    def version(self) -> int:
        return 2
    
    def description(self) -> str:
        return "Add future expansion tables"
    
    def up(self, connection: sqlite3.Connection) -> None:
        cursor = connection.cursor()
        
        # Create sensor_data table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            timestamp TEXT NOT NULL,
            metadata JSON,
            CONSTRAINT idx_sensor_timestamp UNIQUE (sensor_id, timestamp)
        );
        """)
        
        # Create alerts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            resolved_at TEXT,
            metadata JSON
        );
        """)
        
        # Record migration
        cursor.execute(
            "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
            (self.version(), datetime.now().isoformat(), self.description())
        )
        
        connection.commit()
    
    def down(self, connection: sqlite3.Connection) -> None:
        cursor = connection.cursor()
        
        # Drop future expansion tables
        cursor.execute("DROP TABLE IF EXISTS sensor_data;")
        cursor.execute("DROP TABLE IF EXISTS alerts;")
        
        # Remove migration record
        cursor.execute("DELETE FROM schema_version WHERE version = ?", (self.version(),))
        
        connection.commit()