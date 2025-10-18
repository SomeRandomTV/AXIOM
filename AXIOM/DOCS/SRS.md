# AXIOM Phase 1 - Software Requirements Specification

**Document Version:** 1.0  
**Date:** September 27, 2025  
**Project:** AXIOM Core Runtime  
**Phase:** 1 - Virtual Assistant Core  
**Author:** Alejandro Rubio

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) defines the requirements for AXIOM Phase 1, the core runtime component of the ARA (Adaptive Real-Time Assistant) system. This document serves as the primary reference for development, testing, and validation activities.

### 1.2 Scope
AXIOM Phase 1 provides a foundational Virtual Assistant core with basic conversational interaction capabilities, event-driven architecture, and persistent state management. This phase excludes sensor integration, which will be addressed in subsequent phases.

### 1.3 Document Conventions
- **SHALL/MUST**: Mandatory requirement
- **SHOULD**: Recommended requirement
- **MAY**: Optional requirement
- **Core Component**: Essential system module
- **Stub Implementation**: Basic framework for future expansion

### 1.4 Product Overview
AXIOM serves as the central runtime for the ARA system, implementing a modular, extensible architecture designed to support future expansion with sensor integration, machine learning capabilities, and advanced healthcare compliance features.

---

## 2. Overall Description

### 2.1 Product Functions
- **Virtual Assistant Interface**: Speech-To-Text(STT) & Text-To-Speech(TTS) / messaging, conversational interaction, via App(later phases), and Speakers
- **Event Management**: Pub/sub event bus for component communication
- **State Persistence**: SQLite-based storage for conversation history and system state
- **Policy Enforcement**: Basic guardrails and compliance framework
- **Extensible Architecture**: Modular design supporting future enhancements

### 2.2 User Classes and Characteristics
- **Primary Users**: Developers and system administrators
- **Technical Proficiency**: Intermediate to advanced technical users
- **Usage Context**: Development, testing, and initial deployment environments

### 2.3 Operating Environment
- **Operating Systems**: Linux, macOS, Windows, (future ARKOS)
- **Runtime**: Python 3.10 or higher
- **Database**: SQLite (embedded)
- **Deployment**: Local-only processing (no cloud dependencies)

### 2.4 Constraints and Assumptions
- **Privacy-First**: All processing must occur locally
- **No External Dependencies**: No cloud services or external APIs required
- **Backward Compatibility**: Future phases must maintain compatibility with Phase 1 interfaces
- **Resource Constraints**: Must operate efficiently on standard desktop/laptop hardware

---

## 3. Functional Requirements

### 3.1 Virtual Assistant (VA) Component

#### 3.1.1 Input Processing
**REQ-VA-001**: The system SHALL accept speech and/or text
- **Priority**: Extremely High
- **Input Format**: UTF-8 text strings / float32 np.ndarry audio
- **Response Time**: < 500ms for input processing

**REQ-VA-002**: The system SHALL support speech input via Automatic Speech Recognition (ASR).
- **Priority**: Low
- **Supported Engines**: Whisper, Vosk, or equivalent
- **Audio Format**: WAV, MP3, or standard audio formats

#### 3.1.2 Dialog Management
**REQ-VA-003**: The system SHALL implement rule-based intent detection for the following categories:
- **Priority**: High
- Time-related queries
- Greeting interactions
- Caregiver notifications
- Small talk conversations
- 
**REQ-VA-004**: The system SHALL generate appropriate responses using templated or rule-based methods.
- **Priority**: Extremely High
- **Response Quality**: Contextually appropriate and grammatically correct
- **Main Engine:** Ollama
 
**REQ-VA-005**: The dialog management system SHALL be designed to support future integration of ML/NLP capabilities.
- **Priority**: Medium
- **Architecture**: Plugin-based or modular interface for ML integration

#### 3.1.3 Output Generation
**REQ-VA-006**: The system MAY provide text-based responses to all user interactions(via CLI or APP).
- **Priority**: Medium
- **Format**: Human-readable text in UTF-8 encoding

**REQ-VA-007**: The system SHALL support speech synthesis for audio output.
- **Priority**: Extremely High
- **Supported Engines**: gTTS, Coqui TTS, or equivalent
- **Output Format**: WAV or standard audio formats

#### 3.1.4 Conversation Logging
**REQ-VA-008**: The system SHALL log all user inputs, assistant responses, and detected intents to persistent storage.
- **Priority**: High
- **Data Elements**: User text, assistant text, intent classification, timestamp
- **Storage**: LOCAL SQLite database

### 3.2 System Bus Component

#### 3.2.1 Event Architecture
**REQ-BUS-001**: The system SHALL implement an event-driven publish/subscribe messaging model.
- **Priority**: High
- **Pattern**: Observer pattern with event routing

**REQ-BUS-002**: The system SHALL support the following core events in Phase 1:
- `system.start`: System initialization
- `system.shutdown`: System termination
- `conversation.turn`: Each dialog interaction
- **Priority**: High

**REQ-BUS-003**: The event bus SHALL support registration of multiple subscribers for each event type.
- **Priority**: High
- **Scalability**: Support for 10+ concurrent subscribers

### 3.3 State Store Component

#### 3.3.1 Database Requirements
**REQ-STATE-001**: The system SHALL use SQLite as the primary persistence mechanism.
- **Priority**: High
- **File Location**: Configurable database file path
- **Backup**: Support for database backup/restore operations

**REQ-STATE-002**: The database schema SHALL store conversation history with the following minimum fields:
- User input text
- Assistant response text
- Intent classification
- Timestamp
- Session identifier
- **Priority**: High

**REQ-STATE-003**: The database schema SHALL be designed to accommodate future expansion for:
- Sensor data storage
- Alert/notification logs
- User preference storage
- System configuration data
- **Priority**: Medium

### 3.4 Policy Engine Component

#### 3.4.1 Guardrails Implementation
**REQ-POLICY-001**: The system SHALL implement a basic policy engine to enforce response guardrails.
- **Priority**: Medium
- **Implementation**: Stub with expansion framework

**REQ-POLICY-002**: The policy engine SHALL prevent generation of disallowed responses or actions.
- **Priority**: Medium
- **Examples**: Inappropriate content, harmful advice, privacy violations

**REQ-POLICY-003**: The policy engine SHALL provide an expansion path for HIPAA and privacy compliance requirements.
- **Priority**: EXTREMELY HIGHT
- **Design**: Modular architecture supporting compliance modules

### 3.5 Console Interface Component

#### 3.5.1 CLI Implementation
**REQ-CLI-001**: The system SHALL provide a command-line REPL (Read-Eval-Print Loop) interface.
- **Priority**: EXTREMELY High
- **Platform**: Cross-platform compatibility required

**REQ-CLI-002**: The CLI SHALL support the following commands:
- `help`: Display available commands and usage
- `quit` or `exit`: Graceful system shutdown
- **Priority**: High

**REQ-CLI-003**: The default CLI mode SHALL be conversational interaction.
- **Priority**: High
- **Behavior**: Direct text input processed as conversation

---

## 4. Non-Functional Requirements

### 4.1 Extensibility
**REQ-NFR-001**: The system architecture SHALL be modular to support component replacement and upgrades.
- **Metric**: Components replaceable without core system modification
- **Priority**: High

### 4.2 Portability
**REQ-NFR-002**: The system SHALL operate on Linux, macOS, and Windows platforms.
- **Requirement**: Python 3.10+ compatibility
- **Testing**: All platforms must pass integration tests
- **Priority**: High

### 4.3 Reliability
**REQ-NFR-003**: The system SHALL handle unexpected input gracefully without crashes.
- **Metric**: 99.9% uptime during normal operation
- **Error Handling**: All exceptions caught and logged
- **Priority**: High

### 4.4 Privacy and Security
**REQ-NFR-004**: The system SHALL process all data locally without external cloud dependencies.
- **Verification**: No network calls during normal operation
- **Data Residency**: All data remains on local storage
- **Priority**: EXTREMELY High

### 4.5 Performance
**REQ-NFR-005**: The system SHALL respond to user input within 2 seconds under normal conditions.
- **Metric**: 95th percentile response time < 2s
- **Load**: Up to 100 conversation turns per session
- **Priority**: Medium

### 4.6 Testability
**REQ-NFR-006**: All core components SHALL have comprehensive unit test coverage.
- **Coverage Target**: Minimum 80% code coverage
- **Components**: Bus, State Store, VA, Policy Engine
- **Priority**: High

---

## 5. Interface Requirements

### 5.1 User Interfaces
- **CLI Interface**: Text-based command-line interaction
- **Error Messages**: Clear, actionable error descriptions
- **Help System**: Comprehensive command documentation

### 5.2 Hardware Interfaces
- **Microphone** (optional): For speech input functionality
- **Speakers** (optional): For speech output functionality
- **Storage**: Minimum 100MB for database and logs

### 5.3 Software Interfaces
- **Python Runtime**: Version 3.10 or higher
- **SQLite**: Version 3.31 or higher
- **Optional ASR/TTS Libraries**: As specified in VA requirements

---

## 6. Quality Assurance Requirements

### 6.1 Testing Requirements
- **Unit Tests**: All components must have isolated unit tests
- **Integration Tests**: End-to-end system functionality validation
- **Platform Tests**: Verification on all supported operating systems
- **Performance Tests**: Response time and resource usage validation

### 6.2 Documentation Requirements
- **README.md**: Quick start guide and basic usage instructions
- **ARCHITECTURE.md**: System design and module overview
- **REQUIREMENTS.md**: This requirements specification
- **API Documentation**: Generated documentation for all public interfaces

---

## 7. Deliverables

### 7.1 Software Components
1. **Working CLI Virtual Assistant Core**: Complete conversational interface
2. **SQLite-backed Conversation Logging**: Persistent state management
3. **Event Bus with Pub/Sub**: Inter-component communication system
4. **Policy Engine Stub**: Basic guardrails framework

### 7.2 Documentation Package
1. **README.md**: Installation and usage guide
2. **ARCHITECTURE.md**: Technical design documentation
3. **REQUIREMENTS.md**: This specification document
4. **Test Documentation**: Unit and integration test guides

### 7.3 Acceptance Criteria
- All functional requirements implemented and tested
- Non-functional requirements verified through testing
- Documentation complete and reviewed
- Cross-platform compatibility confirmed
- Unit test coverage meets minimum threshold

---

## 8. Appendices

### 8.1 Glossary
- **ARA**: Adaptive Robotic Assistant
- **AXIOM**: Core runtime system
- **CLI**: Command Line Interface
- **REPL**: Read-Eval-Print Loop
- **VA**: Virtual Assistant

### 8.2 References
- Python 3.10+ Documentation
- SQLite Documentation
- Event-Driven Architecture Patterns
- Healthcare IT Compliance Guidelines (for future phases)

---

**End of Document**