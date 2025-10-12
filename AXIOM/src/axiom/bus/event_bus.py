from typing import Callable, Dict, List, Any
from queue import Queue



class Subscriber:
    pass

class Publisher:
    pass

class EventBus:
    def __init__(self, max_events: int = 1000):
        """
        Initialize the Event Bus

        Args:
            max_events (int, optional): Maximum Events allowed in the Queue. Defaults to 1000.
        """
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self._events = Queue(maxsize=max_events)

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """
        Subscriber/Receive messages by topic

        Args:
            topic (str): Topic to subscribe to 
            handler (Callable[[Any], None]): execution/reaction handler
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: Any) -> None:
        """
        Send/Publish Events to the queue for execution

        Args:
            topic (str): topic to send out
            payload (Any): information associated with that topic 
        """
        self._events.put((topic, payload))
        if topic in self._subscribers:
            for handler in self._subscribers[topic]:
                handler(payload)

    def unsubscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """
        

        Args:
            topic (str): _description_
            handler (Callable[[Any], None]): _description_
        """
        if topic in self._subscribers:
            self._subscribers[topic].remove(handler)
            if not self._subscribers[topic]:
                del self._subscribers[topic]

    def clear(self) -> None:
        while not self._events.empty():
            self._events.get()
            
    def print_events(self):
        event_copy = self._events
        while not self._events.empty():
            print(f"Event: {event_copy.get()}")
            
def main():
    
    bus = EventBus()
    
    bus.publish("conversation.turn", {"user": "balls"})
    bus.subscribe("conversation.turn", isinstance(bus, object))
    
    bus.print_events()
    
if __name__ == "__main__":
    main()
    
    
    
