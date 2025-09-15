# cmdcraft/function_registry.py
class FunctionRegistry:
    """
    Holds registered commands and functions.
    Provides decorator for adding new commands.
    """

    def __init__(self):
        self.commands = {}

    def register(self, name: str, func):
        self.commands[name] = func

    def execute(self, name: str, *args, **kwargs):
        if name not in self.commands:
            raise ValueError(f"Unknown command: {name}")
        return self.commands[name](*args, **kwargs)

    def command(self, name: str):
        """Decorator for registering commands."""
        def wrapper(func):
            self.register(name, func)
            return func
        return wrapper
