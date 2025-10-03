# AXIOM: ARA's eXecution & Intent Orchestration Machine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](https://pytest.org/)

AXIOM is the core orchestration engine powering **A.R.A. (Adaptive Real-Time Assistant)**, a sophisticated AI assistant ecosystem. It provides a modular, event-driven framework designed for scalable execution, intelligent state management, policy enforcement, and seamless virtual assistant interactions.

## 🌟 Key Features

- **🚌 Event Bus Architecture** – Pub/sub event-driven system enabling decoupled, scalable communication
- **💾 Persistent State Management** – SQLite-based persistence with migrations and structured schema models
- **🛡️ Policy Engine** – Built-in rule evaluation with comprehensive input/output validation
- **🤖 Virtual Assistant Core** – Complete processing pipeline including ASR, Dialog Management, TTS, intent detection, and response generation
- **💻 Interactive Console** – Feature-rich CLI tools and REPL for live debugging and system management
- **🔧 Utility Suite** – Centralized logging, validation helpers, and shared utilities

## 📁 Project Architecture

```
axiom/
├── 📄 pyproject.toml          # Project configuration and dependencies
├── 📄 requirements.txt        # Production dependencies
├── 🚀 run.py                  # Main application entrypoint
├── 📖 README.md               # Project documentation
├── 📝 CHANGELOG.md            # Version history and updates
├── 🙈 .gitignore             # Git ignore patterns
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
├── ⚙️ config/                 # Configuration files
├── 🧪 tests/                  # Test suites (unit & integration)
├── 📚 docs/                   # Documentation
├── 📊 data/                   # Data storage and assets
├── 📋 logs/                   # Application logs
└── 🔨 bin/                    # Executable scripts
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10 or higher**
- **pip** or [Poetry](https://python-poetry.org/) for dependency management

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/axiom-project.git
cd axiom-project

# Install dependencies
pip install -r requirements.txt

# For development (optional)
pip install -r requirements-dev.txt
```

### Running AXIOM

```bash
# Start the AXIOM orchestration engine
python run.py

# Alternative: Run with specific configuration
python run.py --config production
```

## 🧪 Testing

AXIOM includes comprehensive test coverage with both unit and integration tests:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/axiom --cov-report=html

# Run specific test categories
pytest tests/unit/        # Unit tests only
pytest tests/integration/ # Integration tests only
```

## ⚙️ Configuration

AXIOM uses a flexible configuration system supporting multiple environments:

- **Configuration files**: Located in `config/` directory
  - `default.json` – Base configuration
  - `production.json` – Production overrides
  - `development.json` – Development settings

Configuration is managed through `axiom/config.py` with automatic environment detection and value merging.

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
- **ASR** (Automatic Speech Recognition)
- **Dialog Management** with context awareness
- **TTS** (Text-to-Speech) synthesis
- **Intent Detection** and classification
- **Response Generation** and formatting

### 💻 Console Interface (`console/`)
Developer tools and system management:
- Interactive REPL for live debugging
- CLI commands for system operations
- Real-time monitoring and diagnostics

### 🔧 Utilities (`utils/`)
Shared infrastructure components:
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

Comprehensive documentation is available in the `docs/` directory:

- **[Architecture Overview](DOCS/ARCHITECTURE.md)** – System design and component interactions
- **[Developer Guide](DOCS/SRS.md)** – Software Requirement Specification


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

