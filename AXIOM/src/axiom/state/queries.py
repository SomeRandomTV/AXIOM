"""SQL queries for the state store component."""

# Schema version table
CREATE_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);
"""

# Conversation history table
CREATE_CONVERSATIONS_TABLE = """
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
"""

CREATE_CONVERSATIONS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp);
"""

# System events table
CREATE_SYSTEM_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload JSON,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    correlation_id TEXT,
    CONSTRAINT idx_event_type_timestamp UNIQUE (event_type, timestamp)
);
"""

CREATE_SYSTEM_EVENTS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_correlation_id ON system_events(correlation_id);
"""

# Future expansion tables (Phase 2+)
CREATE_SENSOR_DATA_TABLE = """
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
"""

CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    resolved_at TEXT,
    metadata JSON
);
"""

# Query templates
INSERT_CONVERSATION = """
INSERT INTO conversations (
    session_id, user_input, assistant_response, 
    detected_intent, processing_time, timestamp, metadata
) VALUES (?, ?, ?, ?, ?, ?, ?);
"""

GET_CONVERSATION_HISTORY = """
SELECT * FROM conversations 
WHERE session_id = ? 
ORDER BY timestamp DESC 
LIMIT ?;
"""

INSERT_SYSTEM_EVENT = """
INSERT INTO system_events (
    event_type, payload, timestamp, source, correlation_id
) VALUES (?, ?, ?, ?, ?);
"""

GET_SYSTEM_EVENTS = """
SELECT * FROM system_events 
WHERE event_type = ? 
ORDER BY timestamp DESC 
LIMIT ?;
"""

# Cleanup queries
CLEANUP_OLD_CONVERSATIONS = """
DELETE FROM conversations 
WHERE timestamp < datetime('now', '-? days');
"""

CLEANUP_OLD_EVENTS = """
DELETE FROM system_events 
WHERE timestamp < datetime('now', '-? days');
"""