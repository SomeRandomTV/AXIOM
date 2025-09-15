# cmdcraft/command_processor.py
class CommandProcessor:
    """
    Parses text input and dispatches to the correct function or LLM.
    """

    def __init__(self, function_registry, ollama_manager):
        self.function_registry = function_registry
        self.ollama_manager = ollama_manager

    def process(self, text: str) -> str:
        """
        Process a text command:
        1. Check if it matches a registered command
        2. If not, forward to Ollama
        Returns a response string.
        """
        # TODO: NLP parsing (spaCy)
        if text in self.function_registry.commands:
            return self.function_registry.execute(text)
        return self.ollama_manager.chat(text)
