"""
Structured logging configuration for AXIOM using structlog.

Provides:
- JSON-formatted logs for parsing/analysis
- Per-module loggers with configurable levels
- Console output for WARNING/CRITICAL only
- File output for all log levels
- Performance metrics tracking
- Context enrichment (timestamps, module, correlation IDs)
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
from structlog.types import FilteringBoundLogger
from datetime import datetime


class LogConfig:
    """Centralized logging configuration."""
    
    # Default log levels
    DEFAULT_LEVEL = logging.DEBUG
    CONSOLE_LEVEL = logging.WARNING  # Only WARNING and above to console
    FILE_LEVEL = logging.DEBUG  # Everything to file
    
    # Log file settings
    LOG_DIR = Path("logs")
    LOG_FILE = "axiom.log"
    MAX_BYTES = 10 * 1024 * 1024  # 10MB per file
    BACKUP_COUNT = 7  # Keep 7 days of logs
    
    # Module-specific log levels (can be overridden)
    MODULE_LEVELS: Dict[str, int] = {
        "axiom.bus": logging.DEBUG,
        "axiom.state": logging.DEBUG,
        "axiom.policy": logging.DEBUG,
        "axiom.va": logging.DEBUG,
        "axiom.console": logging.INFO,
        "axiom.config": logging.INFO,
    }


def setup_logging(
    log_dir: Optional[Path] = None,
    debug: bool = False
) -> None:
    """
    Initialize structured logging for AXIOM.
    
    Args:
        log_dir: Directory for log files (default: logs/)
        debug: If True, set all loggers to DEBUG level
    """
    log_dir = log_dir or LogConfig.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / LogConfig.LOG_FILE
    
    # Configure structlog processors
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            LogConfig.DEFAULT_LEVEL if not debug else logging.DEBUG
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # Set up standard logging handlers
    _setup_handlers(log_file, debug)
    
    # Configure module-specific loggers
    _configure_module_loggers(debug)


def _setup_handlers(log_file: Path, debug: bool) -> None:
    """Set up file and console handlers."""
    
    # File handler - all logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LogConfig.MAX_BYTES,
        backupCount=LogConfig.BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(LogConfig.FILE_LEVEL if not debug else logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - WARNING and above only (unless debug mode)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(
        logging.DEBUG if debug else LogConfig.CONSOLE_LEVEL
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else LogConfig.DEFAULT_LEVEL)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def _configure_module_loggers(debug: bool) -> None:
    """Configure per-module loggers with specific levels."""
    for module_name, level in LogConfig.MODULE_LEVELS.items():
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.DEBUG if debug else level)


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger for a specific module.
    
    Args:
        name: Module name (e.g., "axiom.bus.event_bus")
    
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class PerformanceLogger:
    """Context manager for logging performance metrics."""
    
    def __init__(self, logger: FilteringBoundLogger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(
            f"Starting {self.operation}",
            operation=self.operation,
            **self.context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None:
            return False
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation}",
                operation=self.operation,
                duration_seconds=duration,
                success=True,
                **self.context
            )
        else:
            self.logger.error(
                f"Failed {self.operation}",
                operation=self.operation,
                duration_seconds=duration,
                success=False,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                **self.context
            )
        
        return False  # Don't suppress exceptions


def log_event_bus_activity(logger: FilteringBoundLogger, event_type: str, action: str, **context):
    """Log event bus publish/subscribe activity."""
    logger.info(
        f"Event bus {action}",
        component="event_bus",
        event_type=event_type,
        action=action,
        **context
    )


def log_state_operation(
    logger: FilteringBoundLogger,
    operation: str,
    table: Optional[str] = None,
    **context
):
    """Log state store read/write operations."""
    logger.debug(
        f"State operation: {operation}",
        component="state_store",
        operation=operation,
        table=table,
        **context
    )


def log_policy_evaluation(
    logger: FilteringBoundLogger,
    policy_name: str,
    passed: bool,
    violations: Optional[Dict[str, Any]] = None,
    **context
):
    """Log policy evaluation results."""
    logger.info(
        f"Policy evaluation: {policy_name}",
        component="policy_engine",
        policy=policy_name,
        passed=passed,
        violations=violations or {},
        **context
    )


def log_dialog_decision(
    logger: FilteringBoundLogger,
    intent: str,
    action: str,
    **context
):
    """Log dialog manager decisions."""
    logger.info(
        f"Dialog decision: {intent} -> {action}",
        component="dialog_manager",
        intent=intent,
        action=action,
        **context
    )


def log_error(
    logger: FilteringBoundLogger,
    error: Exception,
    **context
):
    """Log errors with full context."""
    from axiom.utils.errors import AxiomError
    
    if isinstance(error, AxiomError):
        logger.error(
            error.message,
            error_code=error.error_code,
            error_details=error.to_dict(),
            **context
        )
    else:
        logger.error(
            str(error),
            error_type=type(error).__name__,
            error_message=str(error),
            **context
        )
