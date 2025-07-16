
# TTSHandler Module

## Overview

`TTSHandler` is a Python class designed to convert text to speech (TTS) using the Google Text-to-Speech (`gTTS`) library. It provides functionality to synthesize speech to an MP3 file or directly into memory as bytes, and can play the audio using system utilities or subprocesses for fast playback.

This module supports efficient in-memory audio streaming and fallback playback methods, making it versatile across different platforms.

---

## Features

- **Synthesize text to speech and save as MP3 file**  
- **Synthesize text to speech and return audio bytes in-memory**  
- **Play audio files using system default audio player**  
- **Fast in-memory playback using `ffplay` (FFmpeg) or `afplay` (macOS)**  
- **Fallback playback to temporary MP3 file if in-memory playback fails**  
- **Detailed logging for debugging and monitoring**

---

## Installation

Make sure you have the following installed:

- Python 3.6+
- `gtts` library  
- `ffmpeg` (for `ffplay`) if you want fast playback  
- Optional: `afplay` is preinstalled on macOS for audio playback

Install dependencies with:

```bash
pip install gtts
```

Ensure `ffmpeg` is installed and accessible in your system `PATH` for `ffplay`:

- On macOS: `brew install ffmpeg`
- On Ubuntu/Debian: `sudo apt install ffmpeg`
- On Windows: Download from [FFmpeg official site](https://ffmpeg.org/download.html)

---

## Usage

### Initialize TTSHandler

```python
from tts_handler import TTSHandler

tts = TTSHandler(lang='en', slow=False)
```

- `lang`: Language code (default `'en'`)  
- `slow`: Whether to speak slowly (default `False`)  

---

### Synthesize speech to MP3 file

```python
mp3_path = tts.synthesize_to_file("Hello world!")
print(f"Audio saved at: {mp3_path}")
```

---

### Synthesize speech to bytes (in-memory)

```python
audio_bytes = tts.synthesize_to_bytes("Hello world!")
# Use audio_bytes as needed (e.g., stream, save, or play)
```

---

### Play audio file

```python
tts.play_audio(mp3_path)
```

This opens the audio file with the system's default audio player.

---

### Speak text with fast playback and fallback

```python
tts.speak("Hello, this is ARA speaking.")
```

- Attempts to play audio in-memory using `ffplay` or `afplay`.
- Falls back to playing a temporary MP3 file if in-memory playback fails.
- Prints the spoken text prefixed with `ARA:`.

---

## Logging

- Logging is configured with the standard Python `logging` module.
- The logger outputs info, warnings, and errors for operational transparency.
- Customize log level when initializing:

```python
tts = TTSHandler(log_level=logging.DEBUG)
```

---

## Notes

- `ffplay` provides the best performance for in-memory audio playback but requires FFmpeg installation.
- On macOS, `afplay` is used as a secondary in-memory playback option.
- On other systems without `ffplay`, the module falls back to file-based playback.

---

## License

This module is open source and free to use under the MIT License.

---

## Author

Created by Alejandro Rubio @ [ZiaTechnica](www.ziatechnica.org)

---

## Contact

For questions or feedback, please contact: [alejoserubio@gmail.com]

