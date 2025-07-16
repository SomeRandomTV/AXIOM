# 🦙 OllamaClient

A Python client to interface with a local LLM server.  
This module allows interaction with chat models, management of the Ollama server process, model pulling, metadata fetching, and embedding generation for ARA

This Module is part of the `CmdCraft library` for handling user input and commands.
---

## 📦 Features

- ✅ Automatic Ollama process management (start/stop)
- 🧠 Chat with persistent history
- 📥 Pull and list local models
- 🔍 Retrieve model metadata
- 🧬 Generate vector embeddings
- 🛠 Colored logging for diagnostics

---


```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install requests psutil coloredlogs
```

Ensure `ollama` is installed and in your system's PATH:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

### 2. Example Usage

```python
from ollama_client import PromptHandler

client = PromptHandler(model="mistral", system_prompt="You are a helpful assistant.")

# Chat with the model
response = client.chat("Who discovered gravity?")
print(response)

# Follow-up in same context
follow_up = client.chat("When did he live?")
print(follow_up)

# List available models
models = client.list_models()
print(models)

# Pull a model if not present
client.pull_model("llama2:7b")

# Create an embedding
embedding = client.create_embedding("Hello world")
print(embedding)

# Graceful shutdown
client.chat("/bye")
```

---

## ⚙️ API Overview

| Method                        | Description                                      |
|------------------------------|--------------------------------------------------|
| `chat(prompt: str)`          | Interacts with model, tracks conversation        |
| `list_models()`              | Lists all installed models                       |
| `pull_model(model_name)`     | Downloads a model from Ollama                    |
| `get_model_info(model_name)` | Retrieves metadata about a specific model        |
| `create_embedding(prompt)`   | Generates vector embedding for a given prompt    |
| `stop_ollama()`              | Gracefully terminates the Ollama server process  |

---

## 🧠 Stateful Chat

The client tracks the full chat history and allows setting a system prompt:

```python
PromptHandler(model="mistral", system_prompt="You are a code assistant.")
```

The conversation history is retained between messages unless reset manually.

---

## 🛑 Shutdown Options

To gracefully stop the server:

```python
client.chat("/bye")
```

Or directly:

```python
client.manager.stop_ollama()
```

---

## 🔧 Logging

Colorized logs are enabled by default using `coloredlogs`.  
You can adjust verbosity with:

```python
import logging
logging.getLogger("OllamaManager").setLevel(logging.DEBUG)
```

---

## ⚠️ Notes

- The client assumes `ollama serve` is the command to run the server.
- A PID file (`ollama.pid`) is created and used to track and terminate the process.
- Only one Ollama server is managed at a time.

---

## 📄 License

MIT License © 2025 ZiaTechnica