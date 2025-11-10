# AXIOM Architecture Decision Records (ADR)

**Project**: AXIOM - AI Assistant Orchestration Engine  
**Version**: 1.0  
**Date**: November 9, 2025  
**Status**: Draft

---

## Executive Summary

AXIOM is a Python-based orchestration engine for AI assistant ecosystems, designed to run on edge devices with local inference capabilities. The system uses an event-driven architecture with pub/sub messaging, SQLite-backed state persistence, policy-based validation, and a complete voice assistant processing pipeline.

**Deployment Context**: Edge device with local database, heavy inference workloads, integration with external devices (Raspberry Pi with computer vision models).

---

## ADR-001: Event Bus Architecture

### Status
**IMPLEMENTED** (Core functionality) / **PLANNED** (Advanced features)

### Context
AXIOM requires a robust event-driven architecture to coordinate between multiple components (Dialog Manager, Intent Detection, State Store, Policy Engine) while maintaining loose coupling and enabling extensibility.

### Decision

#### Event Format
- **Format**: JSON
- **Standard Event Envelope**:
  ```json
  {
    "id": "evt_<uuid>",
    "timestamp": "ISO8601 datetime",
    "type": "namespace.category.action",
    "payload": {},
    "metadata": {
      "session_id": "string",
      "user_id": "string",
      "source": "component_name",
      "priority": "integer",
      "trace_id": "string"
    }
  }
  ```

#### Event Naming Convention
- **Namespaced hierarchy**: `domain.category.action`
- Examples:
  - `audio.input.received`
  - `dialog.intent.detected`
  - `system.error.occurred`
  - `cv.object.detected` (future: computer vision events)
  - `policy.validation.failed`

#### Pub/Sub Model
- **Type**: Topic-based publish/subscribe
- **Asynchronous**: All event handling is non-blocking
- **Delivery Guarantees**: 
  - At-least-once delivery for critical events
  - Exactly-once delivery for state-changing events (using idempotency keys)
- **Subscription**: Configuration-based registration

#### Event Persistence & Processing
- **Current**: Events are processed in-memory, no write-ahead logging
- **Future**: Persist events to disk before processing for durability
- **Future**: Dead Letter Queue (DLQ) for failed events after max retries

#### Event Bus Implementation
```python
# Current implementation
class EventBus:
    def publish(event: Event) -> None  # async
    def subscribe(event_type: str, handler: Callable) -> None
    def register_publisher(publisher_id: str, event_types: List[str]) -> None
```

**Note**: Delivery guarantees, event persistence, and DLQ are planned features not yet implemented.

### Consequences

**Positive**:
- Loose coupling between components
- Clear audit trail of events
- Easy to extend with new event types
- Async processing prevents blocking

**Future Benefits**:
- Event persistence will enable replay and debugging
- DLQ will improve reliability
- Support for external event sources (CV models, sensors)

---

## ADR-002: State Management Strategy

### Status
**IMPLEMENTED** (Core functionality) / **PLANNED** (Advanced concurrency)

### Context
AXIOM runs on an edge device with limited resources. State must be persisted locally using SQLite and handle concurrent access patterns.

### Decision

#### Database Configuration
- **Database**: SQLite 3 in WAL (Write-Ahead Logging) mode
- **Location**: Local edge device storage
- **File**: Single database file `axiom.db` (configurable)

#### Concurrency Strategy
**Current Implementation**:
- Direct SQLite access with connection pooling (max 5 connections)
- Thread-safe operations using locks
- WAL mode enabled for better concurrency

**Future Enhancement - Single Writer Queue Pattern**:
- Dedicated writer thread for all write operations
- Background queue for sequential state changes
- Bounded write queue (max 10,000 pending operations)

```python
# Current implementation
class StateStore:
    def __init__(self, db_path: Path, pool_size: int = 5):
        self._db_path = db_path
        self._lock = Lock()
        self._connections: List[Connection] = []
        
    def log_conversation_turn(self, turn: ConversationTurn) -> None:
        # Direct write with connection pooling
```

#### State Structure
**Current Implementation** - Direct table storage:

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_input TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    detected_intent TEXT,
    processing_time INTEGER,
    timestamp TEXT NOT NULL,
    metadata TEXT
);

CREATE TABLE system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    component TEXT NOT NULL,
    description TEXT,
    severity TEXT,
    timestamp TEXT NOT NULL,
    metadata TEXT
);
```

**Future Enhancement** - JSON document storage with versioning for complex state.

#### Caching Strategy
**Current**: No in-memory caching - direct SQLite queries

**Future Enhancement - In-Memory LRU Cache**:
- Cache active session states in memory
- Size: 1,000 most recently accessed sessions
- Write-through: Updates written to both cache and SQLite
- Invalidation: 30-minute TTL + explicit on session end

#### Transaction Management
**Current**: Simple transactions with context managers
```python
with self._get_connection() as conn:
    conn.execute(INSERT_CONVERSATION, turn.to_db_tuple())
    conn.commit()
```

**Future**: Optimistic concurrency with version fields

### Consequences

**Positive**:
- Simple, reliable SQLite persistence
- WAL mode provides good read performance
- Connection pooling handles concurrent access
- Works well on resource-constrained edge devices
- State survives system restarts

**Future Benefits**:
- Single writer queue will improve write throughput
- In-memory cache will reduce disk I/O
- Optimistic concurrency will enable better scaling

---

## ADR-003: Plugin/Extension System

### Status
**PLANNED** (Not yet implemented)

### Context
AXIOM will need to support extensibility through plugins for custom intents, integrations, and processing logic in future versions. This ADR outlines the planned architecture.

### Decision

#### Plugin Registration
**Configuration-Based Registration** using `plugins.yaml`:

```yaml
plugins:
  - name: weather_plugin
    module: axiom.plugins.weather
    enabled: true
    priority: 10
    subscribes_to:
      - dialog.intent.weather
      - dialog.intent.forecast
    configuration:
      api_key: "${WEATHER_API_KEY}"
      timeout: 5
      
  - name: calendar_plugin
    module: axiom.plugins.calendar
    enabled: true
    priority: 5
    subscribes_to:
      - dialog.intent.schedule
      - dialog.intent.reminder
    configuration:
      calendar_path: "/data/calendar.ics"
      
  - name: cv_integration_plugin
    module: axiom.plugins.cv_bridge
    enabled: true
    priority: 8
    subscribes_to:
      - cv.object.detected
      - cv.face.recognized
    configuration:
      raspberry_pi_host: "192.168.1.100"
      confidence_threshold: 0.75
```

#### Plugin Lifecycle

**Five-Phase Lifecycle**:

1. **Load Phase**
   - Import plugin module
   - Validate plugin class structure
   - Check dependencies

2. **Initialize Phase**
   - Call `plugin.setup(config)`
   - Initialize API clients, load models
   - Validate configuration

3. **Register Phase**
   - Subscribe to event topics
   - Register intent handlers
   - Add middleware hooks

4. **Execute Phase**
   - Process subscribed events
   - Publish response events
   - Update state as needed

5. **Cleanup Phase**
   - Call `plugin.teardown()`
   - Close connections
   - Release resources

#### Plugin Interface

**Standard Plugin Class**:
```python
from axiom.plugin import BasePlugin

class WeatherPlugin(BasePlugin):
    def setup(self, config: dict) -> None:
        """Initialize plugin with configuration"""
        self.api_key = config['api_key']
        self.timeout = config['timeout']
        self.weather_api = WeatherAPI(self.api_key)
    
    def handle_event(self, event: Event) -> None:
        """Process subscribed events"""
        if event.type == 'dialog.intent.weather':
            self._handle_weather_intent(event)
    
    def _handle_weather_intent(self, event: Event) -> None:
        location = event.payload['entities'].get('location')
        weather = self.weather_api.get_weather(location)
        
        # Publish response event
        self.publish('dialog.response.ready', {
            'session_id': event.metadata['session_id'],
            'text': f"Weather in {location}: {weather}",
            'completed': True
        })
    
    def teardown(self) -> None:
        """Cleanup resources"""
        self.weather_api.close()
```

#### Extension Points

**Plugins can hook into**:
1. **Event Handlers**: Subscribe to any event topic
2. **Pipeline Middleware**: Pre/post processing for ASR, Dialog, TTS
3. **Intent Handlers**: Register custom intent implementations
4. **Policy Validators**: Add custom validation rules
5. **State Transformers**: Transform state before/after persistence

#### Plugin Communication
- **Event-based only**: Plugins communicate via publish/subscribe
- **No direct calls**: Plugins cannot directly call other plugins
- **Shared state**: Access only through StateManager API
- **Isolation**: Each plugin runs in its own context

#### Plugin Priority & Ordering
- Priority: Integer (1-100, higher = earlier execution)
- Multiple plugins can subscribe to same event
- Execution order: Priority descending, then alphabetical by name
- Parallel execution: Plugins with same priority run concurrently

### Consequences

**Positive**:
- Easy to add new functionality without core changes
- Configuration-based enables/disables plugins
- Clear separation of concerns
- Plugin isolation prevents cascading failures
- Future CV integration straightforward

**Negative**:
- Configuration complexity grows with plugin count
- Event-only communication can be verbose
- Plugin debugging can be challenging

**Risks**:
- Plugin crashes affecting system stability (mitigated with error boundaries)
- Plugin resource leaks (mitigated with lifecycle management)
- Event loop blocking from slow plugins (mitigated with async execution)

---

## ADR-004: Error Handling & Recovery

### Status
**PARTIALLY IMPLEMENTED**

### Context
AXIOM runs on an edge device and must gracefully handle failures while maintaining user experience and state consistency. Basic error handling is in place with plans for advanced features.

### Decision

#### Error Strategy
**Current Implementation**:
- Basic exception handling in all components
- Policy validation errors with clear messages
- Logging throughout the system
- Graceful fallbacks for intent detection

**Future Enhancements**:
- Structured error events via event bus
- Retry logic with exponential backoff
- Circuit breaker pattern for external services
- Dead letter queue for failed events

#### Error Classification

**Four Error Categories**:

1. **UserError**
   - Invalid input, unrecognized commands
   - Ambiguous requests
   - Response: Polite clarification request
   - No retry, no logging (normal operation)

2. **SystemError**
   - Internal bugs, unexpected states
   - Data corruption, logic errors
   - Response: Fallback behavior + error event
   - Logging: Full stack trace, context dump

3. **ExternalServiceError**
   - ASR/TTS timeouts or failures
   - API rate limits, network issues
   - Response: Retry with backoff + fallback
   - Logging: Service name, error code, retry count

4. **PolicyViolation**
   - Security rules violated
   - Rate limits exceeded
   - Response: Policy denial message
   - Logging: Policy rule, violation details

#### Error Propagation

**Hybrid: Error Events + Limited Exceptions**:

```python
# Normal errors → Publish error events
event_bus.publish('system.error.occurred', {
    'error_type': 'ExternalServiceError',
    'component': 'ASR',
    'message': 'Timeout after 5s',
    'session_id': 'sess_123',
    'retry_count': 2
})

# Fatal errors → Throw exceptions (stop processing)
if state_corrupted:
    raise FatalStateError("Cannot recover conversation state")
```

#### Retry Logic

**Future Implementation - Exponential Backoff with Jitter**:

```python
retry_config = {
    'external_services': {
        'max_retries': 3,
        'base_delay': 1.0,  # seconds
        'max_delay': 10.0,
        'exponential_base': 2,
        'jitter': True
    }
}
```

**Note**: Retry logic and circuit breakers are planned for when external services (ASR/TTS/APIs) are integrated.

#### Circuit Breaker Pattern

**Future Implementation - For External Services**:

```python
# Planned for ASR, TTS, and external API integration
circuit_breaker_config = {
    'failure_threshold': 5,
    'timeout': 30,
    'half_open_timeout': 60,
    'success_threshold': 2
}
```

**Note**: Circuit breakers will be implemented when external service dependencies are added.

#### Fallback Behaviors

**Current Implementation**:

| Component | Failure | Fallback |
|-----------|---------|----------|
| Intent Detection | Low confidence | Return generic/default response |
| Intent Detection | No match | Default "help" or "unknown" response |
| Policy Validation | Violation | Deny with policy violation message |
| State Persistence | Write failed | Log error, continue operation |

**Future Fallbacks** (when external services added):

| Component | Failure | Fallback |
|-----------|---------|----------|
| ASR | Timeout/Error | Prompt user to type text input |
| TTS | Synthesis failed | Return text-only response |
| External API | Unavailable | Use cached data or apologize gracefully |

#### State Rollback

**Future Enhancement - Transactional State Updates**:
```python
# Planned for complex state management
class StateManager:
    def update_with_rollback(self, session_id, update_fn):
        previous_state = self.get_state(session_id).copy()
        try:
            new_state = update_fn(previous_state)
            self.persist(session_id, new_state)
            return new_state
        except Exception as e:
            self.persist(session_id, previous_state)
            raise
```

**Current**: Simple exception handling with logging

#### Observability

**Current Implementation**:
- Python logging module with file output
- Structured error messages
- Policy validation logging
- Event bus activity logging

**Future Enhancement - Structured JSON Logging**:
```json
{
  "timestamp": "2025-11-09T10:30:00.123Z",
  "level": "ERROR",
  "component": "DialogManager",
  "session_id": "sess_xyz789",
  "message": "Intent detection failed",
  "metadata": {...}
}
```

**Planned Metrics**:
- Error rate by category
- Intent detection accuracy
- Response time percentiles
- Policy violation frequency

### Consequences

**Current Benefits**:
- Clear error categorization
- Graceful handling of failures
- Comprehensive logging for debugging
- Policy validation prevents harmful operations

**Future Benefits**:
- Resilient to external service failures
- Automatic recovery without intervention
- Advanced observability and metrics
- Circuit breakers prevent cascading failures

---

## ADR-005: Edge Deployment Architecture

### Status
**PARTIALLY IMPLEMENTED** / **PLANNED**

### Context
AXIOM is designed to run on edge devices with local database. Current implementation focuses on dialog management and intent detection. Future versions will add local inference models and external device integration.

### Decision

#### Deployment Model
**Current Implementation**:
- Single-process Python application
- Async I/O for event handling
- SQLite local persistence
- CLI/REPL interface

**Future Enhancement**:
- Thread pool for concurrent event processing
- Dedicated threads for specialized tasks

#### Resource Constraints
**Design for Edge** (targets):
- **Memory**: 512MB - 2GB footprint
- **CPU**: Optimize for ARM processors
- **Storage**: Local SSD/eMMC
- **Network**: Intermittent connectivity assumed

#### Local Inference
**Future Implementation**:
- ASR/TTS models on-device (Whisper, Piper, Coqui)
- Lightweight local intent detection models
- Fallback to cloud services when available
- Model quantization for efficiency (INT8, FP16)

**Current**: Rule-based intent detection (no ML models)

#### External Device Integration
**Future - Raspberry Pi CV Integration**:
- CV events published to AXIOM event bus
- Communication: HTTP/WebSocket or MQTT
- Event types: `cv.object.detected`, `cv.face.recognized`
- Loose coupling: CV device optional, not required

**Current**: No external device integration

#### Data Persistence
**Current Implementation**:
- SQLite database on local storage
- No cloud synchronization required
- Conversation and event logging
- Schema migrations supported

### Consequences

**Current Benefits**:
- Works offline, no cloud dependency
- Privacy-preserving (data stays on device)
- Simple deployment model
- Efficient resource usage

**Future Benefits**:
- Low latency with local ML inference
- Scalable with external event sources
- Robust with thread pool architecture

---

## Implementation Priorities

### Phase 1: Core Infrastructure ✅ **COMPLETED**
1. Event Bus with async handling
2. State Manager with SQLite and WAL mode
3. Basic error handling and logging
4. Dialog Manager and intent detection
5. Policy engine with validation
6. Console interface (CLI/REPL)

### Phase 2: Testing & Documentation ✅ **COMPLETED**
1. Comprehensive pytest test suite
2. Architecture documentation
3. Configuration system

### Phase 3: Advanced Features 🚧 **IN PROGRESS**
1. Performance monitoring
2. Enhanced error recovery
3. Conversation history in console

### Phase 4: External Integration 📋 **PLANNED**
1. ASR integration (Whisper)
2. TTS integration (Piper/Coqui)
3. Plugin system
4. Circuit breakers and retry logic

### Phase 5: Edge Optimization 📋 **PLANNED**
1. ML model integration
2. Model quantization
3. Resource monitoring
4. CV device integration (Raspberry Pi)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-09 | Team | Initial ADR document |

---

## Appendix A: Event Type Registry

### Core System Events
- `system.startup.complete`
- `system.shutdown.initiated`
- `system.error.occurred`
- `system.health.check`

### Audio Events
- `audio.input.received`
- `audio.output.ready`

### ASR Events
- `asr.transcription.started`
- `asr.transcription.complete`
- `asr.transcription.failed`

### Dialog Events
- `dialog.turn.started`
- `dialog.intent.detected`
- `dialog.response.generated`
- `dialog.clarification.needed`

### Policy Events
- `policy.validation.passed`
- `policy.validation.failed`
- `policy.violation.logged`

### State Events
- `state.updated`
- `state.rollback`
- `state.session.created`
- `state.session.ended`

### TTS Events
- `tts.synthesis.started`
- `tts.synthesis.complete`
- `tts.synthesis.failed`

### Computer Vision Events (Future)
- `cv.object.detected`
- `cv.face.recognized`
- `cv.motion.detected`
- `cv.scene.analyzed`

---

## Appendix B: Configuration Schema

### Main Configuration (`axiom.yaml`)
```yaml
axiom:
  version: "1.0"
  environment: "production"  # development, staging, production
  
  event_bus:
    persistence_path: "/data/events"
    max_queue_size: 10000
    dlq_path: "/data/dlq"
    retention_days: 7
    
  state_manager:
    database_path: "/data/axiom_state.db"
    wal_mode: true
    cache_size: 1000
    cache_ttl_seconds: 1800
    write_queue_size: 10000
    
  plugins:
    config_path: "/etc/axiom/plugins.yaml"
    plugin_directory: "/opt/axiom/plugins"
    
  logging:
    level: "INFO"  # DEBUG, INFO, WARNING, ERROR
    format: "json"
    output: "/var/log/axiom/axiom.log"
    rotation: "daily"
    max_size_mb: 100
    
  error_handling:
    retry_max_attempts: 3
    retry_base_delay: 1.0
    circuit_breaker_enabled: true
    
  edge:
    inference_device: "cpu"  # cpu, cuda, mps
    model_path: "/opt/axiom/models"
    low_power_mode: false
```

---

*End of Architecture Decision Records*