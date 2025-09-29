# AXIOM Configuration Schema

AXIOM uses a hierarchical configuration system with the following precedence:

1. Default values (dataclass defaults)
2. JSON configuration files (`default.json`, `production.json`)
3. Environment variables
4. Command-line arguments

---

## Sections

### `system`
| Key             | Type     | Default          | Description                          |
|-----------------|----------|-----------------|--------------------------------------|
| debug           | bool     | true             | Enable debug mode                     |
| data_directory  | str/Path | "data"           | Directory for storing data            |
| log_directory   | str/Path | "logs"           | Directory for log files               |
| version         | str      | "1.0.0-dev"      | System version                        |
| startup_timeout | int      | 30               | Max startup time in seconds           |

### `database`
| Key             | Type     | Default          | Description                          |
|-----------------|----------|-----------------|--------------------------------------|
| path            | str/Path | "data/axiom.db" | Path to SQLite database               |
| backup_enabled  | bool     | false            | Enable automatic backup               |
| backup_interval | str      | "24h"            | Backup interval                       |
| max_connections | int      | 2                | Max database connections              |

### `virtual_assistant`
| Key                  | Type | Default | Description                           |
|----------------------|------|---------|---------------------------------------|
| response_timeout      | int  | 60      | Timeout for assistant responses       |
| max_context_length    | int  | 256     | Max number of conversation turns      |
| max_response_length   | int  | 150     | Max tokens in a single response       |

### `policy`
| Key        | Type        | Default        | Description                          |
|------------|------------|----------------|--------------------------------------|
| max_tokens | int        | 1000           | Maximum tokens per response           |
| temperature| float      | 0.9            | AI temperature / creativity          |
| stop       | list[str]  | ["TEST_STOP"]  | Stop sequences for AI                 |

---

## Environment Variable Mapping

| Config Key                       | Env Variable Example |
|----------------------------------|--------------------|
| system.debug                      | SYSTEM_DEBUG       |
| database.max_connections          | DB_MAX_CONNECTIONS |
| virtual_assistant.max_response_length | VA_MAX_RESPONSE_LENGTH |
| policy.temperature                | POLICY_TEMPERATURE |

---

## Usage Examples

```python
from axiom.config import AxiomConfig

# Load default JSON
config = AxiomConfig.from_json_file("configs/default.json")

# Load production JSON
config = AxiomConfig.from_json_file("configs/production.json")

# Override with environment variables
config_env = AxiomConfig.from_env()

# Load defaults + CLI args
config_cli = AxiomConfig.load(cli_args=["--debug", "--db-path=cli_data/cli.db"])
