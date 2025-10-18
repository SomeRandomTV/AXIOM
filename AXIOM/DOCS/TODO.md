# AXIOM Phase 1 - Development TODO List

**Project:** AXIOM - Advanced eXtensible Interactive Operations Manager  
**Phase:** 1 - Virtual Assistant Core  
**Last Updated:** September 27, 2025  

---

## 🎯 Phase 1 Goals Recap

- ✅ **Virtual Assistant core** (no sensors yet)
- ✅ **Basic conversational interaction** via CLI
- ✅ **Event-driven architecture** with pub/sub
- ✅ **Persistent state** with SQLite
- ✅ **Modular design** for future expansion


## TODO: Urgent

### pytest/bus

- Implement Abstract class methods for other event types

```python
    def test_event_handler_type():
>       handler = EventHandler()
                  ^^^^^^^^^^^^^^
E       TypeError: Can't instantiate abstract class EventHandler without an implementation for abstract methods 'get_supported_events', 'handle_event'

tests/bus/test_handlers.py:5: TypeError
```

### pytest/policy

- Fix Import Error

```python
ImportError: cannot import name 'ContentFilterPolicy' from 'axiom.policy.policies' (/Users/retr0/Desktop/ZiaTechnica/ARA/AXIOM/src/axiom/policy/policies.py
```
### pytest/va

- test_event_bus_publish_subscribe: Import Asyncio
```python
    @pytest.mark.asyncio
    async def test_event_bus_publish_subscribe():
        bus = EventBus()
        received = []
        def handler(event):
            received.append(event.event_type)
        bus.register_publisher("test", [EventType.CONVERSATION_TURN.value])
        bus.subscribe(EventType.CONVERSATION_TURN.value, handler)
        await bus.publish(DummyEvent(EventType.CONVERSATION_TURN.value))
>       await asyncio.sleep(0.05)  # allow handler to run
              ^^^^^^^
E       NameError: name 'asyncio' is not defined. Did you forget to import 'asyncio'

tests/va/test_event_bus.py:19: NameError
```

- `test_pipeline_init`: type error
```python
    def test_pipeline_init():
        bus = EventBus()
>       pipeline = Pipeline(bus, patterns_dict=TEST_PATTERNS)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: Pipeline.__init__() got an unexpected keyword argument 'patterns_dict'

```

- `test_pipeline_session`: unexpected keyword argument 'patterns_dict'
```python

    def test_pipeline_session():
        bus = EventBus()
>       pipeline = Pipeline(bus, patterns_dict=TEST_PATTERNS)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: Pipeline.__init__() got an unexpected keyword argument 'patterns_dict'

tests/va/test_pipeline.py:25: TypeError


### Warnings Summary
```python
tests/va/test_pipeline.py:11
  /Users/retr0/Desktop/ZiaTechnica/ARA/AXIOM/tests/va/test_pipeline.py:11: PytestCollectionWarning: cannot collect test class 'TestPipeline' because it has a __init__ constructor (from: tests/va/test_pipeline.py)
    class TestPipeline(Pipeline):

tests/va/test_event_bus.py::test_event_bus_register
    def test_event_bus_register():

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
```
---

## 📋 Development Checklist

### 🏗️ **Foundation & Core Infrastructure**

#### Project Setup
- [X] Initialize Git repository with proper `.gitignore`
- [X] Create Python package structure (`axiom/`)
- [X] Set up `pyproject.toml` / `setup.py` for dependencies
- [X] Configure development tools (pytest, black, pylint)
- [X] Create `requirements.txt` with core dependencies
- [X] Set up virtual environment and development workflow

#### Configuration System
- [X] Implement `config.py` module
  - [X] Environment variable override support
  - [X] Command-line argument parsing
  - [X] Configuration validation and defaults
- [X] Create default configuration files
- [X] Add configuration schema documentation

### 🚌 **Event Bus Implementation**
#### Core Event System
- [X] Implement `bus/event_bus.py`
  - [X] In-memory pub/sub mechanism
  - [X] Thread-safe event handling
  - [X]summary Async event processing
  - [X] Event queuing and delivery guarantees
- [X] Create `bus/events.py` for event type definitions
- [X] Implement `bus/handlers.py` for built-in event handlers
- [ ] Add event correlation ID support
#### Event Types
- [X] Define `system.start` event structure
- [X] Define `conversation.turn` event structure
- [X] Add event validation and serialization
- [ ] Create event factory methods

### 🗄️ **State Store Implementation**

- [X] Implement `state/store.py` with SQLite integration
  - [X] Database connection management
  - [X] ACID transaction support
  - [X] Graceful error handling
- [X] Create `state/models.py` for data models
- [X] Implement database schema in `state/migrations/`

#### Schema & Migrations
- [X] Design Phase 1 database schema
  - [X] `conversations` table
  - [X] `system_events` table
  - [X] Future expansion tables (placeholder)
- [X] Implement database migration system
- [X] Create initial migration script (`v001_initial.py`)
- [X] Add schema versioning support

#### Data Access Methods
- [ ] Implement conversation logging methods
- [ ] Add conversation history retrieval
- [ ] Create system event logging
- [ ] Add query utilities and helpers
- [ ] Implement data cleanup and retention policies

### 🛡️ **Policy Engine Implementation**

#### Basic Framework
- [X] Implement `policy/engine.py`
  - [X] Policy evaluation framework
  - [X] Policy registration and management
  - [X] Policy result handling and logging
- [X] Create `policy/policies.py` with basic policies
  - [X] Response length validation
  - [X] Input sanitization policy
  - [X] Safety check policies

#### Validation System
- [X] Implement `policy/validators.py`
  - [X] Input validation utilities
  - [X] Response validation checks
  - [X] Policy violation handling
- [ ] Add policy configuration support
- [ ] Create policy audit logging

### 🤖 **Virtual Assistant Core**

#### Pipeline Architecture
- [X] Implement `va/pipeline.py` - main orchestration
  - [X] Input processing pipeline
  - [X] Component coordination
  - [X] Error handling and recovery
  - [ ] Performance monitoring
- [X] Create modular component interfaces
- [ ] Add pipeline configuration support

#### Dialog Manager
- [X] Implement `va/dm.py` - Dialog Manager
  - [X] Rule-based intent detection engine
  - [X] Context management system
  - [X] Response generation coordination
  - [X] Conversation state tracking
- [X] Create `va/intents/` module structure
  - [X] Base intent detection interface (`base.py`)
  - [X] Rule-based intent detector (`rules.py`)
  - [X] Intent definitions and patterns
- [X] Implement `va/responses/` module structure
  - [X] Base response generator interface (`base.py`)
  - [X] Template-based responses (`templates.py`)
  - [X] Response selection logic

#### Intent Detection (Rule-Based)
- [X] **Time queries** - "What time is it?", "What day is today?"
- [X] **Greetings** - "Hello", "Hi", "Good morning"
- [X] **Farewells** - "Goodbye", "See you later", "Bye"
- [X] **Caregiver notifications** - "Call my daughter", "Alert caregiver"
- [X] **Small talk** - Weather, how are you, general conversation
- [X] **Help requests** - "Help", "What can you do?"
- [X] Add intent confidence scoring
- [X] Create fallback intent for unrecognized input

#### Response Generation
- [X] Template-based response system
- [X] Context-aware response selection
- [ ] Personality and tone consistency
- [X] Response variation to avoid repetition
- [ ] Integration with policy validation

#### Optional Speech Components
- [ ] Implement `va/asr.py` - Automatic Speech Recognition
  - [ ] Whisper integration (optional)
  - [ ] Vosk integration (alternative, optional)
  - [ ] Audio input handling
  - [ ] Speech-to-text processing
- [ ] Implement `va/tts.py` - Text-to-Speech
  - [ ] gTTS integration (optional)
  - [ ] Coqui TTS integration (alternative, optional)
  - [ ] Audio output handling
  - [ ] Voice configuration options

### 💻 **Console Interface**

#### CLI Framework
- [X] Implement `console/cli.py`
  - [X] Command-line argument parsing
  - [X] Interactive mode vs. command mode
  - [X] Session management
  - [X] Graceful shutdown handling
- [X] Create `console/repl.py` - Read-Eval-Print Loop
  - [X] Interactive conversation mode
  - [X] Command history support
  - [ ] Tab completion for commands
  - [ ] Multi-line input support
- [ ] Implement `console/commands.py`
  - [ ] Built-in command handlers
  - [ ] Help system integration
  - [ ] Administrative commands

#### Built-in Commands
- [X] **`help`** - Show available commands and usage
- [X] **`quit`** / **`exit`** - Graceful system shutdown
- [X] **`history`** - Show recent conversation history
- [X] **`status`** - Display system status and health
- [X] **`clear`** - Clear screen/conversation context
- [ ] **`config`** - Show current configuration
- [ ] Add command validation and error handling

#### User Experience
- [X] Design clear, intuitive prompt format
- [ ] Add colored output support (optional)
- [ ] Implement progress indicators for long operations
- [ ] Create startup banner and system information
- [ ] Add conversation context indicators

### 🔧 **System Bootstrap & Integration**

#### Main Entry Point
- [X] Implement `core.py` - System bootstrap
  - [X] Component initialization sequence
  - [ ] Dependency injection setup
  - [X] Configuration loading and validation
  - [X] Graceful startup and shutdown
- [ ] Create `run.py` - Application entry point
- [X] Add command-line interface integration
- [ ] Implement health check system

#### Component Integration
- [ ] Wire all components through event bus
- [ ] Implement component lifecycle management
- [ ] Add inter-component communication patterns
- [ ] Create system status monitoring
- [ ] Add performance metrics collection

### 🧪 **Testing Infrastructure**

#### Unit Tests
- [X] Test framework setup with pytest
- [X] **Event Bus tests**
  - [X] Pub/sub functionality
  - [X] Thread safety
  - [ ] Event delivery guarantees
- [X] **State Store tests**
  - [X] Database operations
  - [X] Migration scripts
  - [X] Data integrity
- [X] **Policy Engine tests**
  - [X] Policy evaluation
  - [X] Validation logic
  - [ ] Policy combinations
- [X] **Virtual Assistant tests**
  - [X] Intent detection accuracy
  - [X] Response generation
  - [X] Pipeline orchestration
- [X] **Console Interface tests**
  - [X] Command parsing
  - [X] REPL functionality
  - [ ] User interaction flows

#### Integration Tests
- [ ] End-to-end conversation flow
- [ ] Component interaction testing
- [ ] Database integration validation
- [ ] Error handling and recovery
- [ ] Performance benchmarks

#### Test Infrastructure
- [ ] Mock frameworks setup
- [ ] Test data management
- [ ] Database test isolation
- [ ] Automated test execution
- [ ] Coverage reporting (target: >80%)

### 📚 **Documentation**

#### User Documentation
- [ ] **`README.md`** - Quick start and usage guide
  - [ ] Installation instructions
  - [ ] Basic usage examples
  - [ ] Configuration options
  - [ ] Troubleshooting guide
- [ ] **`ARCHITECTURE.md`** - System design overview
- [ ] **`REQUIREMENTS.md`** - Detailed requirements specification

#### Developer Documentation
- [ ] API documentation for all components
- [ ] Code comments and docstrings
- [ ] Architecture decision records (ADRs)
- [ ] Development setup guide
- [ ] Contributing guidelines

#### Configuration Documentation
- [ ] Configuration parameter reference
- [ ] Example configuration files
- [ ] Environment variable documentation
- [ ] Deployment guide

### 🚀 **Deployment & Packaging**

#### Packaging
- [ ] Create installable Python package
- [ ] Define package dependencies
- [ ] Add entry point scripts
- [ ] Create distribution packages (wheel, source)

#### Deployment Support
- [ ] Installation scripts for different platforms
- [ ] Docker container support (optional)
- [ ] Service/daemon configuration examples
- [ ] Database initialization scripts

### 🐛 **Error Handling & Monitoring**

#### Logging System
- [ ] Implement `utils/logging.py`
  - [ ] Structured logging configuration
  - [ ] Multiple log levels and destinations
  - [ ] Log rotation and retention
  - [ ] Performance-aware logging
- [ ] Add logging throughout all components
- [ ] Create debugging and troubleshooting logs

#### Error Handling
- [ ] Comprehensive exception handling
- [ ] Graceful degradation for component failures
- [ ] User-friendly error messages
- [ ] Error recovery mechanisms
- [ ] Circuit breaker implementation for optional components

#### Health Monitoring
- [ ] Component health checks
- [ ] System status endpoints
- [ ] Performance metrics collection
- [ ] Resource usage monitoring

### 🔒 **Security & Privacy**

#### Input Security
- [ ] Input sanitization and validation
- [ ] SQL injection prevention
- [ ] Command injection protection
- [ ] Rate limiting for abuse prevention

#### Data Protection
- [ ] File permission configuration
- [ ] Database access controls
- [ ] Audit trail implementation
- [ ] Data minimization practices
- [ ] Privacy-preserving logging

---

## ⚡ **Priority Order (Development Phases)**

### **Phase 1A: Foundation** (Week 1-2)
1. Project setup and development environment
2. Configuration system implementation
3. Event bus core implementation
4. Basic database schema and state store

### **Phase 1B: Core Components** (Week 3-4)
1. Policy engine framework (basic stub)
2. Virtual Assistant pipeline structure
3. Dialog Manager with basic rule-based intents
4. Console interface and REPL

### **Phase 1C: Integration & Polish** (Week 5-6)
1. Component integration and system bootstrap
2. End-to-end conversation flow
3. Error handling and monitoring
4. Basic testing infrastructure

### **Phase 1D: Documentation & Testing** (Week 7-8)
1. Comprehensive testing suite
2. Documentation completion
3. Performance optimization
4. Deployment packaging and release preparation

---

## 🎯 **Success Criteria**

- [ ] **Functional CLI Virtual Assistant** - Users can have basic conversations
- [ ] **Persistent Conversation History** - All interactions logged to SQLite
- [ ] **Event-Driven Architecture** - Components communicate via events
- [ ] **Modular Design** - Components can be easily extended or replaced
- [ ] **Cross-Platform Support** - Runs on Linux, macOS, and Windows
- [ ] **Basic Policy Enforcement** - Content filtering and validation
- [ ] **Comprehensive Testing** - >80% code coverage with unit and integration tests
- [ ] **Complete Documentation** - Architecture, API, and user guides

---

## 🔮 **Future Preparation (Not in Phase 1)**

*Items to keep in mind for architecture but not implement yet:*

- Sensor data processing infrastructure
- Advanced ML/NLP integration hooks  
- Caregiver notification system
- Web dashboard interface
- Multi-user session management
- Distributed deployment support
- HIPAA compliance framework
- Advanced context management

---

**Note:** This TODO list should be updated regularly as development progresses. Mark completed items with ✅ and add new discoveries or requirements as they emerge.