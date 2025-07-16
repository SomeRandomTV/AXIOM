# MicHandler 🎙️

**MicHandler** is a Python module that simplifies microphone input and speech-to-text transcription using OpenAI's [whisper](https://github.com/openai/whisper) model. It handles ambient noise calibration, microphone input, and audio transcription—all with easy-to-use logging and minimal setup.

---

## 🚀 Features

- 🎤 Captures live microphone input using `speech_recognition`
- 🧠 Transcribes audio using OpenAI's `whisper` (base model)
- 🔉 Automatically adjusts for ambient noise
- 📁 Saves temporary audio for transcription (can be changed to in-memory)
- 🪵 Configurable logging for debugging and monitoring

---

## 🛠️ Installation

Ensure Python 3.8+ is installed.

Install required dependencies:

```bash
pip install openai-whisper speechrecognition certifi
```

Optional (for better microphone performance):

```bash
pip install pyaudio
```

---

## 🧠 Usage

```python
from mic_handler import MicHandler

mic = MicHandler()

# Start listening and transcribing
mic.set_mic_input()

# Retrieve the result
print("Transcribed text:", mic.get_text())
```

---

## 📂 File Structure

- `MicHandler`:
  - `set_mic_input()`: Records audio from the microphone and transcribes it using Whisper.
  - `get_text()`: Returns the most recently transcribed string.

---

## ⚙️ Environment Configuration

Make sure to include SSL certificates for Whisper to function correctly:

```python
import certifi, os
os.environ['SSL_CERT_FILE'] = certifi.where()
```

---

## ⚠️ Notes

- The current implementation writes recorded audio to disk (`speech_reference.wav`). A future improvement is planned to use in-memory audio buffers to avoid I/O overhead.
- Whisper model used: `base`. You can change this to `"small"`, `"medium"`, or `"large"` depending on your system capability and accuracy needs.

---

## 🪪 License

MIT License. See LICENSE file.

---

## 🧠 Author

Built with ❤️ using Python, OpenAI Whisper, and `speech_recognition`.