# AXIOM: ARA's eXecution & Intent Orchestration Machine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](https://pytest.org/)

AXIOM is the core orchestration engine powering **A.R.A. (Adaptive Real-Time Assistant)**, a sophisticated AI assistant ecosystem. It provides a modular, event-driven framework designed for scalable execution, intelligent state management, policy enforcement, and seamless virtual assistant interactions.

## 🌟 Key Features

- **🚌 Event Bus Architecture** – Pub/sub event-driven system enabling decoupled, scalable communication
- **💾 Persistent State Management** – SQLite-based persistence with WAL mode and schema migrations
- **🛡️ Policy Engine** – Built-in rule evaluation with comprehensive input/output validation
- **🤖 Virtual Assistant Core** – Complete dialog management pipeline with intent detection and response generation
- **💻 Interactive Console** – Feature-rich CLI and REPL for live interaction and system management
- **🧪 Comprehensive Testing** – Full pytest suite with unit and integration tests

## 📁 Project Architecture

```
axiom/
├── 📄 pyproject.toml          # Project configuration and dependencies
├── 📄 setup.py                # Setup script
├── 🚀 src/axiom/main.py       # Configuration demonstration
├── 📖 README.md               # Project documentation
├── 🙈 .gitignore              # Git ignore patterns
│
├── 📂 src/
│   └── 📂 axiom/
│       ├── 🔧 __init__.py     # Package initialization
│       ├── ⚙️ core.py         # Core orchestration logic
│       ├── 🔐 config.py       # Configuration management
│       ├── ❌ exceptions.py   # Custom exception classes
│       ├── 🚌 bus/            # Event bus implementation
│       ├── 💾 state/          # State management and persistence
│       ├── 🛡️ policy/         # Policy engine and rules
│       ├── 🤖 va/             # Virtual assistant components
│       ├── 💻 console/        # CLI and REPL interfaces
│       └── 🔧 utils/          # Shared utilities and helpers
│
├── ⚙️ configs/                # Configuration files
├── 🧪 tests/                  # Test suites (unit tests)
├── 📚 DOCS/                   # Documentation
├── 📊 data/                   # Data storage (SQLite database)
└── 📋 logs/                   # Application logs
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11 or higher**
- **pip** for dependency management

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/axiom-project.git
cd axiom-project

# Install in development mode (recommended)
pip install -e .

# Or install with optional CLI dependencies
pip install -e ".[cli]"

# For development with testing tools
pip install -e ".[dev]"
```

### Running AXIOM

```bash
# Start the interactive REPL console
python -m axiom.console.cli

# With debug logging
python -m axiom.console.cli --debug

# View configuration examples
python -m axiom.main
```

### Using the Console

Once in the REPL, you can:
- **Chat with the assistant**: Just type your message
- **View history**: Type `history` to see conversation log
- **Check status**: Type `status` for system information
- **View config**: Type `config` to see current settings
- **Get help**: Type `help` for available commands
- **Exit**: Type `quit` or `exit`

Multi-line input is supported - end with a blank line.

## 🧪 Testing

AXIOM includes comprehensive test coverage with pytest:

```bash
# Install the package first
pip install -e .

# Run all tests
pytest

# Run with coverage report
pytest --cov=src/axiom --cov-report=html

# Run specific test modules
pytest tests/va/          # Virtual assistant tests
pytest tests/bus/         # Event bus tests
pytest tests/state/       # State management tests
pytest tests/policy/      # Policy engine tests
pytest tests/console/     # Console interface tests

# Run with verbose output
pytest -v

# Run with debug output
pytest -s
```

## ⚙️ Configuration

AXIOM uses a flexible configuration system supporting multiple environments:

- **Configuration files**: Located in `configs/` directory
  - `default.json` – Base configuration
  - `production.json` – Production overrides

- **Environment variables**: Override any config value
  - `SYSTEM_DEBUG=true`
  - `DB_PATH=/custom/path/axiom.db`
  - `VA_MAX_RESPONSE_LENGTH=200`

- **Command-line arguments**: 
  - `--debug` – Enable debug logging

Configuration is managed through `axiom.config` module with automatic environment detection and value merging. See [`DOCS/CONFIGURATION.md`](DOCS/CONFIGURATION.md) for full schema.

## 🏗️ Core Modules

### 🚌 Event Bus (`bus/`)
Event-driven communication system enabling loose coupling between components:
- Publisher/Subscriber pattern implementation
- Event routing and filtering
- Asynchronous event handling

### 💾 State Management (`state/`)
Persistent data layer with enterprise-grade features:
- SQLite database integration
- Schema migrations and versioning
- Model definitions and query builders
- Transaction management

### 🛡️ Policy Engine (`policy/`)
Security and validation framework:
- Configurable rule evaluation
- Input/output validation
- Access control enforcement
- Custom policy extensions

### 🤖 Virtual Assistant (`va/`)
Complete AI assistant processing pipeline:
- **Dialog Management** with context awareness
- **Intent Detection** using rule-based patterns
- **Response Generation** with template system
- **Event Publishing** for conversation tracking

**Future Enhancements:**
- ASR (Automatic Speech Recognition)
- TTS (Text-to-Speech) synthesis

### 💻 Console Interface (`console/`)
Developer tools and system management:
- Interactive REPL for conversations
- CLI commands for system operations
- Command history and tab completion
- Multi-line input support

### 🔧 Utilities (`utils/`)
Shared infrastructure components (planned):
- Centralized logging system
- Validation helpers and decorators
- Common utility functions

## 🛡️ Security & Policy Framework

AXIOM implements a robust policy system that evaluates all actions before execution, ensuring:

- **System Integrity** – Prevents harmful operations
- **Access Control** – Enforces user permissions
- **Safe Interactions** – Validates all inputs and outputs
- **Extensibility** – Custom policies via the `policy/` module

## 📖 Documentation

Comprehensive documentation is available in the `DOCS/` directory:

- **[System Diagrams](DOCS/SYSTEM_DIAGRAMS.md)** – Visual architecture and flow diagrams
- **[Architecture Overview](DOCS/ARCHITECTURE.md)** – System design and component interactions
- **[Implementation Summary](DOCS/IMPLEMENTATION_SUMMARY.md)** – Phase 1 features and usage
- **[Software Requirements](DOCS/SRS.md)** – Software Requirement Specification
- **[Configuration Guide](DOCS/CONFIGURATION.md)** – Configuration schema and examples
- **[Pub/Sub Model](DOCS/PUBSUB.md)** – Event bus architecture
- **[TODO List](DOCS/TODO.md)** – Development roadmap and progress


## 🏢 Project Ecosystem

AXIOM is part of the broader A.R.A. ecosystem:

```
A.R.A. (Adaptive Real-Time Assistant)
├── AXIOM (Core Orchestration Engine)
├   ├── Event Bus Module
├   ├── State Management Module
├   ├── Policy Engine Module
├   ├── Virtual Assistant Module
├   └── Console Interface Module
├── Auralens(Other stuff)
└── ARKOS/ARKS (Other other stuff)
```

