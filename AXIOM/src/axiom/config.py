import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

"""
This file contains the configuration for the project
All configurations come from /configs
"""

@dataclass
class DatabaseConfig:
    path: str = Path(__file__).parent.parent / "data" / "database.db"
    backup_enabled: bool = True
    backup_interval: str = "24h"  # 24 hours
    connection_timeout: int = 30
    max_connections: int = 2

@dataclass
class VAConfig:
    response_timeout: int = 40
    max_context_length: int = 512 # for now
    enable_streaming_text: bool = True
    max_response_length: int = 150


@dataclass
class PolicyConfig:
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.1
    presence_penalty: float = 0.6
    frequency_penalty: float = 0.0
    stop: Optional[Union[str, List[str]]] = None
    seed: int = 42

@dataclass
class EventBusConfig:
    max_queue_size: int = 150
    worker_threads: int = 1
    event_timeout: int = 10
    enable_dead_letter: bool = True
    dead_letter_path: Path = Path(__file__).parent.parent / "dead_letter"

@dataclass
class LoggingConfig:
    level: int = logging.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    file_enabled: bool = True
    file_path: Path = Path(__file__).parent.parent / "logs"
    max_file_size: int = 10 # in mb
    console_enabled: bool = False

@dataclass
class SystemConfig:
    debug: bool = False
    environment: Path = Path(__file__).parent.parent / "config" / "environment.json"
    data_directory: Path = Path(__file__).parent.parent / "data"
    log_directory: Path = Path(__file__).parent.parent / "logs"
    config_directory: Path = Path(__file__).parent.parent / "configs"
    version: str = "1.0.0"
    startup_timeout: int = 30

@dataclass
class AxiomConfig:
    """Main AXIOM configuration container."""
    system: SystemConfig = field(default_factory=SystemConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    virtual_assistant: VAConfig = field(default_factory=VAConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    event_bus: EventBusConfig = field(default_factory=EventBusConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigManager:
    """
    Configuration manager that loads and validates configuration from multiple sources.

    Priority order (highest to lowest):
    1. Command-line arguments
    2. Environment variables
    3. Configuration files
    4. Default values
    """

    def __init__(self, config_file_paths: Optional[List[Union[str, Path]]] = None):
        """
        Initialize the configuration manager.

        :param config_file_paths: List of configuration file paths to try loading from
        """

        self.config_file_paths = config_file_paths or [
            "axiom-config.yaml",
            "axiom-config.yml",
            "axiom-config.json",
            "config/axiom-config.yaml",
            "config/axiom-config.yml",
            "config/axiom-config.json"
        ]
        self._loaded_config: Optional[AxiomConfig] = None

    def load_config(self, config_file: Optional[Path] = None, environment: Optional[Path] = None, cli_args: Optional[Dict[str, Any]] = None) -> AxiomConfig:
       """
        Load configuration from all sources in priority order.

        :param config_file: Path to specific config file (optional)
        :param environment: name (development, production, etc.)
        :param cli_args: Command-line arguments dictionary

        :returns: Complete configuration object

        :raises: ConfigurationError: If configuration is invalid
        """

       logging.info("Loading configuration from {}".format(config_file))

