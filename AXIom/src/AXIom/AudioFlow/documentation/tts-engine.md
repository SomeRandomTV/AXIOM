
# Enhanced TTSHandler Module

## Overview

`TTSHandler` is an enhanced Python class designed to provide high-quality text-to-speech (TTS) synthesis using multiple engines. It now supports:

- **Coqui TTS** for high-quality local synthesis with real-time streaming
- **gTTS** for cloud-based synthesis as fallback
- **Real-time audio streaming** with chunk-based processing
- **Cross-platform audio playback** with PyAudio integration
- **Hybrid approach** with automatic fallback mechanisms

This module provides efficient in-memory audio streaming, local synthesis capabilities, and fallback playback methods, making it versatile across different platforms and use cases.

---

## Features

### Core TTS Capabilities
- **Local TTS Synthesis** using Coqui TTS (no internet required)
- **Cloud TTS Synthesis** using Google Text-to-Speech (gTTS)
- **Real-time Streaming** with configurable chunk sizes
- **Hybrid Engine Selection** with automatic fallback
- **Performance Monitoring** and statistics

### Audio Output Options
- **Synthesize to WAV/MP3 files** using best available engine
- **Synthesize to memory** as audio bytes
- **Direct audio playback** using PyAudio
- **System audio player** fallback

### Streaming Capabilities
- **Chunk-based text processing** for real-time synthesis
- **Sentence boundary detection** for natural speech flow
- **Audio queue management** for smooth playback
- **Configurable chunk sizes** for different use cases

---

## Installation

### Required Dependencies

```bash
# Core TTS libraries
pip install TTS gTTS

# Audio playback
pip install pyaudio

# Deep learning backend (for Coqui TTS)
pip install torch torchaudio

# Additional dependencies
pip install numpy
```

### System Requirements

- **Python 3.8+** (for Coqui TTS compatibility)
- **FFmpeg** (optional, for enhanced audio playback)
- **Audio drivers** (for PyAudio functionality)

### Platform-Specific Installation

#### macOS
```bash
# Install audio dependencies
brew install portaudio
pip install pyaudio

# Install Coqui TTS
pip install TTS
```

#### Ubuntu/Debian
```bash
# Install system dependencies
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio TTS
```

#### Windows
```bash
# PyAudio and TTS should install directly
pip install pyaudio TTS
```

---

## Usage

### Basic Initialization

```python
from tts_handler import TTSHandler

# Initialize with local TTS priority
tts = TTSHandler(
    lang='en',
    use_local=True,      # Prioritize local synthesis
    streaming=True,       # Enable real-time streaming
    voice_model=None     # Auto-select best model
)
```

### Local TTS Synthesis

```python
# Use local Coqui TTS for high-quality synthesis
tts.speak("Hello! This uses local TTS for fast, private synthesis.")

# Force local synthesis
tts.speak("This text will use local TTS.", use_local=True)

# Synthesize to file
file_path = tts.synthesize_to_file("Save this audio locally.")
print(f"Audio saved to: {file_path}")

# Synthesize to memory
audio_bytes = tts.synthesize_to_bytes("Get audio as bytes.")
```

### Real-time Streaming

```python
# Stream text with automatic chunking
tts.stream_speak(
    "This is a long text that will be processed in real-time chunks. "
    "Each chunk is synthesized and played as it becomes available.",
    chunk_size=50  # Characters per chunk
)

# Stop streaming if needed
tts.stop_streaming()
```

### Cloud TTS Fallback

```python
# Force cloud TTS
tts.speak("This uses Google TTS.", use_local=False)

# Synthesize to file with cloud TTS
file_path = tts.synthesize_to_file("Cloud synthesis.", use_local=False)
```

### Performance Monitoring

```python
# Get performance statistics
stats = tts.get_performance_stats()
print(f"Average synthesis time: {stats['avg_synthesis_time']:.2f}s")
print(f"Local TTS available: {stats['local_tts_available']}")
print(f"Total syntheses: {stats['total_syntheses']}")
```

---

## Advanced Configuration

### Voice Model Selection

```python
# Use specific Coqui TTS model
tts = TTSHandler(
    voice_model="tts_models/en/ljspeech/fast_pitch",
    use_local=True
)

# Check available models
if tts.coqui_tts:
    print(f"Available models: {tts.available_models}")
```

### Streaming Configuration

```python
# Customize streaming behavior
tts = TTSHandler(
    streaming=True,
    use_local=True
)

# Adjust chunk size for different use cases
tts.stream_speak(text, chunk_size=30)   # Small chunks for real-time
tts.stream_speak(text, chunk_size=100)  # Larger chunks for efficiency
```

### Error Handling and Fallback

```python
try:
    # Try local TTS first
    tts.speak("This should work locally.")
except Exception as e:
    print(f"Local TTS failed: {e}")
    # Automatic fallback to cloud TTS
    tts.speak("Using cloud TTS as fallback.")
```

---

## Architecture

### Engine Selection Priority

1. **Local Coqui TTS** (if available and requested)
2. **Cloud gTTS** (fallback option)
3. **System audio players** (ffplay, afplay, etc.)

### Streaming Pipeline

```
Text Input → Chunking → Synthesis → Audio Queue → Playback
    ↓           ↓         ↓          ↓          ↓
  Long text  Sentences  Coqui TTS  Buffering  PyAudio
```

### Fallback Chain

```
Local TTS → Cloud TTS → File-based → System Player
    ↓           ↓           ↓           ↓
  Coqui     Google TTS   Temp file   Default app
```

---

## Performance Characteristics

### Local vs Cloud TTS

| Feature | Local (Coqui) | Cloud (gTTS) |
|---------|---------------|--------------|
| **Latency** | 50-200ms | 500ms-2s |
| **Privacy** | 100% local | Text sent to Google |
| **Quality** | High | Very High |
| **Reliability** | Depends on hardware | High |
| **Cost** | Free | Free (with limits) |

### Streaming Performance

- **Chunk processing**: 10-50ms per chunk
- **Audio playback**: Real-time with minimal buffering
- **Memory usage**: Configurable based on chunk size
- **CPU usage**: Moderate during synthesis, low during playback

---

## Troubleshooting

### Common Issues

#### Coqui TTS Not Available
```bash
# Install TTS library
pip install TTS

# Check Python version (requires 3.8+)
python --version
```

#### PyAudio Installation Issues
```bash
# macOS
brew install portaudio
pip install pyaudio

# Ubuntu/Debian
sudo apt-get install portaudio19-dev
pip install pyaudio

# Windows
pip install pyaudio
```

#### Audio Playback Problems
```python
# Check system audio
tts = TTSHandler(use_local=False)  # Force cloud TTS
tts.speak("Test audio playback")

# Verify audio drivers
import pyaudio
audio = pyaudio.PyAudio()
print(f"Available devices: {audio.get_device_count()}")
```

### Performance Optimization

```python
# Use appropriate chunk sizes
tts.stream_speak(text, chunk_size=30)   # Real-time applications
tts.stream_speak(text, chunk_size=100)  # Efficiency-focused

# Preload models for repeated use
tts = TTSHandler(use_local=True)
# Model is loaded once and reused
```

---

## Examples

### Complete Streaming Example

```python
from tts_handler import TTSHandler
import time

# Initialize streaming TTS
tts = TTSHandler(use_local=True, streaming=True)

# Stream long text
long_text = """
This is a demonstration of real-time streaming text-to-speech synthesis.
The system processes text in chunks and plays audio as it becomes available,
providing a responsive and natural speaking experience.
"""

print("Starting streaming TTS...")
tts.stream_speak(long_text, chunk_size=40)

# Wait for completion
time.sleep(5)

# Get performance stats
stats = tts.get_performance_stats()
print(f"Performance: {stats}")

# Cleanup
tts.cleanup()
```

### Hybrid TTS with Fallback

```python
def speak_with_fallback(text, prefer_local=True):
    """Speak text with automatic fallback."""
    tts = TTSHandler(use_local=prefer_local, streaming=False)
    
    try:
        tts.speak(text)
    except Exception as e:
        print(f"Primary TTS failed: {e}")
        if prefer_local:
            print("Falling back to cloud TTS...")
            tts.speak(text, use_local=False)
        else:
            print("Falling back to local TTS...")
            tts.speak(text, use_local=True)
    
    tts.cleanup()

# Usage
speak_with_fallback("Hello, this is ARA speaking.")
```

---

## License

This module is open source and free to use under the MIT License.

---

## Author

Created by Alejandro Rubio @ [ZiaTechnica](www.ziatechnica.org)

---

## Contact

For questions or feedback, please contact: [alejoserubio@gmail.com]

