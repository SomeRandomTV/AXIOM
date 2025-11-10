from typing import Dict, List, Callable, Set, Optional
from queue import Queue
import asyncio
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta

from .events import Event, EventType
from .exceptions import (
    EventBusException, InvalidEventTypeError,
    UnregisteredPublisherError, EventDeliveryError
)
from axiom.utils.logging import get_logger, log_event_bus_activity, PerformanceLogger, log_error
from axiom.utils.errors import ErrorCode, EventBusError

logger = get_logger(__name__)

@dataclass
class DeliveryRecord:
    """Record of event delivery attempt."""
    event: Event
    subscriber: Callable
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    error: Optional[Exception] = None
    
    def should_retry(self, max_attempts: int, retry_delay: timedelta) -> bool:
        """Check if event should be retried based on attempt count and delay."""
        if self.attempts >= max_attempts:
            return False
        if self.last_attempt is None:
            return True
        return datetime.now() - self.last_attempt >= retry_delay

class EventBus:
    """
    Central event bus implementation that handles publisher-subscriber pattern.
    Provides asynchronous, decoupled communication between system components.
    """
    
    def __init__(self, max_events: int = 1000, 
                 max_retry_attempts: int = 3,
                 retry_delay: timedelta = timedelta(seconds=1),
                 num_workers: int = 4):
        """
        Initialize the Event Bus with publisher-subscriber infrastructure.
        
        Args:
            max_events: Maximum number of events allowed in the queue
            max_retry_attempts: Maximum number of delivery attempts per event
            retry_delay: Time to wait between retry attempts
            num_workers: Number of worker threads for event processing
        """
        # Core data structures
        self._subscribers: Dict[str, Set[Callable[[Event], None]]] = {}
        self._publishers: Dict[str, Set[str]] = {}
        self._event_queue: Queue = Queue(maxsize=max_events)
        self._dead_letter_queue: Queue = Queue()  # For failed deliveries
        
        # Delivery tracking
        self._delivery_records: Dict[str, DeliveryRecord] = {}
        self._max_retry_attempts = max_retry_attempts
        self._retry_delay = retry_delay
        
        # Thread management
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=num_workers)
        self._running = False
        
        logger.info(
            "Event bus initialized",
            max_events=max_events,
            max_retry_attempts=max_retry_attempts,
            retry_delay_seconds=retry_delay.total_seconds(),
            num_workers=num_workers
        )
        
    async def start(self) -> None:
        """Start the event processing loop."""
        logger.info("Starting event bus processing loop")
        self._running = True
        
        await self._process_events_loop()
        
    async def stop(self) -> None:
        """Stop the event processing loop."""
        logger.info("Stopping event bus processing loop")
        self._running = False
        self._executor.shutdown(wait=True)
        logger.info("Event bus stopped")
        
    def register_publisher(self, publisher_name: str, event_types: List[str]) -> None:
        """
        Register a publisher with the event types it can publish.
        
        Args:
            publisher_name: Unique identifier for the publisher
            event_types: List of event types this publisher can emit
            
        Raises:
            InvalidEventTypeError: If any event type is not valid
        """
        # Validate event types
        invalid_types = [et for et in event_types if et not in EventType.values()]
        if invalid_types:
            error = EventBusError(
                error_code=ErrorCode.BUS_INVALID_EVENT_TYPE,
                message=f"Invalid event types: {invalid_types}",
                details={"invalid_types": invalid_types, "publisher": publisher_name}
            )
            log_error(logger, error)
            raise InvalidEventTypeError(f"Invalid event types: {invalid_types}")
            
        with self._lock:
            if publisher_name not in self._publishers:
                self._publishers[publisher_name] = set()
            self._publishers[publisher_name].update(event_types)
            log_event_bus_activity(
                logger,
                event_type=",".join(event_types),
                action="publisher_registered",
                publisher=publisher_name
            )
    
    def unregister_publisher(self, publisher_name: str) -> None:
        """
        Remove a publisher's registration.
        
        Args:
            publisher_name: Name of the publisher to unregister
        """
        with self._lock:
            if publisher_name in self._publishers:
                del self._publishers[publisher_name]
                logger.debug(f"Unregistered publisher {publisher_name}")

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        Subscribe a handler to a specific event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function that will handle the event
            
        Raises:
            InvalidEventTypeError: If event type is not valid
        """
        if event_type not in EventType.values():
            error = EventBusError(
                error_code=ErrorCode.BUS_INVALID_EVENT_TYPE,
                message=f"Invalid event type: {event_type}",
                details={"event_type": event_type}
            )
            log_error(logger, error)
            raise InvalidEventTypeError(f"Invalid event type: {event_type}")
            
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = set()
            self._subscribers[event_type].add(handler)
            log_event_bus_activity(
                logger,
                event_type=event_type,
                action="subscriber_added",
                handler=handler.__name__ if hasattr(handler, '__name__') else str(handler)
            )
    
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        Remove a handler's subscription to an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove from subscribers
        """
        with self._lock:
            if event_type in self._subscribers and handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
                logger.debug(f"Removed subscriber for event type: {event_type}")

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers asynchronously.
        
        Args:
            event: Event instance to publish
            
        Raises:
            UnregisteredPublisherError: If publisher is not registered for this event type
        """
        with PerformanceLogger(logger, "event_publish", event_type=event.event_type, source=event.source):
            # Verify publisher registration
            if event.source not in self._publishers or \
                event.event_type not in self._publishers[event.source]:
                error = EventBusError(
                    error_code=ErrorCode.BUS_UNREGISTERED_PUBLISHER,
                    message=f"Publisher {event.source} is not registered to publish {event.event_type}",
                    details={"publisher": event.source, "event_type": event.event_type}
                )
                log_error(logger, error)
                raise UnregisteredPublisherError(
                    f"Publisher {event.source} is not registered to publish {event.event_type}"
                )
            
            # Add event to queue
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    self._executor, 
                    self._event_queue.put,
                    event
                )
                log_event_bus_activity(
                    logger,
                    event_type=event.event_type,
                    action="event_published",
                    source=event.source,
                    correlation_id=event.correlation_id
                )
            except Exception as e:
                error = EventBusError(
                    error_code=ErrorCode.BUS_QUEUE_FULL,
                    message="Failed to add event to queue",
                    details={"event": str(event), "error": str(e)},
                    retry_allowed=True
                )
                log_error(logger, error)
                raise
    
    async def _process_events_loop(self) -> None:
        """Main event processing loop."""
        while self._running:
            try:
                loop = asyncio.get_running_loop()
                # Get next event from queue
                event = await loop.run_in_executor(
                    self._executor,
                    self._event_queue.get,
                    True,  # Block until item available
                    1.0    # Timeout after 1 second
                )
                
                # Process event asynchronously
                await self._process_event(event)
                
                # Handle any events in dead letter queue that are ready for retry
                await self._process_dead_letter_queue()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
    
    async def _process_event(self, event: Event) -> None:
        """
        Process an event by calling all subscribed handlers.
        
        Args:
            event: Event to process
        """
        if event.event_type in self._subscribers:
            delivery_tasks = []
            
            for handler in self._subscribers[event.event_type]:
                # Create delivery record
                record = DeliveryRecord(event=event, subscriber=handler)
                self._delivery_records[event.correlation_id] = record
                
                # Schedule delivery
                task = asyncio.create_task(self._deliver_to_subscriber(record))
                delivery_tasks.append(task)
            
            # Wait for all deliveries to complete
            await asyncio.gather(*delivery_tasks)
    
    async def _deliver_to_subscriber(self, record: DeliveryRecord) -> None:
        """
        Attempt to deliver an event to a subscriber with retry logic.
        
        Args:
            record: Delivery record containing event and subscriber
        """
        while record.should_retry(self._max_retry_attempts, self._retry_delay):
            try:
                record.attempts += 1
                record.last_attempt = datetime.now()
                loop = asyncio.get_running_loop()
                # Execute handler in thread pool
                await loop.run_in_executor(
                    self._executor,
                    record.subscriber,
                    record.event
                )
                
                # Successful delivery
                return
                
            except Exception as e:
                record.error = e
                logger.error(
                    f"Error delivering event {record.event} to {record.subscriber} "
                    f"(attempt {record.attempts}/{self._max_retry_attempts}): {e}"
                )

                # Wait before retry
                await asyncio.sleep(self._retry_delay.total_seconds())
        
        # Failed all retry attempts
        self._dead_letter_queue.put(record)
        
    async def _process_dead_letter_queue(self) -> None:
        """Process events in the dead letter queue that are ready for retry."""
        while not self._dead_letter_queue.empty():
            record = self._dead_letter_queue.get()
            
            if record.should_retry(self._max_retry_attempts, self._retry_delay):
                # Attempt redelivery
                await self._deliver_to_subscriber(record)
            else:
                self._dead_letter_queue.put(record)  # Put back if not ready
    
    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get the number of subscribers for an event type.
        
        Args:
            event_type: Event type to check
            
        Returns:
            Number of subscribers for the event type
        """
        return len(self._subscribers.get(event_type, set()))
    
    def get_publisher_events(self, publisher_name: str) -> Set[str]:
        """
        Get all event types a publisher can emit.
        
        Args:
            publisher_name: Name of the publisher to check
            
        Returns:
            Set of event types the publisher can emit
        """
        return self._publishers.get(publisher_name, set())
    
    def get_failed_deliveries(self) -> List[DeliveryRecord]:
        """
        Get all failed event deliveries.
        
        Returns:
            List of delivery records for failed attempts
        """
        failed = []
        while not self._dead_letter_queue.empty():
            failed.append(self._dead_letter_queue.get())
        return failed

    def clear(self) -> None:
        """Clear all events from the queues."""
        while not self._event_queue.empty():
            self._event_queue.get()
        while not self._dead_letter_queue.empty():
            self._dead_letter_queue.get()
