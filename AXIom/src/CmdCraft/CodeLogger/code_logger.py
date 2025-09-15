# src/cmdcraft/CodeLogger/code_logger.py
import logging
import inspect

class CodeLogger:
    def __init__(self, logger_name: str = "CodeLogger"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        # Formatter that includes module, function, and line number
        formatter = logging.Formatter(
            "[%(levelname)s] %(asctime)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)

        if not self.logger.handlers:  # Avoid duplicate handlers
            self.logger.addHandler(ch)

    def _get_context(self):
        """Helper to fetch caller's context."""
        stack = inspect.stack()
        caller = stack[2]  # 0 = current, 1 = this method, 2 = actual caller
        return f"{caller.function}:{caller.lineno}"

    def info(self, message: str):
        self.logger.info(f"{self._get_context()} - {message}")

    def warning(self, message: str):
        self.logger.warning(f"{self._get_context()} - {message}")

    def error(self, message: str):
        self.logger.error(f"{self._get_context()} - {message}")
