import sys, os, sqlite3
from datetime import datetime
from axiom.bus.event_bus import EventBus


class Core:
    def __init__(self):
        self.bus = EventBus()

    def start(self):
        print("Starting AXIOM Core...")
        x = 1
        y = 2
        return x + y
