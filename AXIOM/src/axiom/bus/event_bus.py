# src/axiom/bus/event_bus.py

from typing import Callable, Any
from collections import deque
from events import Event



class EventBus:

    def __init__(self):
        self.event: Event = Event()
        self._subscribers: dict[str, list[Callable]] = {}
        self._event_queue: deque[tuple[str, Any]] = deque()


    def subscribe(self, event_name: str, callback: Callable):
        # register handler for events
        pass

    def unsubscribe(self, event_name: str, callback: Callable):
        # remove handler

        pass

    def publish(self, event_name: str, payload: Any):
        # add event to the event queue
        self._event_queue.append((event_name, payload))

    def run(self):
        # execute the tasks in queue
        pass
