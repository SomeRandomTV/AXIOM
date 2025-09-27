import argparse
import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# BROKEN CONFIG SYSTEM - FIX ME!

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    username: str = "admin"
    password: str = None  # PROBLEM: Secret in code!, load from env
    ssl: bool = False


@dataclass
class APIConfig:
    timeout: int = 30
    retries: int = 3
    rate_limit: int = 100
    api_key: str = "secret-api-key"  # PROBLEM: Another secret!, load from env


@dataclass
class AppConfig:
    debug: bool = False
    database: DatabaseConfig = DatabaseConfig()
    api: APIConfig = APIConfig()


class BrokenConfigManager:
    """This config manager has many problems - fix them!"""

    def load_config(self, cli_config = Optional[argparse.Namespace]):
        # PROBLEM: Only loads from one source
        config = AppConfig()
        file_config = None # replace wtih load_from_file
        env_config = None # replace with load_from_env
        cli_config = None


        # PROBLEM: No error handling
        try:
            with open("config.json") as f:
                data = json.load(f)
        except FileNotFoundError as error:
            print(f"Error loading config: {error}")


        # PROBLEM: No type conversion or validation
        config.debug = data.get("debug", False)
        config.database.host = data.get("db_host", "localhost")
        config.database.port = data.get("db_port", 5432)  # What if it's a string?

        return config


# EXERCISE 1: Environment Variable Loading
def exercise_1():
    """
    Make this function load config from environment variables.

    Environment variables to support:
    - APP_DEBUG (boolean)
    - APP_DB_HOST (string)
    - APP_DB_PORT (integer)
    - APP_DB_SSL (boolean)
    - APP_API_TIMEOUT (integer)

    Handle type conversion and errors gracefully.
    """
    # YOUR CODE HERE
    pass


# EXERCISE 2: Configuration Validation
def exercise_2():
    """
    Create a validator that checks:
    - Database port is between 1 and 65535
    - API timeout is positive
    - API rate_limit is between 1 and 10000
    - Required fields are not empty

    Raise meaningful errors for invalid configs.
    """
    # YOUR CODE HERE
    pass


# EXERCISE 3: Secret Management
def exercise_3():
    """
    Remove hardcoded secrets and load them safely:
    - Try environment variables first
    - Fall back to a secrets file
    - Never log or print secrets
    - Handle missing secrets gracefully
    """
    # YOUR CODE HERE
    pass


# EXERCISE 4: Configuration Merging
def exercise_4():
    """
    Create a merge function that combines configs in priority order:
    1. CLI arguments (highest)
    2. Environment variables
    3. Config file
    4. Defaults (lowest)

    Handle nested dictionaries properly.
    """
    # YOUR CODE HERE
    pass


# EXERCISE 5: Testing Configuration
def exercise_5():
    """
    Write tests for your configuration system:
    - Test environment variable loading
    - Test validation logic
    - Test error handling
    - Test configuration merging
    """
    # YOUR CODE HERE
    pass


if __name__ == "__main__":
    print("Configuration Management Exercises")
    print("==================================")
    print()
    print("Fix the broken config manager above!")
    print("Complete exercises 1-5 to build a robust system.")
    print()

    # Test the broken system
    try:
        broken_manager = BrokenConfigManager()
        config = broken_manager.load_config()
        print("❌ Broken config 'worked' - but it shouldn't!")
    except Exception as e:
        print(f"❌ Broken config failed as expected: {e}")

    print()
    print("Now implement the exercises to fix it! 🚀")


# BONUS CHALLENGES (Advanced)

def bonus_challenge_1():
    """
    Hot Configuration Reload

    Implement a system that:
    - Watches config files for changes
    - Reloads configuration automatically
    - Notifies application components
    - Handles reload errors gracefully
    """
    pass


def bonus_challenge_2():
    """
    Configuration Profiles

    Support multiple environments:
    - development.yaml
    - staging.yaml
    - production.yaml

    Load the right profile based on APP_ENV variable.
    """
    pass


def bonus_challenge_3():
    """
    Configuration Schema

    Define a JSON Schema or Pydantic model for your config.
    Validate all loaded configurations against the schema.
    Generate documentation from the schema.
    """
    pass


# SOLUTIONS TEMPLATE
"""
Here's how I'd approach this:

1. Start with Exercise 1 - get environment variables working
2. Add type conversion with proper error handling  
3. Build validation logic (Exercise 2)
4. Tackle secrets management (Exercise 3)
5. Implement configuration merging (Exercise 4)
6. Write comprehensive tests (Exercise 5)

Key principles:
- Fail fast with clear error messages
- Never expose secrets in logs/errors
- Make it easy to test different configurations  
- Follow the principle of least surprise
- Document environment variables and their types

Want me to walk through my solution for any exercise?
"""