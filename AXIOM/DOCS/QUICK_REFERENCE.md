# AXIOM Quick Reference

## 🚀 Quick Start Commands

```bash
# Start AXIOM console
python -m axiom.console.cli

# Start with debug logging
python -m axiom.console.cli --debug

# View configuration
python -m axiom.main

# Run all tests
pytest

# Run with coverage
pytest --cov=src/axiom --cov-report=html

# Run feature demonstration
python demo_features.py
```

## 💻 REPL Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `health` | Run system health checks |
| `status` | Show system status |
| `history` | Display conversation history |
| `config` | View/update configuration |
| `clear` | Clear conversation history |
| `quit` / `exit` | Exit AXIOM |

## 📊 Error Codes Reference

### Event Bus (BUS-XXX)
- `BUS-001` - Event delivery failed
- `BUS-002` - Invalid event type
- `BUS-003` - Unregistered publisher
- `BUS-004` - Queue full
- `BUS-005` - Subscriber error
- `BUS-006` - Initialization failed

### State Management (STATE-XXX)
- `STATE-001` - Database connection failed
- `STATE-002` - Query failed
- `STATE-003` - Migration failed
- `STATE-004` - Transaction failed
- `STATE-005` - Invalid model
- `STATE-006` - Integrity error

### Policy Engine (POLICY-XXX)
- `POLICY-001` - Validation failed
- `POLICY-002` - Policy not found
- `POLICY-003` - Registration failed
- `POLICY-004` - Evaluation error
- `POLICY-005` - Blocked content
- `POLICY-006` - SQL injection detected
- `POLICY-007` - Invalid path

### Virtual Assistant (VA-XXX)
- `VA-001` - Intent detection failed
- `VA-002` - Response generation failed
- `VA-003` - Dialog manager error
- `VA-004` - Pipeline error
- `VA-005` - Context error

### Configuration (CONFIG-XXX)
- `CONFIG-001` - Load failed
- `CONFIG-002` - Invalid value
- `CONFIG-003` - Missing required
- `CONFIG-004` - Parse error
- `CONFIG-005` - File not found

### System (SYSTEM-XXX)
- `SYSTEM-001` - Initialization failed
- `SYSTEM-002` - Shutdown failed
- `SYSTEM-003` - Health check failed
- `SYSTEM-004` - Resource exhausted
- `SYSTEM-005` - Timeout

## 🎯 Health Check Status

| Status | Symbol | Meaning |
|--------|--------|---------|
| `HEALTHY` | ✓ | Component operating normally |
| `DEGRADED` | ⚠ | Component working but suboptimal |
| `UNHEALTHY` | ✗ | Component failure |

### Critical Components (Startup Blockers)
- Configuration
- Database

### Non-Critical Components (Warnings)
- Event Bus
- Policy Engine
- Dialog Manager
- Disk Space (warn <1GB, error <100MB)
- Memory (warn >80%, error >95%)

## 📝 Log Levels

| Level | Console | File | Use For |
|-------|---------|------|---------|
| `DEBUG` | ❌ | ✅ | Detailed debugging info |
| `INFO` | ❌ | ✅ | General information |
| `WARNING` | ✅ | ✅ | Warning messages |
| `ERROR` | ✅ | ✅ | Error conditions |
| `CRITICAL` | ✅ | ✅ | Critical failures |

**Log Location**: `logs/axiom.log`  
**Log Format**: JSON (structured)  
**Rotation**: 10MB max, 7 backups

## 🔒 Input Validation Rules

### SQL Injection Prevention
- Blocks: `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `UNION SELECT`
- Blocks: SQL comments (`--`, `/* */`)
- Blocks: Always-true conditions

### XSS Prevention
- Blocks: `<script>`, `javascript:`, event handlers
- Blocks: `<iframe>`, `<object>`, `<embed>`

### Path Traversal Prevention
- Blocks: `../`, `..\`
- Config paths must be within `configs/` directory

### Character Validation
- Max length: 500 characters
- Allowed: Alphanumeric + standard punctuation
- Allowed chars: `a-zA-Z0-9 .,!?-'"();:@#$%&*+=/[]{}`

## 🔄 Retry Configuration

- **Max Attempts**: 3
- **Backoff**: Exponential (1s, 2s, 4s)
- **Retryable Errors**:
  - Event delivery failures
  - Queue full
  - Database connection issues
  - Query failures
  - Timeouts
  - Resource exhaustion

## ⚙️ Configuration Files

| File | Purpose |
|------|---------|
| `configs/default.json` | Base configuration |
| `configs/production.json` | Production overrides |
| `configs/intents.json` | Intent patterns |
| `configs/eventbus.schema.json` | Event bus schema |

### Environment Variable Overrides
```bash
SYSTEM_DEBUG=true
DB_PATH=/custom/path/axiom.db
VA_MAX_RESPONSE_LENGTH=200
```

## 📦 Module Structure

```
axiom/
├── bus/           # Event bus system
├── state/         # State management
├── policy/        # Policy engine & validation
├── va/            # Virtual assistant
│   ├── intents/   # Intent detection
│   └── responses/ # Response generation
├── console/       # CLI & REPL
└── utils/         # Utilities
    ├── errors.py      # Error handling
    ├── logging.py     # Structured logging
    ├── health.py      # Health checks
    └── shutdown.py    # Graceful shutdown
```

## 🔌 API Usage Examples

### Error Handling
```python
from axiom.utils.errors import ErrorCode, EventBusError

error = EventBusError(
    error_code=ErrorCode.BUS_QUEUE_FULL,
    message="Queue at capacity",
    retry_allowed=True
)
```

### Logging
```python
from axiom.utils.logging import get_logger, PerformanceLogger

logger = get_logger(__name__)
logger.info("Operation started", user_id=123)

with PerformanceLogger(logger, "database_query"):
    result = db.query()
```

### Health Checks
```python
from axiom.utils.health import HealthChecker

checker = HealthChecker()
results = checker.check_all(
    event_bus=bus,
    state_store=store
)

if checker.is_healthy():
    print("All systems go!")
```

### Input Validation
```python
from axiom.policy.input_validation import InputSanitizationPolicyEnhanced
from axiom.policy.policies import PolicyContext

validator = InputSanitizationPolicyEnhanced()
context = PolicyContext(user_input=user_text)
result = validator.evaluate(context)

if not result.passed:
    print(f"Blocked: {result.violations}")
```

### Graceful Shutdown
```python
from axiom.utils.shutdown import register_shutdown_handler

register_shutdown_handler("database", lambda: db.close())
register_shutdown_handler("event_bus", bus.stop)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific module
pytest tests/bus/
pytest tests/policy/
pytest tests/va/

# Run with verbose output
pytest -v

# Run with debug output  
pytest -s

# Run specific test
pytest tests/bus/test_events.py::test_event_type_enum
```

## 📊 Performance Metrics

All operations automatically tracked:
- Event publish/subscribe
- Database queries
- Policy evaluations
- Dialog processing
- Response generation

Metrics logged with:
- `operation`: Operation name
- `duration_seconds`: Execution time
- `success`: True/False
- Additional context

## 🚨 Troubleshooting

### Logs not appearing
```bash
# Check log directory exists
ls -la logs/

# Check file permissions
chmod 755 logs/
```

### Database connection failed
```bash
# Check database file
ls -la data/axiom.db

# Check directory permissions
chmod 755 data/
```

### Import errors
```bash
# Reinstall in development mode
pip install -e .
```

### Tests failing
```bash
# Reinstall dependencies
pip install -e ".[dev]"

# Clear pytest cache
rm -rf .pytest_cache
```

## 📚 Documentation Links

- [System Diagrams](DOCS/SYSTEM_DIAGRAMS.md) - Visual architecture
- [Architecture](DOCS/ARCHITECTURE.md) - Design decisions
- [Implementation Summary](DOCS/IMPLEMENTATION_SUMMARY.md) - Feature details
- [Configuration Guide](DOCS/CONFIGURATION.md) - Config reference
- [Pub/Sub Model](DOCS/PUBSUB.md) - Event bus details

## 🆘 Support

- Check logs: `tail -f logs/axiom.log`
- Run health check: `health` command in REPL
- View test coverage: `pytest --cov=src/axiom --cov-report=html`
- Demo features: `python demo_features.py`

---

**Version**: 1.0.0  
**Last Updated**: November 9, 2025
