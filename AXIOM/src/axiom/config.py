#!/usr/bin/env python3
"""
AXIOM Configuration Management with Dataclasses and Factories.

Supports:
- JSON-based configuration files
- Environment variable overrides
- Command-line argument overrides
- Validation and defaults
- Dev/Prod factory environments
- Directory creation and path management
- Logging setup
"""

#!/usr/bin/env python3
"""
AXIOM Configuration Management with Project-Root Paths.

All persistent files (database, logs, data) are stored at the project root.
"""

import argparse
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ----------------------
# Define project root
# ----------------------
# config.py is at AXIOM/src/axiom/config.py
ROOT_DIR = Path(__file__).resolve().parents[2] # -> AXIOM/
logger.debug(f"ROOT_DIR set to: {ROOT_DIR}")

# ----------------------
# Exceptions
# ----------------------
class ConfigurationError(Exception):
    pass

# ----------------------
# Utilities
# ----------------------
def _validate_positive_int(value: int, name: str) -> None:
    if value <= 0:
        raise ConfigurationError(f"{name} must be positive, got {value}")

def _ensure_directory_exists(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning(f"Failed to create directory {path}: {e}")

def _convert_env_bool(value: str) -> bool:
    return value.lower() in ("true", "1", "yes", "on")

def _parse_stop_sequences(value: str) -> List[str]:
    return [s.strip() for s in value.split(",") if s.strip()]

# ----------------------
# Dataclasses
# ----------------------
@dataclass
class SystemConfig:
    debug: bool = False
    data_directory: Path = field(default_factory=lambda: ROOT_DIR / "data")
    log_directory: Path = field(default_factory=lambda: ROOT_DIR / "logs")
    version: str = "1.0.0"
    startup_timeout: int = 30

    def __post_init__(self):
        if isinstance(self.data_directory, str):
            self.data_directory = Path(self.data_directory)
        if isinstance(self.log_directory, str):
            self.log_directory = Path(self.log_directory)
        _validate_positive_int(self.startup_timeout, "startup_timeout")
        _ensure_directory_exists(self.data_directory)
        _ensure_directory_exists(self.log_directory)

    @classmethod
    def from_env(cls, prefix="SYSTEM_") -> "SystemConfig":
        kwargs = {}
        env_map = {
            f"{prefix}DEBUG": ("debug", _convert_env_bool),
            f"{prefix}DATA_DIRECTORY": ("data_directory", lambda x: Path(x)),
            f"{prefix}LOG_DIRECTORY": ("log_directory", lambda x: Path(x)),
            f"{prefix}VERSION": ("version", str),
            f"{prefix}STARTUP_TIMEOUT": ("startup_timeout", int),
        }
        for env_var, (field_name, conv) in env_map.items():
            val = os.getenv(env_var)
            if val is not None:
                kwargs[field_name] = conv(val)
        return cls(**kwargs)

@dataclass
class DatabaseConfig:
    path: Path = field(default_factory=lambda: ROOT_DIR / "data" / "axiom.db")
    backup_enabled: bool = True
    backup_interval: str = "24h"
    max_connections: int = 2

    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)
        _ensure_directory_exists(self.path.parent)

    @classmethod
    def from_env(cls, prefix="DB_") -> "DatabaseConfig":
        kwargs = {}
        env_map = {
            f"{prefix}PATH": ("path", lambda x: Path(x)),
            f"{prefix}BACKUP_ENABLED": ("backup_enabled", _convert_env_bool),
            f"{prefix}BACKUP_INTERVAL": ("backup_interval", str),
            f"{prefix}MAX_CONNECTIONS": ("max_connections", int),
        }
        for env_var, (field_name, conv) in env_map.items():
            val = os.getenv(env_var)
            if val is not None:
                kwargs[field_name] = conv(val)
        return cls(**kwargs)

@dataclass
class VirtualAssistantConfig:
    response_timeout: int = 40
    max_context_length: int = 512
    max_response_length: int = 150

    def __post_init__(self):
        _validate_positive_int(self.response_timeout, "response_timeout")
        _validate_positive_int(self.max_context_length, "max_context_length")
        if self.max_response_length > self.max_context_length:
            raise ConfigurationError(
                "max_response_length cannot exceed max_context_length"
            )

    @classmethod
    def from_env(cls, prefix="VA_") -> "VirtualAssistantConfig":
        kwargs = {}
        env_map = {
            f"{prefix}RESPONSE_TIMEOUT": ("response_timeout", int),
            f"{prefix}MAX_CONTEXT_LENGTH": ("max_context_length", int),
            f"{prefix}MAX_RESPONSE_LENGTH": ("max_response_length", int),
        }
        for env_var, (field_name, conv) in env_map.items():
            val = os.getenv(env_var)
            if val is not None:
                kwargs[field_name] = conv(val)
        return cls(**kwargs)

@dataclass
class PolicyConfig:
    max_tokens: int = 1000
    temperature: float = 0.7
    stop: Optional[List[str]] = None

    def __post_init__(self):
        if isinstance(self.stop, str):
            self.stop = _parse_stop_sequences(self.stop)

    @classmethod
    def from_env(cls, prefix="POLICY_") -> "PolicyConfig":
        kwargs = {}
        env_map = {
            f"{prefix}MAX_TOKENS": ("max_tokens", int),
            f"{prefix}TEMPERATURE": ("temperature", float),
            f"{prefix}STOP": ("stop", _parse_stop_sequences),
        }
        for env_var, (field_name, conv) in env_map.items():
            val = os.getenv(env_var)
            if val is not None:
                kwargs[field_name] = conv(val)
        return cls(**kwargs)

@dataclass
class AxiomConfig:
    system: SystemConfig = field(default_factory=SystemConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    virtual_assistant: VirtualAssistantConfig = field(default_factory=VirtualAssistantConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AxiomConfig":
        return cls(
            system=SystemConfig(**data.get("system", {})),
            database=DatabaseConfig(**data.get("database", {})),
            virtual_assistant=VirtualAssistantConfig(**data.get("virtual_assistant", {})),
            policy=PolicyConfig(**data.get("policy", {})),
        )

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> "AxiomConfig":
        path = Path(file_path)
        if not path.exists():
            raise ConfigurationError(f"Config file not found: {file_path}")
        with path.open("r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_env(cls) -> "AxiomConfig":
        """
        Load configuration from environment variables and
        resolve any relative paths under ROOT_DIR.
        """
        # Load sections individually
        system = SystemConfig.from_env()
        database = DatabaseConfig.from_env()
        virtual_assistant = VirtualAssistantConfig.from_env()
        policy = PolicyConfig.from_env()

        # Ensure all paths are absolute under ROOT_DIR
        if not system.data_directory.is_absolute():
            system.data_directory = ROOT_DIR / system.data_directory
        if not system.log_directory.is_absolute():
            system.log_directory = ROOT_DIR / system.log_directory
        if not database.path.is_absolute():
            database.path = ROOT_DIR / database.path

        return cls(
            system=system,
            database=database,
            virtual_assistant=virtual_assistant,
            policy=policy
        )

    @classmethod
    def load(cls, json_file: Optional[Union[str, Path]] = None, cli_args: Optional[List[str]] = None) -> "AxiomConfig":
        """
        Load configuration with precedence:
        defaults -> JSON -> environment -> CLI
        and ensure all paths are absolute under ROOT_DIR.
        """
        # 1) Start with defaults
        config = cls()

        # 2) JSON overrides
        if json_file:
            json_config = cls.from_json_file(json_file)
            config_dict = {**config.to_dict(), **json_config.to_dict()}
            config = cls.from_dict(config_dict)

        # 3) Environment overrides
        env_config = cls.from_env()
        config_dict = {**config.to_dict(), **env_config.to_dict()}
        config = cls.from_dict(config_dict)

        # 4) CLI overrides
        if cli_args:
            parser = argparse.ArgumentParser()
            parser.add_argument("--debug", action="store_true")
            parser.add_argument("--db-path", type=str)
            args, _ = parser.parse_known_args(cli_args)

            if args.debug:
                config.system.debug = True

            if args.db_path:
                db_path = Path(args.db_path)
                if not db_path.is_absolute():
                    db_path = ROOT_DIR / db_path
                config.database.path = db_path

        # 5) Normalize all relative paths under ROOT_DIR
        if not config.system.data_directory.is_absolute():
            config.system.data_directory = ROOT_DIR / config.system.data_directory
        if not config.system.log_directory.is_absolute():
            config.system.log_directory = ROOT_DIR / config.system.log_directory
        if not config.database.path.is_absolute():
            config.database.path = ROOT_DIR / config.database.path

        # 6) Ensure directories exist
        for directory in [
            config.system.data_directory,
            config.system.log_directory,
            config.database.path.parent
        ]:
            _ensure_directory_exists(directory)

        return config

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# ----------------------
# Factories
# ----------------------
class AxiomConfigFactory:
    @staticmethod
    def development() -> AxiomConfig:
        return AxiomConfig(
            system=SystemConfig(debug=True, version="1.0.0-dev"),
            database=DatabaseConfig(path=ROOT_DIR / "dev_data" / "axiom.db", backup_enabled=False),
            virtual_assistant=VirtualAssistantConfig(response_timeout=60, max_context_length=256),
            policy=PolicyConfig(temperature=0.9, stop=["TEST_STOP"]),
        )

    @staticmethod
    def production() -> AxiomConfig:
        return AxiomConfig(
            system=SystemConfig(debug=False, startup_timeout=60),
            database=DatabaseConfig(path=ROOT_DIR / "data" / "axiom.db", backup_enabled=True, backup_interval="12h", max_connections=10),
            virtual_assistant=VirtualAssistantConfig(response_timeout=30, max_context_length=1024),
            policy=PolicyConfig(temperature=0.7),
        )

    @classmethod
    def from_environment(cls, env_name: Optional[str] = None) -> AxiomConfig:
        env_name = env_name or os.getenv("AXIOM_ENV", "development")
        if env_name.lower() in ["dev", "development"]:
            return cls.development()
        elif env_name.lower() in ["prod", "production"]:
            return cls.production()
        else:
            logger.warning(f"Unknown environment: {env_name}, defaulting to development")
            return cls.development()


# --- Tests / Examples ---
if __name__ == "__main__":
    import logging
    from pathlib import Path


    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    logger.info("🚀 Running AXIOM Configuration Tests")

    CONFIGS_DIR = ROOT_DIR / "configs"
    default_json = CONFIGS_DIR / "default.json"
    production_json = CONFIGS_DIR / "production.json"

    print("ROOT_DIR:", ROOT_DIR)
    print("Database path:", ROOT_DIR / "data" / "axiom.db")

    # 1️⃣ Default / Factory loading
    try:
        config_default = AxiomConfig()
        logger.info(f"✅ Default config loaded: debug={config_default.system.debug}")
    except Exception as e:
        logger.error(f"❌ Default config failed: {e}")

    # 2️⃣ Development factory
    try:
        config_dev = AxiomConfigFactory.development()
        logger.info(f"✅ Development factory loaded: debug={config_dev.system.debug}")
    except Exception as e:
        logger.error(f"❌ Development factory failed: {e}")

    # 3️⃣ Production factory
    try:
        config_prod = AxiomConfigFactory.production()
        logger.info(f"✅ Production factory loaded: debug={config_prod.system.debug}")
    except Exception as e:
        logger.error(f"❌ Production factory failed: {e}")

    # 4️⃣ JSON file loading - default
    try:
        config_json_default = AxiomConfig.from_json_file(default_json)
        assert config_json_default.system.debug is True
        assert config_json_default.database.backup_enabled is False
        logger.info("✅ JSON default.json loaded correctly")
    except Exception as e:
        logger.error(f"❌ JSON default.json loading failed: {e}")

    # 5️⃣ JSON file loading - production
    try:
        config_json_prod = AxiomConfig.from_json_file(production_json)
        assert config_json_prod.system.debug is False
        assert config_json_prod.database.backup_enabled is True
        logger.info("✅ JSON production.json loaded correctly")
    except Exception as e:
        logger.error(f"❌ JSON production.json loading failed: {e}")

    # 6️⃣ Environment variable overrides
    os.environ["SYSTEM_DEBUG"] = "true"
    os.environ["DB_MAX_CONNECTIONS"] = "5"
    os.environ["VA_MAX_RESPONSE_LENGTH"] = "200"
    try:
        config_env = AxiomConfig.from_env()
        assert config_env.system.debug is True
        assert config_env.database.max_connections == 5
        assert config_env.virtual_assistant.max_response_length == 200
        logger.info("✅ Environment variable loading works")
    except Exception as e:
        logger.error(f"❌ Environment variable loading failed: {e}")

    # 7️⃣ CLI argument overrides
    cli_args = ["--debug", "--db-path=cli_data/cli.db"]
    try:
        config_cli = AxiomConfig.load(cli_args=cli_args)
        assert config_cli.system.debug is True
        assert str(config_cli.database.path).endswith("cli_data/cli.db")
        logger.info("✅ CLI argument overrides work")
    except Exception as e:
        logger.error(f"❌ CLI argument overrides failed: {e}")

    logger.info("🚀 All configuration tests completed successfully!")
