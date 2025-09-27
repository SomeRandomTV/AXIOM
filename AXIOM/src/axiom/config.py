#!/usr/bin/env python3
"""
AXIOM Configuration Management with Dataclasses.

This module provides robust configuration management using Python dataclasses,
following PEP 8 and modern Python best practices.

Key Features:
- Type-safe configuration with validation
- Environment variable integration
- Multiple loading strategies (env, dict, factory)
- Proper error handling and logging
- Path management and directory creation
"""

import json
import logging
import os
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv

# Configure module logger
logger = logging.getLogger(__name__)

# --- Configuration Loading ---
# This line loads variables from a file named .env into os.environ
load_dotenv()


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


def _validate_positive_int(value: int, name: str) -> None:
    """Validate that an integer value is positive."""
    if value <= 0:
        raise ConfigurationError(f"{name} must be positive, got {value}")


def _validate_range(value: float, min_val: float, max_val: float, name: str) -> None:
    """Validate that a value is within the specified range."""
    if not (min_val <= value <= max_val):
        raise ConfigurationError(
            f"{name} must be between {min_val} and {max_val}, got {value}"
        )


def _ensure_directory_exists(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning(f"Failed to create directory {path}: {e}")


def _convert_env_bool(value: str) -> bool:
    """Convert string environment variable to boolean."""
    return value.lower() in ("true", "1", "yes", "on")


def _parse_stop_sequences(value: str) -> List[str]:
    """Parse comma-separated stop sequences."""
    return [s.strip() for s in value.split(",") if s.strip()]


@dataclass
class DatabaseConfig:
    """Database configuration with comprehensive validation."""

    path: Path = field(
        default_factory=lambda: Path.cwd() / "data" / "database.db"
    )
    backup_enabled: bool = True
    backup_interval: str = "24h"
    connection_timeout: int = 30
    max_connections: int = 2

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Convert string paths to Path objects
        if isinstance(self.path, str):
            self.path = Path(self.path)

        # Validation
        _validate_positive_int(self.connection_timeout, "connection_timeout")
        _validate_positive_int(self.max_connections, "max_connections")

        if not self.backup_interval:
            raise ConfigurationError("backup_interval cannot be empty")

        # Ensure parent directory exists
        _ensure_directory_exists(self.path.parent)

    @classmethod
    def from_env(cls, prefix: str = "DB_") -> "DatabaseConfig":
        """Create configuration from environment variables."""
        kwargs = {}

        env_mappings = {
            f"{prefix}PATH": ("path", lambda x: Path(x)),
            f"{prefix}BACKUP_ENABLED": ("backup_enabled", _convert_env_bool),
            f"{prefix}BACKUP_INTERVAL": ("backup_interval", str),
            f"{prefix}CONNECTION_TIMEOUT": ("connection_timeout", int),
            f"{prefix}MAX_CONNECTIONS": ("max_connections", int),
        }

        for env_var, (field_name, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    kwargs[field_name] = converter(value)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(f"Invalid {env_var}: {value} - {e}")

        return cls(**kwargs)


@dataclass
class VirtualAssistantConfig:
    """Virtual Assistant configuration with validation."""

    response_timeout: int = 40
    max_context_length: int = 512
    enable_streaming_text: bool = True
    max_response_length: int = 150

    def __post_init__(self) -> None:
        """Validate configuration."""
        _validate_positive_int(self.response_timeout, "response_timeout")
        _validate_positive_int(self.max_context_length, "max_context_length")
        _validate_positive_int(self.max_response_length, "max_response_length")

        # Logical validation
        if self.max_response_length > self.max_context_length:
            raise ConfigurationError(
                "max_response_length cannot exceed max_context_length"
            )

    @classmethod
    def from_env(cls, prefix: str = "VA_") -> "VirtualAssistantConfig":
        """Create configuration from environment variables."""
        kwargs = {}

        env_mappings = {
            f"{prefix}RESPONSE_TIMEOUT": ("response_timeout", int),
            f"{prefix}MAX_CONTEXT_LENGTH": ("max_context_length", int),
            f"{prefix}ENABLE_STREAMING_TEXT": ("enable_streaming_text", _convert_env_bool),
            f"{prefix}MAX_RESPONSE_LENGTH": ("max_response_length", int),
        }

        for env_var, (field_name, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    kwargs[field_name] = converter(value)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(f"Invalid {env_var}: {value} - {e}")

        return cls(**kwargs)


@dataclass
class PolicyConfig:
    """AI Policy configuration with comprehensive validation."""

    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.1
    presence_penalty: float = 0.6
    frequency_penalty: float = 0.0
    stop: Optional[Union[str, List[str]]] = None
    seed: int = 42

    def __post_init__(self) -> None:
        """Validate AI policy parameters."""
        # Token validation
        _validate_positive_int(self.max_tokens, "max_tokens")

        # Parameter range validations
        _validate_range(self.temperature, 0.0, 2.0, "temperature")
        _validate_range(self.top_p, 0.0, 1.0, "top_p")
        _validate_positive_int(self.top_k, "top_k")
        _validate_range(self.repetition_penalty, 0.0, 2.0, "repetition_penalty")
        _validate_range(self.presence_penalty, -2.0, 2.0, "presence_penalty")
        _validate_range(self.frequency_penalty, -2.0, 2.0, "frequency_penalty")

        # Convert single stop string to list
        if isinstance(self.stop, str):
            self.stop = [self.stop]

    @classmethod
    def from_env(cls, prefix: str = "POLICY_") -> "PolicyConfig":
        """Create configuration from environment variables."""
        kwargs = {}

        env_mappings = {
            f"{prefix}MAX_TOKENS": ("max_tokens", int),
            f"{prefix}TEMPERATURE": ("temperature", float),
            f"{prefix}TOP_P": ("top_p", float),
            f"{prefix}TOP_K": ("top_k", int),
            f"{prefix}REPETITION_PENALTY": ("repetition_penalty", float),
            f"{prefix}PRESENCE_PENALTY": ("presence_penalty", float),
            f"{prefix}FREQUENCY_PENALTY": ("frequency_penalty", float),
            f"{prefix}STOP": ("stop", _parse_stop_sequences),
            f"{prefix}SEED": ("seed", int),
        }

        for env_var, (field_name, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    kwargs[field_name] = converter(value)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(f"Invalid {env_var}: {value} - {e}")

        return cls(**kwargs)


@dataclass
class EventBusConfig:
    """Event Bus configuration with validation."""

    max_queue_size: int = 150
    worker_threads: int = 1
    event_timeout: int = 10
    enable_dead_letter: bool = True
    dead_letter_path: Path = field(
        default_factory=lambda: Path.cwd() / "dead_letter"
    )

    def __post_init__(self) -> None:
        """Validate configuration."""
        # Convert string paths to Path objects
        if isinstance(self.dead_letter_path, str):
            self.dead_letter_path = Path(self.dead_letter_path)

        # Validation
        _validate_positive_int(self.max_queue_size, "max_queue_size")
        _validate_positive_int(self.worker_threads, "worker_threads")
        _validate_positive_int(self.event_timeout, "event_timeout")

        # Ensure dead letter directory exists if enabled
        if self.enable_dead_letter:
            _ensure_directory_exists(self.dead_letter_path)

    @classmethod
    def from_env(cls, prefix: str = "EVENT_") -> "EventBusConfig":
        """Create configuration from environment variables."""
        kwargs = {}

        env_mappings = {
            f"{prefix}MAX_QUEUE_SIZE": ("max_queue_size", int),
            f"{prefix}WORKER_THREADS": ("worker_threads", int),
            f"{prefix}EVENT_TIMEOUT": ("event_timeout", int),
            f"{prefix}ENABLE_DEAD_LETTER": ("enable_dead_letter", _convert_env_bool),
            f"{prefix}DEAD_LETTER_PATH": ("dead_letter_path", lambda x: Path(x)),
        }

        for env_var, (field_name, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    kwargs[field_name] = converter(value)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(f"Invalid {env_var}: {value} - {e}")

        return cls(**kwargs)


@dataclass
class LoggingConfig:
    """Logging configuration with validation."""

    level: int = logging.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    file_enabled: bool = True
    file_path: Path = field(default_factory=lambda: Path.cwd() / "logs")
    max_file_size: int = 10  # in MB
    console_enabled: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        # Convert string paths to Path objects
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)

        # Validation
        valid_levels = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]
        if self.level not in valid_levels:
            raise ConfigurationError(f"Invalid logging level: {self.level}")

        _validate_positive_int(self.max_file_size, "max_file_size")

        if not self.format:
            raise ConfigurationError("format cannot be empty")

        # Ensure log directory exists if file logging is enabled
        if self.file_enabled:
            _ensure_directory_exists(self.file_path)

    @classmethod
    def from_env(cls, prefix: str = "LOG_") -> "LoggingConfig":
        """Create configuration from environment variables."""
        kwargs = {}

        # Map string level names to constants
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        def parse_log_level(value: str) -> int:
            """Parse log level from string or integer."""
            if value.upper() in level_mapping:
                return level_mapping[value.upper()]
            try:
                # Allow integer parsing for log level
                return int(value)
            except ValueError:
                raise ConfigurationError(f"Invalid log level string or integer: {value}")


        env_mappings = {
            f"{prefix}LEVEL": ("level", parse_log_level),
            f"{prefix}FORMAT": ("format", str),
            f"{prefix}DATEFMT": ("datefmt", str),
            f"{prefix}FILE_ENABLED": ("file_enabled", _convert_env_bool),
            f"{prefix}FILE_PATH": ("file_path", lambda x: Path(x)),
            f"{prefix}MAX_FILE_SIZE": ("max_file_size", int),
            f"{prefix}CONSOLE_ENABLED": ("console_enabled", _convert_env_bool),
        }

        for env_var, (field_name, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    kwargs[field_name] = converter(value)
                except (ValueError, TypeError, KeyError) as e:
                    raise ConfigurationError(f"Invalid {env_var}: {value} - {e}")

        return cls(**kwargs)


@dataclass
class SystemConfig:
    """System configuration with validation."""

    debug: bool = False
    environment: Path = field(
        default_factory=lambda: Path.cwd() / "config" / "environment.json"
    )
    data_directory: Path = field(default_factory=lambda: Path.cwd() / "data")
    log_directory: Path = field(default_factory=lambda: Path.cwd() / "logs")
    config_directory: Path = field(default_factory=lambda: Path.cwd() / "configs")
    version: str = "1.0.0"
    startup_timeout: int = 30

    def __post_init__(self) -> None:
        """Validate configuration and create directories."""
        # Convert string paths to Path objects
        path_fields = [
            "environment",
            "data_directory",
            "log_directory",
            "config_directory"
        ]
        for field_name in path_fields:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, Path(value))

        # Validation
        _validate_positive_int(self.startup_timeout, "startup_timeout")

        if not self.version:
            raise ConfigurationError("version cannot be empty")

        # Create directories
        directories = [
            self.data_directory,
            self.log_directory,
            self.config_directory,
        ]
        for directory in directories:
            _ensure_directory_exists(directory)

        # Create config directory for environment file
        _ensure_directory_exists(self.environment.parent)

    @classmethod
    def from_env(cls, prefix: str = "SYSTEM_") -> "SystemConfig":
        """Create configuration from environment variables."""
        kwargs = {}

        env_mappings = {
            f"{prefix}DEBUG": ("debug", _convert_env_bool),
            f"{prefix}ENVIRONMENT": ("environment", lambda x: Path(x)),
            f"{prefix}DATA_DIRECTORY": ("data_directory", lambda x: Path(x)),
            f"{prefix}LOG_DIRECTORY": ("log_directory", lambda x: Path(x)),
            f"{prefix}CONFIG_DIRECTORY": ("config_directory", lambda x: Path(x)),
            f"{prefix}VERSION": ("version", str),
            f"{prefix}STARTUP_TIMEOUT": ("startup_timeout", int),
        }

        for env_var, (field_name, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    kwargs[field_name] = converter(value)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(f"Invalid {env_var}: {value} - {e}")

        return cls(**kwargs)


@dataclass
class AxiomConfig:
    """Main AXIOM configuration container with enhanced functionality."""

    system: SystemConfig = field(default_factory=SystemConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    virtual_assistant: VirtualAssistantConfig = field(
        default_factory=VirtualAssistantConfig
    )
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    event_bus: EventBusConfig = field(default_factory=EventBusConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def __post_init__(self) -> None:
        """Additional validation for cross-section dependencies."""
        # Sync debug mode with logging level
        if self.system.debug and self.logging.level > logging.DEBUG:
            self.logging.level = logging.DEBUG
            self.logging.console_enabled = True

    @classmethod
    def from_env(cls, prefix: str = "AXIOM_") -> "AxiomConfig":
        """Create complete configuration from environment variables."""
        return cls(
            system=SystemConfig.from_env(f"{prefix}SYSTEM_"),
            database=DatabaseConfig.from_env(f"{prefix}DB_"),
            virtual_assistant=VirtualAssistantConfig.from_env(f"{prefix}VA_"),
            policy=PolicyConfig.from_env(f"{prefix}POLICY_"),
            event_bus=EventBusConfig.from_env(f"{prefix}EVENT_"),
            logging=LoggingConfig.from_env(f"{prefix}LOG_"),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AxiomConfig":
        """Create configuration from dictionary (e.g., from JSON/YAML)."""
        kwargs = {}

        # Handle each section explicitly for better type safety
        if "system" in data:
            kwargs["system"] = SystemConfig(**data["system"])
        if "database" in data:
            kwargs["database"] = DatabaseConfig(**data["database"])
        if "virtual_assistant" in data:
            kwargs["virtual_assistant"] = VirtualAssistantConfig(
                **data["virtual_assistant"]
            )
        if "policy" in data:
            kwargs["policy"] = PolicyConfig(**data["policy"])
        if "event_bus" in data:
            kwargs["event_bus"] = EventBusConfig(**data["event_bus"])
        if "logging" in data:
            kwargs["logging"] = LoggingConfig(**data["logging"])

        return cls(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        result = asdict(self)
        return self._convert_paths_to_strings(result)

    def _convert_paths_to_strings(self, obj: Any) -> Any:
        """Convert Path objects to strings for JSON serialization."""
        if isinstance(obj, dict):
            return {k: self._convert_paths_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_paths_to_strings(item) for item in obj]
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return obj

    def validate_all(self) -> bool:
        """Validate all configuration sections."""
        try:
            # Individual validations are handled in __post_init__
            # Add any cross-section validation here

            # Example: Ensure database path is within data directory
            if not str(self.database.path).startswith(str(self.system.data_directory)):
                logger.warning("Database path is outside data directory")

            # Example: Check logging file path consistency
            if (
                    self.logging.file_enabled
                    and not str(self.logging.file_path).startswith(
                str(self.system.log_directory)
            )
            ):
                logger.warning("Log file path is outside log directory")

            return True

        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")

    def create_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.system.data_directory,
            self.system.log_directory,
            self.system.config_directory,
            self.database.path.parent,
        ]

        if self.logging.file_enabled:
            directories.append(self.logging.file_path)

        if self.event_bus.enable_dead_letter:
            directories.append(self.event_bus.dead_letter_path)

        for directory in directories:
            if directory:
                _ensure_directory_exists(directory)


class AxiomConfigFactory:
    """Factory for creating environment-specific configurations."""

    @staticmethod
    def development() -> "AxiomConfig":
        """Create development environment configuration."""
        return AxiomConfig(
            system=SystemConfig(debug=True, version="1.0.0-dev"),
            database=DatabaseConfig(
                path=Path("dev_data/database.db"), backup_enabled=False
            ),
            virtual_assistant=VirtualAssistantConfig(
                response_timeout=60,  # Longer timeout for debugging
                max_context_length=256,  # Smaller for faster iteration
            ),
            policy=PolicyConfig(
                temperature=0.9,  # More creative for testing
                seed=12345,  # Fixed seed for reproducible testing
            ),
            logging=LoggingConfig(
                level=logging.DEBUG, console_enabled=True, file_enabled=True
            ),
        )

    @staticmethod
    def production() -> "AxiomConfig":
        """Create production environment configuration."""
        return AxiomConfig(
            system=SystemConfig(debug=False, startup_timeout=60),
            database=DatabaseConfig(
                backup_enabled=True,
                backup_interval="12h",  # More frequent backups
                max_connections=10,  # Higher capacity
            ),
            virtual_assistant=VirtualAssistantConfig(
                response_timeout=30,  # Stricter timeout
                max_context_length=1024,  # Full capacity
            ),
            policy=PolicyConfig(
                temperature=0.7,  # Balanced creativity
                max_tokens=2000,  # Higher token limit
            ),
            event_bus=EventBusConfig(
                max_queue_size=500,  # Larger queue
                worker_threads=4,  # More workers
            ),
            logging=LoggingConfig(
                level=logging.WARNING,  # Less verbose
                console_enabled=False,
                file_enabled=True,
                max_file_size=50,  # Larger log files
            ),
        )

    @classmethod
    def from_environment(cls, env_name: Optional[str] = None) -> "AxiomConfig":
        """Load configuration based on environment name."""
        env_name = env_name or os.getenv("AXIOM_ENV", "development")

        if env_name.lower() in ["dev", "development"]:
            return cls.development()
        elif env_name.lower() in ["prod", "production"]:
            return cls.production()
        else:
            # Default to development with environment variable overrides
            logger.warning(f"Unknown environment: {env_name}, defaulting to development")
            return cls.development()


# The test_env_vars dictionary is still useful for defining expected values
test_env_vars = {
    "AXIOM_SYSTEM_DEBUG": "true",
    "AXIOM_DB_MAX_CONNECTIONS": "5",
    "AXIOM_POLICY_TEMPERATURE": "0.8",
    "AXIOM_VA_MAX_RESPONSE_LENGTH": "200",
    "AXIOM_EVENT_WORKER_THREADS": "2",
    "AXIOM_LOG_LEVEL": "DEBUG",
    "AXIOM_POLICY_STOP": "HALT,BREAK_TURN",
}


def _run_environment_variable_test() -> None:
    """
    Test environment variable loading, relying on the top-level load_dotenv()
    to load settings from an external .env file.
    """

    # 🛑 REMOVE MANUAL INJECTION LOOP:
    # for key, value in test_env_vars.items():
    #     os.environ[key] = value

    # Check if the required environment variables are actually loaded first
    # If not loaded, this test cannot prove the .env mechanism works.
    if os.getenv("AXIOM_SYSTEM_DEBUG") is None:
        logger.warning("⚠️ Skipping ENV test: AXIOM_SYSTEM_DEBUG not found. Ensure .env is loaded.")
        return

    try:
        # Load configuration directly from the environment (which load_dotenv populated)
        env_config = AxiomConfig.from_env()

        # Assertions to check if the .env values were loaded and correctly converted
        assert env_config.system.debug is True
        assert env_config.database.max_connections == 5
        assert env_config.policy.temperature == 0.8
        assert env_config.virtual_assistant.max_response_length == 200
        assert env_config.event_bus.worker_threads == 2
        assert env_config.logging.level == logging.DEBUG
        assert env_config.policy.stop == ["HALT", "BREAK_TURN"]

        logger.info("✅ Environment variable loading (via .env run) works")

    except Exception as e:
        logger.error(f"❌ Environment variable loading failed: {e}")


def _run_basic_configuration_test() -> None:
    """Test basic configuration creation and validation."""
    try:
        config = AxiomConfig()
        config.validate_all()
        logger.info("✅ Basic configuration created and validated")
    except Exception as e:
        logger.error(f"❌ Basic configuration failed: {e}")


def _run_development_configuration_test() -> None:
    """Test development configuration creation."""
    try:
        dev_config = AxiomConfigFactory.development()
        dev_config.validate_all()
        logger.info("✅ Development configuration created")
    except Exception as e:
        logger.error(f"❌ Development configuration failed: {e}")


def _run_dictionary_loading_test() -> None:
    """Test dictionary loading."""
    config_dict = {
        "system": {"debug": True, "version": "2.0.0"},
        "database": {"max_connections": 8},
        "policy": {"temperature": 1.0},
    }

    try:
        dict_config = AxiomConfig.from_dict(config_dict)
        assert dict_config.system.debug is True
        assert dict_config.database.max_connections == 8
        assert dict_config.policy.temperature == 1.0
        logger.info("✅ Dictionary loading works")
    except Exception as e:
        logger.error(f"❌ Dictionary loading failed: {e}")


def _run_serialization_test() -> None:
    """Test serialization and deserialization."""
    try:
        config = AxiomConfig()
        config_dict = config.to_dict()
        restored_config = AxiomConfig.from_dict(config_dict)
        logger.info("✅ Serialization/deserialization works")
    except Exception as e:
        logger.error(f"❌ Serialization failed: {e}")


def main() -> None:
    """Run configuration examples and tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("AXIOM Configuration Examples")
    logger.info("=" * 50)

    # Run all tests
    _run_basic_configuration_test()
    _run_development_configuration_test()
    _run_environment_variable_test()
    _run_dictionary_loading_test()
    _run_serialization_test()

    logger.info("🚀 All tests completed!")


if __name__ == "__main__":
    main()