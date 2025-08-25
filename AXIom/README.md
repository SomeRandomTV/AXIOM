# ARA Virtual Assistant AKA The AXIOM 1.0
**Authors:** Alejandro Rubio, David Escobar  
**Company:** ZiaTechnica

---

## Overview

**AXIOM** is a Python-based virtual assistant designed to process voice or text commands, automate tasks, and integrate with external services. It is structured with modular components for speech recognition, natural language understanding, task automation, and plugin extensibility.

---

## Features

- **Voice Recognition (STT):** Captures and transcribes user speech for hands‑free interaction.
- **Text Processing (NLP/Regex):** Parses and classifies text commands into intents and parameters.
- **Text-to-Speech (TTS):** Delivers verbal responses via an offline or cloud-based engine.
- **Task Automation:** Schedules reminders and retrieves useful information.
- **Memory Management:** Remembers user preferences and context across sessions.
- **Extensibility:** Plugin-based architecture for adding new skills and integrations.

---

## Setup Instructions

### Prerequisites

- **Python ≥ 3.9** must be installed.
- Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

### File Structure

```
main.py                       # Entry point of the assistant
CmdCraft/
  ├── cmd_handler.py          # Parses input and dispatches function calls
  ├── prompt_handler.py       # Handles prompt engineering for LLMs
  └── function-handler/       # Logic for executing assistant functions
  └── helpers/
      ├── scheduler.py        # Adds events to user’s Google Calendar
      └── user_handler.py     # Manages user accounts and preferences
AudioFlow/                    # Handles TTS and microphone I/O
  └── mic_handler.py          # Records and Transcibes mic audio
  └── tts_engine.py           # Builds/generates the TTS output
```

> **Note:**  
> `user_handler.py` and `scheduler.py` are helper modules called from within `function-handler` and are **not** entry points.

---

## Functionality

### Core Components

1. **Speech-to-Text (STT)**
   - *(Done)* Captures audio input via microphone.
   - *(In-progress)* Supports offline (`SpeechRecognition`, `pyaudio`) and cloud-based STT (OpenAI Whisper, Google STT).
   - *(In-progress)* Includes text normalization (noise filtering, punctuation).

2. **Natural Language Processing (NLP / Regex)**
   - *(In-progress)* Currently using Regex for intent/parameter extraction *(to be upgraded to NLP)*.
   - Identifies commands like `get_weather`, `create_user`, `schedule`.
   - *(Planned)* Supports context tracking for follow-up queries.

3. **Text-to-Speech (TTS)**
   - Uses ElevenLabs for audio responses.
   - *(Planned)* Configurable voice parameters (speed, pitch).
   - *(Planned)* Queued responses to prevent overlap.

4. **Task Automation**
   - **Scheduler:** Create/list/cancel tasks and reminders.
   - *(Planned)* Advanced reminders: snooze, repeat.
   - *(in-progress)* External services: calendar, messaging, IoT.

5. **Memory Management** *(Planned)*
   - Store user data (name, preferences, tasks) in JSON or SQLite.
   - Auto-load on startup and save on state changes.
   - Accessible API for all modules.

---

### Architecture & Design

- **Modular Structure:** Each major component in its own file and associated library.

```mermaid
graph TB
    %% Main Application Layer
    subgraph "Main Application Layer"
        MAIN[main.py<br/>Application Orchestrator<br/>Main Loop & Signal Handling]
    end

    %% AudioFlow Module
    subgraph "AudioFlow Module"
        MIC[MicHandler<br/>Speech Recognition<br/>Whisper AI Integration]
        TTS[TTSHandler<br/>Text-to-Speech<br/>gTTS + Audio Playback]
        AUDIO_CACHE[Model Cache<br/>Whisper Models]
    end

    %% CmdCraft Module
    subgraph "CmdCraft Module"
        CMD[CommandHandler<br/>Slash Command Parsing<br/>Function Dispatch]
        PROMPT[PromptHandler<br/>Ollama LLM Integration<br/>Chat Management]
        FUNC[FunctionHandler<br/>External API Calls<br/>Weather, News, Stocks]
        NLP[Command Handler NLP<br/>Natural Language Processing]
    end

    %% Helpers Module
    subgraph "Helpers Module"
        OLLAMA[OllamaManager<br/>AI Service Management<br/>Process Lifecycle]
        SCHEDULER[Scheduler<br/>Task Scheduling<br/>Google Calendar Integration]
    end

    %% External Services
    subgraph "External Services"
        OLLAMA_SERVICE[Ollama AI Service<br/>Local LLM Models]
        WEATHER_API[Weather API<br/>WeatherStack]
        NEWS_API[News API<br/>NewsAPI.org]
        GOOGLE[Google Services<br/>OAuth & Calendar]
    end

    %% Configuration & Environment
    subgraph "Configuration"
        CONFIG[config.py<br/>Environment Variables<br/>API Keys]
        SECRETS[Secrets Directory<br/>Credentials & Keys]
    end

    %% Data Flow
    MAIN --> MIC
    MAIN --> TTS
    MAIN --> CMD
    MAIN --> PROMPT
    MAIN --> OLLAMA

    MIC --> AUDIO_CACHE
    TTS --> AUDIO_CACHE

    CMD --> FUNC
    CMD --> NLP
    PROMPT --> OLLAMA_SERVICE

    FUNC --> WEATHER_API
    FUNC --> NEWS_API
    FUNC --> GOOGLE

    OLLAMA --> OLLAMA_SERVICE
    SCHEDULER --> GOOGLE

    CONFIG --> FUNC
    CONFIG --> PROMPT
    SECRETS --> CONFIG

    %% Styling
    classDef mainLayer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef audioFlow fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef cmdCraft fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef helpers fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef external fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef config fill:#f1f8e9,stroke:#33691e,stroke-width:2px

    class MAIN mainLayer
    class MIC,TTS,AUDIO_CACHE audioFlow
    class CMD,PROMPT,FUNC,NLP cmdCraft
    class OLLAMA,SCHEDULER helpers
    class OLLAMA_SERVICE,WEATHER_API,NEWS_API,GOOGLE external
    class CONFIG,SECRETS config
```


