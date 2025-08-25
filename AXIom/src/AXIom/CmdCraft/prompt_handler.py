
from typing import Dict, List, Any
import logging
import coloredlogs
from typing import Optional
import requests

# --- Constants ---
# Use uppercase for constants as per PEP 8
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_NUM_CTX = 4096              # Context window for the model
DEFAULT_MODEL = "llama3:latest"     # Use the actual model name you have installed

"""
Module: OllamaClient
Provides a high-level interface to interact with the Ollama API forZ
language model operations. It's designed to be stateless regarding
individual API calls but manages an internal chat history and
Ollama service lifecycle.
    
# TODO: work on starting/stopping the Ollama service
"""
class PromptHandler:
    def __init__(self,
                 url: str = DEFAULT_OLLAMA_BASE_URL,
                 model: Optional[str] = DEFAULT_MODEL,
                 system_prompt: Optional[str] = None,
                 stream: bool = False,
                 log_level: int = logging.INFO
                 ) -> None:
        """
        Initializes the Ollama client.

        Args:
            url (str): The base URL of the Ollama API.
                            Defaults to "http://localhost:11434".
            model (Optional[str]): The model to use for generating responses
                                (e.g., "llama3:latest", "phi3:latest"). If None,
                                uses DEFAULT_MODEL.
            system_prompt (Optional[str]): A system-level instruction to
                                        set the context for the model's
                                        behavior. Defaults to None.
            stream (bool): If True, responses are streamed token by token.
                        If False, the complete response is returned at once.
                        Defaults to False.

        """
        
        # --- Logger Setup ---
        self.logger = self._setup_logger(log_level)
        # --- API Configuration ---
        if not model:
            self.logger.warning(f"No model provided, using default: {DEFAULT_MODEL}")
            model = DEFAULT_MODEL
        self.base_url: str = url
        self.model: str = model  # Now guaranteed to have a value
        self.system_prompt: Optional[str] = system_prompt
        self.stream: bool = stream
        self.chat_history: List[Dict[str, str]] = [] # Stores user/assistant messages for conversation context

        # --- Internal State (generally reset per request or managed) ---
        # Removed self.message as it was redundant and created confusion with self.messages
        # self.response is transient, better handled as a return value.
        self.context: Optional[List[int]] = None  # Ollama's context token list (for future use if needed)
        self.template: Optional[str] = None  # Custom prompt template (for future use if needed)

        
        # Validate model availability
        self._validate_model()

    def _validate_model(self):
        """Validate that the specified model is available on the Ollama server."""
        try:
            self.logger.info(f"Validating model: {self.model}")
            available_models = self.list_models()
            model_names = [m.get('name', '') for m in available_models]
            
            if self.model not in model_names:
                self.logger.warning(f"Model '{self.model}' not found in available models: {model_names}")
                # Try to find a similar model
                for available_model in model_names:
                    if self.model.split(':')[0] in available_model:
                        self.logger.info(f"Found similar model: {available_model}, using it instead")
                        self.model = available_model
                        break
                else:
                    self.logger.error(f"No suitable model found. Available: {model_names}")
                    raise ValueError(f"Model '{self.model}' not available. Please install it with: ollama pull {self.model}")
            else:
                self.logger.info(f"Model '{self.model}' validated successfully")
                
        except Exception as e:
            self.logger.error(f"Model validation failed: {e}")
            # Don't raise here, let it fail gracefully during first use

    @staticmethod
    def _setup_logger(level: int) -> logging.Logger:
        """
        Sets up and returns a logger for the Ollama client.

        Args:
            level (int): Logging level (e.g., logging.INFO, logging.DEBUG).

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger("OllamaClient")
        coloredlogs.install(level=level, logger=logger,
                            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        return logger   


    def _ensure_ollama_running(self) -> None:
        """
        Checks if the Ollama service is running. 
        Note: Service management is now handled at the main application level.
        """
        # First check if there's an existing Ollama service running
        try:

            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.debug("Ollama service is responding to API calls.")
                return
        except requests.exceptions.ConnectionError:
            pass


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
        self.logger.debug(f"Prepared chat payload: {payload['messages']}") # Use debug for verbose data

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
        self.logger.info(f"Making {method.upper()} request to {url}")
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
            self.logger.error(f"Failed to connect to Ollama server at {self.base_url}. Is it running?")
            raise
        except requests.exceptions.Timeout:
            self.logger.error(f"Request to {url} timed out.")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request to {url} failed: {e}")
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
            self.logger.info("User requested shutdown: Ollama service will be stopped by main application.")
            return "Goodbye! Shutting down AXIom and Ollama service."

        # Check if Ollama is running (but don't start it)
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
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to Ollama API. Service may be down.")
            return "I'm sorry, I cannot connect to the AI service. Please check if Ollama is running."
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error during chat request: {e}")
            return "I'm sorry, I encountered an error. Please try again later."
        except ValueError as e:
            self.logger.error(f"Configuration error for chat: {e}")
            return "A configuration error occurred. Please check the model settings."
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during chat: {e}", exc_info=True)
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
        # Check if Ollama is running (but don't start it)
        self._ensure_ollama_running()
        try:
            response = self._make_api_request("/api/tags", method="get")
            return response.json().get("models", [])
        except requests.exceptions.RequestException:
            self.logger.error("Failed to list models.")
            raise

    def pull_model(self, model_name: str) -> Dict[str, Any]:
        """
        Pulls (downloads) a specified model from the Ollama library.
        Note: This is typically a long-running operation.

        Args:
            model_name (str): The exact name of the model to pull (e.g., "llama3:latest").

        Returns:
            Dict[str, Any]: The JSON response from the API, usually indicating status
                            or progress if streaming were enabled.

        Raises:
            requests.exceptions.RequestException: If the API request fails.
        """
        # Check if Ollama is running (but don't start it)
        self._ensure_ollama_running()
        payload = {"name": model_name}
        try:
            response = self._make_api_request("/api/pull", method="post", json_data=payload)
            return response.json()
        except requests.exceptions.RequestException:
            self.logger.error(f"Failed to pull model: {model_name}.")
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
        # Check if Ollama is running (but don't start it)
        self._ensure_ollama_running()
        payload = {"name": model_name}
        try:
            response = self._make_api_request("/api/show", method="post", json_data=payload)
            return response.json()
        except requests.exceptions.RequestException:
            self.logger.error(f"Failed to get info for model: {model_name}.")
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
        # Check if Ollama is running (but don't start it)
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
            self.logger.error(f"Failed to create embedding for prompt: '{prompt[:50]}...'")
            raise



