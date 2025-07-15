import requests
from typing import Dict, List, Optional, Any
import subprocess
import psutil
import os
import logging
import coloredlogs
from typing import Optional

# --- Constants ---
# Use uppercase for constants as per PEP 8
OLLAMA_PID_FILE = "ollama.pid"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_NUM_CTX = 4096 # Context window for the model

# --- Logger Configuration ---
# Configure logging once at the module level for consistency
# This makes the logging setup less repetitive and easier to manage.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__) # Use __name__ for the logger name


class PromptHandler:
    """
    Module: OllamaClient
    Provides a high-level interface to interact with the Ollama API for
    language model operations. It's designed to be stateless regarding
    individual API calls but manages an internal chat history and
    Ollama service lifecycle.
    """

    def __init__(self,
                 url: str = DEFAULT_OLLAMA_BASE_URL,
                 model: Optional[str] = None,
                 system_prompt: Optional[str] = None,
                 stream: bool = False) -> None:
        """
        Initializes the Ollama client.

        Args:
            url (str): The base URL of the Ollama API.
                            Defaults to "http://localhost:11434".
            model (Optional[str]): The model to use for generating responses
                                   (e.g., "llama2", "mistral"). If None,
                                   it must be provided during method calls.
            system_prompt (Optional[str]): A system-level instruction to
                                           set the context for the model's
                                           behavior. Defaults to None.
            stream (bool): If True, responses are streamed token by token.
                           If False, the complete response is returned at once.
                           Defaults to False.
        """
        # --- API Configuration ---
        if not model:
            logger.warning("No default model provided. You will need to specify a model for each API call.")
        self.base_url: str = url
        self.model: Optional[str] = model
        self.system_prompt: Optional[str] = system_prompt
        self.stream: bool = stream
        self.chat_history: List[Dict[str, str]] = [] # Stores user/assistant messages for conversation context

        # --- Internal State (generally reset per request or managed) ---
        # Removed self.message as it was redundant and created confusion with self.messages
        # self.response is transient, better handled as a return value.
        self.context: Optional[List[int]] = None  # Ollama's context token list (for future use if needed)
        self.template: Optional[str] = None  # Custom prompt template (for future use if needed)

        # --- Manager Setup ---
        # The manager handles starting/stopping the Ollama service
        self.manager = OllamaManager(OLLAMA_PID_FILE)


    def _ensure_ollama_running(self) -> None:
        """
        Checks if the Ollama service is running and starts it if it's not.
        Logs the startup process.
        """
        status = self.manager.check_ollama()
        if status != 0:
            logger.info("=== Ollama Service Not Running: Initiating Startup Process ===")
            self.manager.start_ollama()
            logger.info("=== Ollama Service Started Successfully ===")
        else:
            logger.debug("Ollama service is already running.")

    def _prepare_chat_payload(self, prompt: str) -> Dict[str, Any]:
        """
        Prepares the JSON payload for the /api/chat endpoint.

        Args:
            prompt (str): The user's current input prompt.

        Returns:
            Dict[str, Any]: The complete payload dictionary for the API request.
        """
        messages_for_request = []

        # Add system prompt if defined
        if self.system_prompt:
            messages_for_request.append({"role": "system", "content": self.system_prompt})

        # Add chat history
        messages_for_request.extend(self.chat_history)

        # Add the current user prompt
        messages_for_request.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model, # Model is required for /api/chat
            "stream": self.stream,
            "messages": messages_for_request,
            "options": {
                "num_ctx": DEFAULT_NUM_CTX # Use a constant for magic numbers
            }
        }
        logger.debug(f"Prepared chat payload: {payload['messages']}") # Use debug for verbose data

        # Validate that a model is set
        if not payload["model"]:
            raise ValueError("No model specified for the chat request. "
                             "Please set a default model in the constructor or pass it explicitly.")

        return payload

    def _make_api_request(self, endpoint: str, method: str = "post", json_data: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Generic helper for making API requests to the Ollama server.

        Args:
            endpoint (str): The specific API endpoint (e.g., "/api/chat").
            method (str): The HTTP method ("get" or "post").
            json_data (Optional[Dict[str, Any]]): JSON payload for POST requests.

        Returns:
            requests.Response: The response object from the requests library.

        Raises:
            requests.exceptions.RequestException: If the network request fails.
            ValueError: If an unsupported HTTP method is provided.
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Making {method.upper()} request to {url}")
        try:
            if method.lower() == "post":
                response = requests.post(url, json=json_data)
            elif method.lower() == "get":
                response = requests.get(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}. Only 'get' and 'post' are supported.")

            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            return response
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama server at {self.base_url}. Is it running?")
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Request to {url} timed out.")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"API request to {url} failed: {e}")
            raise

    def chat(self, prompt: str) -> Optional[str]:
        """
        Engages in a chat conversation with the Ollama model.
        The current prompt and previous conversation history are sent to the model.

        Args:
            prompt (str): The user's input prompt for the current turn.

        Returns:
            Optional[str]: The content of the model's response message as a string,
                           or None if an error occurs or the service is shut down.
        """
        if prompt.lower() in "/bye" or prompt.lower() in "bye":
            logger.info("User requested shutdown: Initiating Ollama service stop.")
            self.manager.stop_ollama()
            return "Ollama service stopped. Goodbye!"

        self._ensure_ollama_running()

        try:
            payload = self._prepare_chat_payload(prompt)
            response = self._make_api_request("/api/chat", method="post", json_data=payload)
            response_json = response.json()

            # Extract the actual message content
            message_obj = response_json.get("message")
            if isinstance(message_obj, dict):
                model_response_content = message_obj.get("content")
            else:
                # Fallback for unexpected message format, though less common with /api/chat
                model_response_content = str(message_obj) if message_obj is not None else None

            if model_response_content:
                # Update chat history for the next turn
                self.chat_history.append({"role": "user", "content": prompt})
                self.chat_history.append({"role": "assistant", "content": model_response_content})

            return model_response_content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during chat request: {e}")
            return "I'm sorry, I encountered an error. Please try again later."
        except ValueError as e:
            logger.error(f"Configuration error for chat: {e}")
            return "A configuration error occurred. Please check the model settings."
        except Exception as e:
            logger.error(f"An unexpected error occurred during chat: {e}", exc_info=True)
            return "An unexpected error occurred. Please contact support."

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all models available on the Ollama server.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  represents a model and its details.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        self._ensure_ollama_running()
        try:
            response = self._make_api_request("/api/tags", method="get")
            return response.json().get("models", [])
        except requests.exceptions.RequestException:
            logger.error("Failed to list models.")
            raise

    def pull_model(self, model_name: str) -> Dict[str, Any]:
        """
        Pulls (downloads) a specified model from the Ollama library.
        Note: This is typically a long-running operation.

        Args:
            model_name (str): The exact name of the model to pull (e.g., "llama2:7b").

        Returns:
            Dict[str, Any]: The JSON response from the API, usually indicating status
                            or progress if streaming were enabled.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        self._ensure_ollama_running()
        payload = {"name": model_name}
        try:
            response = self._make_api_request("/api/pull", method="post", json_data=payload)
            return response.json()
        except requests.exceptions.RequestException:
            logger.error(f"Failed to pull model: {model_name}.")
            raise

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Retrieves detailed information about a specific model.

        Args:
            model_name (str): The name of the model to get information about.

        Returns:
            Dict[str, Any]: A dictionary containing detailed information about the model.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        self._ensure_ollama_running()
        payload = {"name": model_name}
        try:
            response = self._make_api_request("/api/show", method="post", json_data=payload)
            return response.json()
        except requests.exceptions.RequestException:
            logger.error(f"Failed to get info for model: {model_name}.")
            raise

    def create_embedding(self,
                         prompt: str,
                         model: Optional[str] = None) -> List[float]: # Embeddings are typically list of floats
        """
        Generates an embedding vector for a given prompt using an Ollama model.

        Args:
            prompt (str): The text prompt for which to create the embedding.
            model (Optional[str]): The model to use for creating the embedding.
                                   If None, the client's default model is used.

        Returns:
            List[float]: A list of floats representing the embedding vector.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
            ValueError: If no model is specified and no default is set.
        """
        self._ensure_ollama_running()
        chosen_model = model or self.model
        if not chosen_model:
            raise ValueError("No model specified for embedding creation. "
                             "Please set a default model in the constructor or pass it explicitly.")

        payload = {
            "model": chosen_model,
            "prompt": prompt
        }

        try:
            response = self._make_api_request("/api/embeddings", method="post", json_data=payload)
            embedding = response.json().get("embedding")
            if embedding is None:
                raise ValueError("Embedding not found in the response.")
            return embedding
        except requests.exceptions.RequestException:

            raise logger.error(f"Failed to create embedding for prompt: '{prompt[:50]}...'")



# --- Module-level Logger Configuration ---
# Configure logging once at the module level for consistency.
# This logger will be inherited by instances of OllamaManager.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# Using __name__ for the logger name is a best practice.
# It allows for more granular control over logging levels if needed later.
module_logger = logging.getLogger(__name__)


class OllamaManager:
    """
    Manages the lifecycle of the Ollama server process.
    This includes starting, stopping, and checking the status of the
    Ollama 'ollama serve' process using a PID file for tracking.
    """

    def __init__(self, pid_file: Optional[str] = None, log_level: int = logging.INFO):
        """
        Initializes the OllamaManager.

        Args:
            pid_file (Optional[str]): The path to the file where the Ollama
                                      process ID (PID) will be stored.
                                      If None, some operations (like checking/stopping)
                                      will be limited or skipped.
            log_level (int): The logging verbosity level (e.g., logging.INFO,
                             logging.DEBUG). Defaults to logging.INFO.
        """
        self.pid_file = pid_file
        # Use a dedicated instance logger, which can be configured independently
        # if needed, but defaults to the module-level configuration.
        self.logger = self._setup_logger(log_level)
        self.logger.debug(f"OllamaManager initialized with PID file: {self.pid_file}")

    @staticmethod
    def _setup_logger(log_level: int) -> logging.Logger:
        """
        Configures and returns a logger instance for OllamaManager.
        This static method ensures that coloredlogs is installed and applied
        to the logger if it hasn't been already.

        Args:
            log_level (int): The desired logging level.

        Returns:
            logging.Logger: The configured logger instance.
        """
        logger = logging.getLogger("OllamaManager") # Use a consistent name for this manager's logs
        logger.setLevel(log_level)

        # Check if handlers are already configured to prevent duplicate logs
        if not logger.handlers:
            # Apply coloredlogs for better console output
            fmt = "%(asctime)s [%(levelname)s] %(message)s"
            coloredlogs.install(level=log_level, logger=logger, fmt=fmt)
            logger.debug("Coloredlogs installed for OllamaManager logger.")
        return logger

    def check_ollama(self) -> int:
        """
        Checks if the Ollama server process is currently running.

        Reads the PID from the configured PID file and verifies if a process
        with that PID exists and is named "ollama".

        Returns:
            int:
                0: Ollama is running.
                -1: PID file path is not set (self.pid_file is None or empty).
                -2: PID file does not exist.
                -3: Process found, but its name is not "ollama" or it's not running.
                -4: Error reading PID file or accessing process (e.g., permission denied).
        """
        if not self.pid_file:
            self.logger.warning("PID file path is not configured. Cannot check Ollama status definitively.")
            return -1
        elif not os.path.exists(self.pid_file):
            self.logger.info(f"PID file '{self.pid_file}' does not exist. Ollama is likely not running.")
            return -2

        try:
            with open(self.pid_file, "r") as f:
                pid_str = f.read().strip()
                if not pid_str:
                    self.logger.warning(f"PID file '{self.pid_file}' is empty. Ollama is likely not running.")
                    return -4 # Treat as an error in PID file content
                pid = int(pid_str)

            # Check if the process exists and is indeed Ollama
            proc = psutil.Process(pid)
            # Check for "ollama" in the process name (case-insensitive)
            # and ensure the process is still running.
            if "ollama" in proc.name().lower() and proc.is_running():
                self.logger.info(f"Ollama is running with PID: {pid}.")
                return 0
            else:
                self.logger.warning(f"Process with PID {pid} found, but it's not the Ollama server "
                                    f"('{proc.name()}' instead of 'ollama') or it's not running.")
                return -3
        except psutil.NoSuchProcess:
            self.logger.info(f"No process found with PID from '{self.pid_file}'. Ollama is not running.")
            # If the PID file exists but the process doesn't, it implies Ollama stopped
            # unexpectedly or the PID file is stale.
            return -3
        except ValueError:
            self.logger.error(f"PID file '{self.pid_file}' contains invalid PID. Please check its content.")
            return -4
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while checking Ollama status: {e}", exc_info=True)
            return -4

    def start_ollama(self) -> int:
        """
        Starts the Ollama server process.

        If Ollama is already running, it will not attempt to start it again.
        The PID of the new process is written to the configured PID file.

        Returns:
            int:
                0: Ollama was successfully started or was already running.
                -1: Failed to start Ollama (e.g., 'ollama' command not found, permissions issue).
                -2: PID file path is not configured, preventing PID tracking.
        """
        if not self.pid_file:
            self.logger.error("PID file path is not configured. Cannot start Ollama and track its PID.")
            return -2

        if self.check_ollama() == 0:
            self.logger.info("Ollama is already running. No new process started.")
            return 0

        self.logger.info("Attempting to start Ollama server...")
        try:
            # Use `subprocess.Popen` to start `ollama serve` in the background.
            # `preexec_fn=os.setsid` (for Unix-like systems) can detach the child
            # process from the parent's session, making it less susceptible
            # to being killed when the parent exits.
            # `creationflags=subprocess.DETACHED_PROCESS` for Windows.
            # For cross-platform, it's often simpler to rely on the PID file.
            proc = subprocess.Popen(["ollama", "serve"],
                                    stdout=subprocess.DEVNULL, # Suppress stdout
                                    stderr=subprocess.DEVNULL) # Suppress stderr

            # Write the PID to the file for later tracking
            with open(self.pid_file, "w") as f:
                f.write(str(proc.pid))
            self.logger.info(f"Ollama server started successfully with PID: {proc.pid}. PID written to '{self.pid_file}'.")
            return 0
        except FileNotFoundError:
            self.logger.error("Failed to start Ollama: 'ollama' command not found. "
                              "Please ensure Ollama is installed and in your system's PATH.")
            return -1
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while trying to start Ollama: {e}", exc_info=True)
            return -1

    def stop_ollama(self) -> int:
        """
        Stops the running Ollama server process.

        Attempts a graceful termination first (SIGTERM),
        and if the process does not exit within a timeout,
        it resorts to a forceful kill (SIGKILL).
        The PID file is removed upon successful termination.

        Returns:
            int:
                0: Ollama was successfully stopped or was not running.
                -1: PID file path is not configured.
                -2: Error during process termination (e.g., permissions).
                -3: Failed to remove the PID file.
        """
        if not self.pid_file:
            self.logger.error("PID file path is not configured. Cannot stop Ollama definitively.")
            return -1

        # Check current status to avoid errors if already stopped
        status = self.check_ollama()
        if status in [-1, -2, -3, -4]: # Ollama is not running or PID file issues
            self.logger.info("Ollama server is not running or PID file is invalid. No stop action needed.")
            # Attempt to clean up stale PID file if it exists but process doesn't
            if os.path.exists(self.pid_file):
                try:
                    os.remove(self.pid_file)
                    self.logger.info(f"Removed stale PID file: '{self.pid_file}'.")
                except Exception as e:
                    self.logger.error(f"Failed to remove stale PID file '{self.pid_file}': {e}")
                    return -3 # Indicate PID file cleanup issue
            return 0 # Indicate success in ensuring it's stopped

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            proc = psutil.Process(pid)

            # Double-check if it's indeed the Ollama process before terminating
            if "ollama" not in proc.name().lower():
                self.logger.warning(f"PID {pid} from PID file '{self.pid_file}' is not an Ollama process ('{proc.name()}'). "
                                    "Skipping termination to prevent unintended process killing.")
                return 0 # Consider it "stopped" from this manager's perspective

            self.logger.info(f"Attempting to gracefully stop Ollama server (PID: {pid})...")
            proc.terminate() # Send SIGTERM

            try:
                # Wait for the process to terminate, with a timeout
                proc.wait(timeout=10)
                self.logger.info("Ollama server stopped gracefully.")
            except psutil.TimeoutExpired:
                self.logger.warning("Ollama server did not terminate gracefully within 10 seconds. Forcibly killing...")
                proc.kill() # Send SIGKILL
                proc.wait() # Wait for the kill to complete
                self.logger.info("Ollama server forcibly killed.")

        except psutil.NoSuchProcess:
            self.logger.info("Ollama process not found (it was likely already stopped).")
            # This can happen if check_ollama returned 0, but the process died
            # between check_ollama and this try block.
        except ValueError:
            self.logger.error(f"PID file '{self.pid_file}' contains invalid PID. Cannot stop process.")
            return -2
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while trying to stop Ollama: {e}", exc_info=True)
            return -2
        finally:
            # Always attempt to remove the PID file if it exists, regardless of termination success
            if os.path.exists(self.pid_file):
                try:
                    os.remove(self.pid_file)
                    self.logger.info(f"Removed PID file: '{self.pid_file}'.")
                except Exception as e:
                    self.logger.error(f"Failed to remove PID file '{self.pid_file}': {e}", exc_info=True)
                    return -3 # Indicate PID file cleanup issue

        return 0


