"""Read-Eval-Print Loop for AXIOM Console."""


import sys
import logging
from typing import List
from ..va.pipeline import Pipeline
from ..bus.event_bus import EventBus
from ..config import AxiomConfig, ROOT_DIR
import asyncio

logger = logging.getLogger(__name__)

class REPL:
    """
    Interactive console for AXIOM Virtual Assistant.
    Supports conversation and command mode.
    """
    def __init__(self):
        # Load config (default to configs/default.json)
        config_path = ROOT_DIR / "configs" / "default.json"
        config = AxiomConfig.from_json_file(config_path)
        va_cfg = config.virtual_assistant
        # Get intent_config_path (resolve relative to ROOT_DIR)
        intent_config_path = va_cfg.__dict__.get("intent_config_path")
        if intent_config_path and not str(intent_config_path).startswith("/"):
            intent_config_path = str(ROOT_DIR / intent_config_path)
        self._event_bus = EventBus()
        self._pipeline = Pipeline(self._event_bus, intent_config_path=intent_config_path)
        self._history = []  # (user_input, response)
        self._running = True
        self._commands = {
            "help": self._cmd_help,
            "quit": self._cmd_quit,
            "exit": self._cmd_quit,
            "history": self._cmd_history,
            "status": self._cmd_status,
            "clear": self._cmd_clear,
            "config": self._cmd_config
        }
        # Tab completion setup
        try:
            import readline
            readline.set_completer(self._tab_complete)
            readline.parse_and_bind('tab: complete')
        except ImportError:
            pass
        self._buffer = []  # For multi-line input
    
    async def run(self):
        print("AXIOM Virtual Assistant Console (type 'help' for commands)")
        print("Multi-line input: End with a blank line. Tab completion enabled for commands.")
        while self._running:
            try:
                user_input = input(">>> ")
                if user_input.strip() == "":
                    if self._buffer:
                        full_input = "\n".join(self._buffer)
                        self._buffer.clear()
                        if full_input.split()[0] in self._commands:
                            self._commands[full_input.split()[0]]()
                        else:
                            await self._handle_conversation(full_input)
                    continue
                if user_input.endswith("\\"):
                    self._buffer.append(user_input[:-1])
                    continue
                if self._buffer:
                    self._buffer.append(user_input)
                    continue
                cmd = user_input.strip().split()[0] if user_input.strip() else ""
                if cmd in self._commands:
                    try:
                        self._commands[cmd]()
                    except Exception as e:
                        print(f"Error executing command '{cmd}': {e}")
                else:
                    try:
                        await self._handle_conversation(user_input)
                    except Exception as e:
                        print(f"Error: {e}")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                self._running = False
    def _tab_complete(self, text, state):
        options = [cmd for cmd in self._commands if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        return None
    def _cmd_config(self):
        print("Current pipeline config:")
        print(self._pipeline.config)
        print("To update config, type: config key=value")
        # Example: config max_length=100
        update = input("Config update (or blank to skip): ").strip()
        if update:
            try:
                key, value = update.split("=", 1)
                self._pipeline.config[key.strip()] = value.strip()
                print(f"Config updated: {key.strip()} = {value.strip()}")
            except Exception as e:
                print(f"Error updating config: {e}")
    
    async def _handle_conversation(self, user_input: str):
        response = await self._pipeline.process_text_input(user_input)
        self._history.append((user_input, response))
        print(response)
    
    def _cmd_help(self):
        print("Available commands:")
        for cmd in self._commands:
            print(f"  {cmd}")
        print("Type any other text to chat with the assistant.")
    
    def _cmd_quit(self):
        print("Goodbye!")
        self._running = False
    
    def _cmd_history(self):
        print("Conversation history:")
        for idx, (user, resp) in enumerate(self._history, 1):
            print(f"{idx}: User: {user}")
            print(f"   AXIOM: {resp}")
    
    def _cmd_status(self):
        print("System status: Running")
    
    def _cmd_clear(self):
        self._history.clear()
        print("Conversation history cleared.")
