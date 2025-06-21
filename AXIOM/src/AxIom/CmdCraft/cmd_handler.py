"""
Module: LLM
Provides Prompt and Command Handling
"""
import regex as re
from typing import List, Dict, Any

"""Module: CommandHandler
Provides slash-command parsing and dispatch functionality, including fetch commands of the form
`/<cmd> <cmd body>` and fallback to LLM prompts.
"""
class CommandHandler:
    """
    Manage and interpret slash-style commands(/<cmd>) using Regex
    There are some patterns/structures we are following such as /get <function> for <target>
    Or /create <type> <params>
    Here is where the type of command is also assigned
    """
    SUPPORTED_FUNCTIONS = {"weather", "news", "stock"}
    SUPPORTED_TYPES = {"staff", "resident", "visitor"}
    MASTER_SPLITTER = re.compile(r'^\/(?P<cmd>\w+)\s+(?P<rest>.+)$')
    GET_CMD_PATTERN = re.compile(r'^(?P<function>\w+)\s+for\s+(?P<target>.+)$', re.IGNORECASE)
    CREATE_CMD_PATTERN = re.compile(r'(?P<type>\w+)\s+(?P<payload>.+)', re.IGNORECASE)
    SCHEDULE_CMD_PATTERN = re.compile(r'(?P<user>\w+)\s+for\s(?P<event>\w+)\s+at\s+(?P<time>\w+)', re.IGNORECASE)
    NOTIFY_PAYLOAD = re.compile(r'(?P<recipient>\w+)\s+(?P<message>.+)', re.IGNORECASE)
    PAYLOAD_PATTERN = re.compile(r'(?P<key>\w+)\s+(?P<value>[^ \t]+)', re.IGNORECASE)

    def __init__(self) -> None:
        """
        Initialize parser state and compile necessary regex patterns.
        """
        # raw input and parsed components
        self.raw: str | None = None
        self.cmd: str | None = None
        self.rest: str | None = None

        # parsed command parts
        self.function_call: str | None = None
        self.target: Dict | None = None
        self.function_flag: int = 0  # 1 if a valid fetch command was parsed and a function needs to be called

        # return value
        self.function_calls = []
        self.return_val: dict | None = None

    def set_command(self, raw_command: str) -> None:
        """
        Store the raw input, reset the state, and split into command and rest if prefixed with '/'.
        :param raw_command: The complete user input string.
        """
        # reset previous parse state
        self.raw = raw_command
        self.cmd = None
        self.rest = raw_command
        self.target = None
        self.function_flag = 0

        # try to extract slash-command and the remainder
        match = self.MASTER_SPLITTER.match(raw_command)
        if match:
            # normalize command to lowercase
            self.cmd = match.group("cmd").lower()
            # store everything after the command keyword
            self.rest = match.group("rest")

    def parse_command(self) -> None:
        """
        Here we will determine the type of command
        and prepare the function call with all its parameters.

        :raises ValueError: On missing or invalid command syntax, or unsupported function.
        """
        # check if the rest of the command is given
        if not self.rest:
            raise ValueError(
                "Usage: `/<cmd> <rest of command>` : Missing the body of command"
            )
        # handle fetch commands when cmd is 'get'
        if self.cmd == "get":
            # match '<function> for <target>' pattern
            match = self.GET_CMD_PATTERN.match(self.rest)
            if not match:
                raise ValueError(
                    "Usage: `/get <function> for <target>`"
                )

            # extract and normalize function name
            func = match.group("function").lower()
            targ = match.group("target").strip()

            # validate supported functions
            if func not in self.SUPPORTED_FUNCTIONS:
                raise ValueError(
                    f"I don’t know how to get '{func}'. Supported: {', '.join(self.SUPPORTED_FUNCTIONS)}"
                )

            # store parsed fetch details and mark flag
            self.function_call = func
            self.target = {"params": targ}
            self.function_calls = [{"function_name": self.function_call, "function_params": self.target}]
            self.function_flag = 1

        elif self.cmd == "create":
            # match the “create” header and split off type vs. payload string
            match = self.CREATE_CMD_PATTERN.match(self.rest)
            if not match:
                raise ValueError("Usage: `/create <type> key1 val1 key2 val2 …`")

            # store the function/type
            func = match.group("type").lower()
            targ = match.group("payload")

            # extract all key/value pairs from the payload
            params = {}
            for m in self.PAYLOAD_PATTERN.finditer(targ):
                key = m.group("key").lower().strip()
                value = m.group("value").strip()
                params[key] = value
            params['type'] = func

            if func not in self.SUPPORTED_TYPES:
                raise ValueError(f"There is no type {func}, please choose from {self.SUPPORTED_TYPES}")

            # if we found nothing, complain
            if not params:
                raise ValueError(
                    "No valid key/value pairs found. Usage: `/create <type> key1 val1 key2 val2 …`"
                )

            # store the params and flip the flag
            self.function_call = f"create {func}"
            self.target = params
            self.function_calls = [{"function_name": self.function_call, "function_params": params}]
            self.function_flag = 1


        elif self.cmd == "schedule":

            match = self.SCHEDULE_CMD_PATTERN.match(self.rest)

            if not match:
                raise ValueError("Usage: `/schedule <user> for <event> at <time>`")

            params = {

                "user": match.group("user").strip(),

                "event": match.group("event").strip(),

                "time": match.group("time").strip()

            }

            self.function_call = "schedule"

            self.target = params

            self.function_calls = [{"function_name": self.function_call, "function_params": params}]  # ✅ Fixed here

            self.function_flag = 1

        elif self.cmd == "notify":
            # match the rest of the command to the notify_payload (<recipient> <message>)
            match = self.NOTIFY_PAYLOAD.match(self.rest)
            if not match:
                raise ValueError("Usage: `/notify <recipient> <message>`")
            # set up params
            params = {"recipient": match.group("recipient").strip(), "message": match.group("message").strip()}

            self.function_call = "notify"
            self.target = params
            self.function_flag = 1

        else:
            pass

    def get_commands(self) -> List[Dict[str, Any]]:
        """
        Return the parsed command as a list of dictionaries.

        :return: List of dictionaries, each containing 'cmd' and 'rest' keys.
        """
        return self.function_calls


    def dispatch(self) -> None:
        """
        Route the parsed command to the appropriate handler:
        - If function_flag is set, dispatch to a fetch handler for the function_call and target.
        - Otherwise, pass through the rest string to the LLM or other default processor.
        """
        for function_call in self.function_calls:
            print(f"Function Call: \nCalled Function: {function_call['function_name']} \nFunction Parameters: {function_call['function_params']}")


