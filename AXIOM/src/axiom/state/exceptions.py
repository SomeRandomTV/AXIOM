"""Exception classes for the state store component."""

class StateStoreException(Exception):
    """Base exception for state store related errors."""
    pass

class DatabaseConnectionError(StateStoreException):
    """Raised when database connection fails."""
    pass

class DatabaseMigrationError(StateStoreException):
    """Raised when database migration fails."""
    pass

class InvalidSchemaVersionError(StateStoreException):
    """Raised when database schema version is invalid."""
    pass

class QueryExecutionError(StateStoreException):
    """Raised when a database query fails."""
    pass