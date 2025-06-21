# prompt_handler.py
import os
import requests
from typing import List, Dict, Any
"""
Module: LLM
Provides HTTP-based communication with a language model API.
"""
class PromptHandler:
    def __init__(self, url: str,model: str = "llama3") -> None:
        """
        Initialize the LLM client

        :param url: Base URL of the LLM HTTP chat endpoint
        :param model: Identifier of the language model to use
        :raises ValueError: If the `url` parameter is empty or None
        """

        # check if URL is not provided
        if not url:
            raise ValueError("LLM_URL nnot set")
        self.url = url or os.getenv("LLM_URL")
        self.model = model
    def send_prompt(self,messages: List[Dict[str, str]],stream: bool = False) -> Dict[str, Any]:
        """
        Send messages to llm and return the response as json

        :param messages: list of dictionaries, each containing 'role' and 'content' keys
        :param stream: whether to request streaming token responses (default: False)
        :return: dictionary representing the JSON-decoded response from the API
        :raises requests.RequestException: if HTTP request fails or returns an error status
        """
        # construct json payload for the POST request
        prompt = f"You are an AI assistant named AURA, You will need to you keep your responses short(1-3 sentences max). Here is the prompt: {messages}"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }

        # make the HTTP POST request to llm service
        resp = requests.post(self.url, json=payload, timeout=10)

        # raise exception for HTTP error codes
        resp.raise_for_status()

        # return response json body
        return resp.json()
