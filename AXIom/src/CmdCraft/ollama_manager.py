# src/cmdcraft/ollama_manager.py
import os
import requests
from dotenv import load_dotenv
import subprocess
import time
from .CodeLogger.code_logger import CodeLogger

load_dotenv()
# OLLAMA URL
LLM_URL = os.getenv("LLM_URL")


class OllamaManager:
    """
    Manages Ollama server lifecycle and chat interactions.
    """

    def __init__(self, model: str = "llama3:latest", system_prompt: str = None):
        """
        Initialize OllamaManager

        Args:
            model -> name of model to use
        """
        self.server_process = None
        self.model = model
        self.system_prompt = system_prompt
        self.conversation = {}
        self.prompt = ""
        self.response = ""
        self.logger = CodeLogger()

    def start_server(self) -> int:
        """
        Start the ollama server

        Returns:
            0 -> success
            1 -> already running
            2 -> failed to start server
        """
        self.logger.info("Starting Ollama server...")
        print(f"DEBUG: LLM_URL = {LLM_URL}")  # Debug line
        try:
            # check if already running
            if self.check_server() == 0:
                self.logger.info("Server already running - using existing instance.")
                return 0  # Changed from 1 to 0 since this is actually success

            # start process
            self.server_process = subprocess.Popen(["ollama", "serve"])
            time.sleep(2)  # give server time to initialize

            if self.check_server() == 0:
                self.logger.info("Server started successfully.")
                return 0
            else:
                self.logger.error("Failed to start server.")
                return 2
        except Exception as e:
            self.logger.error(f"Exception starting server: {e}")
            return 2

    def stop_server(self) -> int:
        """Stop the ollama server"""
        self.logger.info("Stopping Ollama server...")
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.server_process = None
            else:
                self.logger.info("Server was not started by this manager.")
                # Actually stop the external Ollama server
                try:
                    subprocess.run(["pkill", "ollama"], check=True)
                    self.logger.info("External Ollama server stopped.")
                except subprocess.CalledProcessError:
                    self.logger.warning("No external Ollama processes found or failed to kill.")

            return 0
        except Exception as e:
            self.logger.error(f"Exception stopping server: {e}")
            return 2

    def restart_server(self) -> int:
        """
        Restart the ollama server

        Returns:
            0 -> success
            1 -> failed to restart server
        """
        self.logger.info("Restarting Ollama server...")
        stopped = self.stop_server()
        started = self.start_server()
        if stopped == 0 and started == 0:
            return 0
        return 1

    def check_server(self) -> int:
        """
        Check ollama server status

        Returns:
            0 -> server running
            1 -> server not running
            2 -> server check failed
        """
        try:
            resp = requests.get(f"{LLM_URL}/api/tags", timeout=2)
            if resp.status_code == 200:
                return 0
            return 1
        except requests.exceptions.RequestException:
            return 1
        except Exception as e:
            self.logger.error(f"Check server failed: {e}")
            return 2

    def list_models(self):
        """
        Show available models

        Returns:
            models -> list of model names if available, empty list otherwise
        """
        models = {"Current model": self.model}

        try:
            resp = requests.get(f"{LLM_URL}/api/tags")
            resp.raise_for_status()

            # extract models from response JSON
            available_models = resp.json().get("models", [])
            # add them to the dictionary
            models["Available models"] = available_models

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch models: {e}")

        return models

    def pull_model(self, model_name):
        """
        Get model details

        Args:
            model_name -> name of model to pull details for

        Returns:
            Response -> json of model details if successful, None otherwise
        """
        try:
            resp = requests.post(f"{LLM_URL}/api/pull", json={"name": model_name})
            self.logger.info(f"Pull response: {resp.json()}")
            return resp.json()
        except Exception as e:
            self.logger.error(f"Error pulling model: {e}")
            return None

    def show_model(self, model_name):
        """
        Show model details

        Args:
            model_name -> name of model to show details for

        Returns:
            details -> json of model details if successful, None otherwise
        """
        try:
            resp = requests.post(f"{LLM_URL}/api/show", json={"name": model_name})
            details = resp.json()
            self.logger.info(f"Model {model_name}: {details}")
            return details
        except Exception as e:
            self.logger.error(f"Error showing model {model_name}: {e}")
            return None

    def chat(self, prompt, model_name=None, **kwargs):
        """
        Send prompts to ollama server

        Args:
            prompt -> prompt to send to model
            model_name -> name of model to use (optional, uses self.model if not provided)
            **kwargs -> additional arguments to pass to model, e.g., temperature, max_tokens, etc.

        Returns:
            reply -> json of response if successful, None otherwise
        """
        try:
            payload = {
                "model": model_name or self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,  # Request non-streaming response
                "options": kwargs or {}
            }
            resp = requests.post(f"{LLM_URL}/api/chat", json=payload)
            resp.raise_for_status()  # Raise an exception for bad status codes
            reply = resp.json()
            self.logger.info(f"Response: {reply}")
            return reply
        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            return None

    def embed(self, model_name, text):
        """
        Embed text to vector space

        Returns:
            emb -> json of embedding if successful, None otherwise
        """
        try:
            payload = {
                "model": model_name,
                "input": text
            }
            resp = requests.post(f"{LLM_URL}/api/embed", json=payload)
            emb = resp.json()
            self.logger.info(f"Embedding: {emb}")
            return emb
        except Exception as e:
            self.logger.error(f"Error embedding text: {e}")
            return None