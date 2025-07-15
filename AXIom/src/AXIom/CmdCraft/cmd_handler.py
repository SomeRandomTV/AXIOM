import re
import logging
from typing import List, Dict, Any
import coloredlogs # Import coloredlogs

"""
Module: CommandHandler
Provides slash-command parsing and dispatch functionality, including specific fetch commands
of the form `/get <function> for <target>` and fallback to LLM prompts.
"""

class CommandHandler:
    """
    Manages and interprets slash-style commands (e.g., /<cmd>).
    It uses regex patterns to identify command types and extract parameters,
    preparing them for subsequent function calls.
    """

    # Supported commands and their expected structures
    SUPPORTED_FUNCTIONS = {"weather", "news", "stock"}
    SUPPORTED_TYPES = {"staff", "resident", "visitor"}

    # Regex patterns for parsing commands
    MASTER_SPLITTER = re.compile(r'^/(?P<cmd>\w+)\s+(?P<rest>.+)$')
    GET_CMD_PATTERN = re.compile(r'^(?P<function>\w+)\s+for\s+(?P<target>.+)$', re.IGNORECASE)
    CREATE_CMD_PATTERN = re.compile(r'(?P<type>\w+)\s+(?P<payload>.+)', re.IGNORECASE)
    SCHEDULE_CMD_PATTERN = re.compile(r'(?P<user>\w+)\s+for\s+(?P<event>.+)\s+at\s+(?P<time>.+)', re.IGNORECASE)
    NOTIFY_PAYLOAD = re.compile(r'(?P<recipient>\w+)\s+(?P<message>.+)', re.IGNORECASE)
    PAYLOAD_PATTERN = re.compile(r'(?P<key>\w+)\s+(?P<value>[^ \t]+)', re.IGNORECASE)

    def __init__(self, log_level: int = logging.INFO) -> None:
        """
        Initializes the CommandHandler, setting up parser state and a logger.
        """
        # Raw input and parsed components
        self.raw: str | None = None
        self.cmd: str | None = None
        self.rest: str | None = None

        # Parsed command parts for function calls
        self.function_call_name: str | None = None
        self.function_params: Dict[str, Any] | None = None
        self.function_flag: int | None = None


        # List to store all parsed function calls (for potential multiple calls)
        self.function_calls: List[Dict[str, Any]] = []

        self.logger = self._setup_logger(log_level)

    @staticmethod
    def _setup_logger(level: int) -> logging.Logger:
        """
        Sets up and returns a logger instance with coloredlogs.
        """
        logger = logging.getLogger('CommandHandler')
        coloredlogs.install(level=level, logger=logger,
                            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        return logger

    def set_command(self, raw_command: str) -> None:
        """
        Stores the raw user input, resets the internal state, and attempts to
        split the input into a command and its arguments if it's a slash command.

        Args:
            raw_command (str): The complete user input string.
        """
        # Reset previous parse state
        self.raw = raw_command
        self.cmd = None
        self.rest = raw_command
        self.function_call_name = None
        self.function_params = None
        self.function_calls = [] # Clear previous calls
        self.function_flag = 0

        self.logger.info(f"Attempting to parse raw command: '{raw_command}'")
        match = self.MASTER_SPLITTER.match(raw_command)
        if match:
            # Normalize command to lowercase
            self.cmd = match.group("cmd").lower()
            # Store everything after the command keyword
            self.rest = match.group("rest")
            self.function_flag = 1
            self.logger.info(f"Identified slash command: '/{self.cmd}' with rest: '{self.rest}'")
        else:
            self.logger.info("No slash command detected. Treating as a regular prompt.")

    def parse_command(self) -> None:
        """
        Determines the type of command and extracts all necessary parameters,
        preparing the function call details.

        Raises:
            ValueError: If the command syntax is invalid, a required part is missing,
                        or an unsupported function/type is requested.
        """
        # If it's not a slash command, there's nothing to parse here for function calls.
        if not self.function_flag:
            self.logger.debug("Not a slash command, skipping command parsing for function calls.")
            return

        # Check if the rest of the command is provided for slash commands
        if not self.rest:
            self.logger.error(f"Missing command body for /{self.cmd} command.")
            raise ValueError(f"Usage: `/{self.cmd} <rest of command>` : Missing the body of the command.")

        self.logger.info(f"Parsing command: '{self.cmd}'")

        if self.cmd == "get":
            self._parse_get_command()
        elif self.cmd == "create":
            self._parse_create_command()
        elif self.cmd == "schedule":
            self._parse_schedule_command()
        elif self.cmd == "notify":
            self._parse_notify_command()
        else:
            self.logger.warning(f"Unsupported slash command type: '/{self.cmd}'. This will be treated as a general prompt.")
            # For unsupported slash commands, we might decide to pass them to LLM directly
            # or raise an error depending on desired strictness.
            # For now, we will simply not populate function_calls.

    def _parse_get_command(self) -> None:
        """Helper to parse '/get' commands."""
        self.logger.debug("Processing '/get' command pattern.")
        match = self.GET_CMD_PATTERN.match(self.rest)
        if not match:
            self.logger.error("Invalid '/get' command syntax.")
            raise ValueError("Usage: `/get <function> for <target>` (e.g., `/get weather for Seattle`)")

        func = match.group("function").lower()
        target = match.group("target").strip()
        self.logger.debug(f"Extracted function: '{func}', target: '{target}'")

        if func not in self.SUPPORTED_FUNCTIONS:
            self.logger.error(f"Unsupported function requested: '{func}'.")
            raise ValueError(f"I don't know how to get '{func}'. Supported functions: {', '.join(self.SUPPORTED_FUNCTIONS)}.")

        # Special handling for 'get weather' and 'get news' vs 'get stock' (param name)
        params = {}
        if func == "weather":
            params = {"location": target}
        elif func == "news":
            params = {"topic": target}
        elif func == "stock":
            params = {"stock_name": target} # Assuming 'stock_name' is the expected param for get_stock

        self.function_call_name = f"get_{func}" # e.g., "get_weather"
        self.function_params = params
        self.function_calls.append({"function_name": self.function_call_name, "function_params": self.function_params})
        self.logger.info(f"Prepared function call: {self.function_call_name} with params: {self.function_params}")

    def _parse_create_command(self) -> None:
        """Helper to parse '/create' commands."""
        self.logger.debug("Processing '/create' command pattern.")
        match = self.CREATE_CMD_PATTERN.match(self.rest)
        if not match:
            self.logger.error("Invalid '/create' command syntax.")
            raise ValueError("Usage: `/create <type> key1 val1 key2 val2 ...`")

        obj_type = match.group("type").lower()
        payload_str = match.group("payload")
        self.logger.debug(f"Extracted type: '{obj_type}', payload string: '{payload_str}'")

        if obj_type not in self.SUPPORTED_TYPES:
            self.logger.error(f"Unsupported type for creation: '{obj_type}'.")
            raise ValueError(f"Cannot create type '{obj_type}'. Supported types: {', '.join(self.SUPPORTED_TYPES)}.")

        params = {}
        # Iterate over all key/value pairs found in the payload string
        for m in self.PAYLOAD_PATTERN.finditer(payload_str):
            key = m.group("key").lower().strip()
            value = m.group("value").strip()
            params[key] = value
            self.logger.debug(f"Parsed parameter: {key}='{value}'")

        if not params:
            self.logger.error("No valid parameters found in '/create' command payload.")
            raise ValueError("No valid key/value pairs found. Usage: `/create <type> key1 val1 key2 val2 ...`")

        self.function_call_name = f"create_{obj_type}" # e.g., "create_resident"
        self.function_params = params
        self.function_calls.append({"function_name": self.function_call_name, "function_params": self.function_params})
        self.logger.info(f"Prepared function call: {self.function_call_name} with params: {self.function_params}")

    def _parse_schedule_command(self) -> None:
        """Helper to parse '/schedule' commands."""
        self.logger.debug("Processing '/schedule' command pattern.")
        match = self.SCHEDULE_CMD_PATTERN.match(self.rest)

        if not match:
            self.logger.error("Invalid '/schedule' command syntax.")
            raise ValueError("Usage: `/schedule <user> for <event> at <time>` (e.g., `/schedule John for team meeting at 2025-07-10T10:00:00`)")

        params = {
            "user": match.group("user").strip(),
            "event": match.group("event").strip(),
            "time": match.group("time").strip()
        }
        self.logger.debug(f"Extracted schedule parameters: {params}")

        self.function_call_name = "schedule"
        self.function_params = params
        self.function_calls.append({"function_name": self.function_call_name, "function_params": self.function_params})
        self.logger.info(f"Prepared function call: {self.function_call_name} with params: {self.function_params}")

    def _parse_notify_command(self) -> None:
        """Helper to parse '/notify' commands."""
        self.logger.debug("Processing '/notify' command pattern.")
        match = self.NOTIFY_PAYLOAD.match(self.rest)
        if not match:
            self.logger.error("Invalid '/notify' command syntax.")
            raise ValueError("Usage: `/notify <recipient> <message>` (e.g., `/notify John Hello there!`)")

        params = {
            "recipient": match.group("recipient").strip(),
            "message": match.group("message").strip()
        }
        self.logger.debug(f"Extracted notify parameters: {params}")

        self.function_call_name = "notify"
        self.function_params = params
        self.function_calls.append({"function_name": self.function_call_name, "function_params": self.function_params})
        self.logger.info(f"Prepared function call: {self.function_call_name} with params: {self.function_params}")

    def get_function_calls(self) -> List[Dict[str, Any]]:
        """
        Returns the list of parsed function calls. Each call is a dictionary
        containing 'function_name' and 'function_params'.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                   represents a function call to be made.
        """
        return self.function_calls

    def dispatch(self) -> None:
        """
        This method is a placeholder for actual command dispatching.
        In a real application, this would call the `FunctionHandler`
        or a similar component to execute the parsed commands.
        For now, it simply prints the parsed function calls.
        """
        if not self.function_calls:
            self.logger.info("No specific function commands parsed to dispatch.")
            return

        self.logger.info("Dispatching parsed function calls:")
        for function_call in self.function_calls:
            self.logger.info(f"  Called Function: {function_call.get('function_name', 'N/A')}")
            self.logger.info(f"  Function Parameters: {function_call.get('function_params', {})}")
            print("-" * 30)


def main():
    """
    Main function to demonstrate CommandHandler usage.
    """
    cmd_handler = CommandHandler(log_level=logging.DEBUG) # Set to DEBUG to see all log messages

    # Test cases
    print("\n--- Test Case 1: Get Weather ---")
    cmd_handler.set_command("/get weather for Seattle")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Error: {e}")

    print("\n--- Test Case 2: Get News ---")
    cmd_handler.set_command("/get news for AI")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Error: {e}")

    print("\n--- Test Case 3: Create Resident ---")
    cmd_handler.set_command("/create resident name JohnDoe weight 180 height 70")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Error: {e}")

    print("\n--- Test Case 4: Schedule Event ---")
    cmd_handler.set_command("/schedule Alice for team meeting at 2025-07-10T10:00:00")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Error: {e}")

    print("\n--- Test Case 5: Notify User ---")
    cmd_handler.set_command("/notify Bob Your package has arrived.")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Error: {e}")

    print("\n--- Test Case 6: Invalid Get Command ---")
    cmd_handler.set_command("/get weather Seattle") # Missing "for"
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Caught expected error: {e}")

    print("\n--- Test Case 7: Unsupported Function ---")
    cmd_handler.set_command("/get forecast for London")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Caught expected error: {e}")

    print("\n--- Test Case 8: Non-slash Command ---")
    cmd_handler.set_command("Tell me a joke.")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch() # This should print "No specific function commands parsed..."
    except ValueError as e:
        cmd_handler.logger.error(f"Caught unexpected error: {e}")

    print("\n--- Test Case 9: Create Staff with Temperature ---")
    cmd_handler.set_command("/create staff name JaneDoe weight 150 height 65 temp 98.6")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Error: {e}")

    print("\n--- Test Case 10: Create Visitor ---")
    cmd_handler.set_command("/create visitor name GuestUser purpose tour")
    try:
        cmd_handler.parse_command()
        cmd_handler.dispatch()
    except ValueError as e:
        cmd_handler.logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()