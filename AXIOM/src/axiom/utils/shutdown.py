"""
Graceful shutdown handler for AXIOM.

Manages orderly shutdown of all components with:
- 15-second timeout
- Retry logic for stuck operations (2 retries, then kill)
- State preservation
- Log flushing
- Resource cleanup
"""

import asyncio
import signal
import sys
import time
from typing import Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from axiom.utils.logging import get_logger, log_error
from axiom.utils.errors import ErrorCode, SystemError

logger = get_logger(__name__)


class ShutdownHandler:
    """
    Manages graceful shutdown of AXIOM components.
    """
    
    SHUTDOWN_TIMEOUT = 15.0  # seconds
    MAX_RETRY_ATTEMPTS = 2
    RETRY_DELAY = 1.0  # seconds
    
    def __init__(self):
        self._shutdown_in_progress = False
        self._components: List[tuple[str, Callable]] = []
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Shutdown handler initialized")
    
    def register_component(self, name: str, shutdown_fn: Callable):
        """
        Register a component for graceful shutdown.
        
        Args:
            name: Component name
            shutdown_fn: Function to call for shutdown (can be async or sync)
        """
        self._components.append((name, shutdown_fn))
        logger.debug(f"Registered shutdown handler for {name}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.warning(f"Received signal {signal_name}, initiating graceful shutdown")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """
        Perform graceful shutdown sequence.
        
        Shutdown order:
        1. Stop accepting new requests
        2. Finish processing in-flight events
        3. Flush logs
        4. Close database connections
        5. Save state/cleanup
        """
        if self._shutdown_in_progress:
            logger.warning("Shutdown already in progress")
            return
        
        self._shutdown_in_progress = True
        start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("INITIATING GRACEFUL SHUTDOWN")
        logger.info("=" * 60)
        
        try:
            # Shutdown components in reverse order (LIFO)
            for name, shutdown_fn in reversed(self._components):
                elapsed = time.time() - start_time
                remaining_time = self.SHUTDOWN_TIMEOUT - elapsed
                
                if remaining_time <= 0:
                    logger.error(
                        f"Shutdown timeout exceeded, forcing shutdown of remaining components",
                        elapsed_seconds=elapsed
                    )
                    break
                
                await self._shutdown_component(name, shutdown_fn, remaining_time)
            
            # Final cleanup
            self._executor.shutdown(wait=False)
            
            total_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info(f"SHUTDOWN COMPLETED in {total_time:.2f}s")
            logger.info("=" * 60)
        
        except Exception as e:
            error = SystemError(
                error_code=ErrorCode.SYSTEM_SHUTDOWN_FAILED,
                message=f"Shutdown failed: {str(e)}",
                details={"error": str(e)}
            )
            log_error(logger, error)
        
        finally:
            # Force exit if shutdown didn't complete cleanly
            if time.time() - start_time > self.SHUTDOWN_TIMEOUT:
                logger.critical("Forcing immediate shutdown")
                sys.exit(1)
    
    async def _shutdown_component(
        self,
        name: str,
        shutdown_fn: Callable,
        timeout: float
    ):
        """
        Shutdown a single component with retry logic.
        
        Args:
            name: Component name
            shutdown_fn: Shutdown function
            timeout: Maximum time to wait
        """
        logger.info(f"Shutting down {name}...", timeout_seconds=timeout)
        
        for attempt in range(1, self.MAX_RETRY_ATTEMPTS + 2):  # +1 for initial, +1 for final kill
            try:
                # Determine if function is async
                if asyncio.iscoroutinefunction(shutdown_fn):
                    await asyncio.wait_for(shutdown_fn(), timeout=timeout)
                else:
                    # Run sync function in executor with timeout
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(self._executor, shutdown_fn),
                        timeout=timeout
                    )
                
                logger.info(f"Successfully shut down {name}")
                return
            
            except asyncio.TimeoutError:
                if attempt <= self.MAX_RETRY_ATTEMPTS:
                    logger.warning(
                        f"Shutdown timeout for {name} (attempt {attempt}/{self.MAX_RETRY_ATTEMPTS}), retrying...",
                        attempt=attempt
                    )
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    logger.error(
                        f"Failed to shut down {name} after {self.MAX_RETRY_ATTEMPTS} retries, killing operation",
                        component=name,
                        attempts=attempt
                    )
                    # Log as critical since we're killing the operation
                    error = SystemError(
                        error_code=ErrorCode.SYSTEM_TIMEOUT,
                        message=f"Shutdown timeout for {name}",
                        details={"component": name, "attempts": attempt}
                    )
                    log_error(logger, error)
                    return
            
            except Exception as e:
                logger.error(
                    f"Error shutting down {name}: {str(e)}",
                    component=name,
                    error=str(e),
                    attempt=attempt
                )
                
                if attempt <= self.MAX_RETRY_ATTEMPTS:
                    logger.info(f"Retrying {name} shutdown...")
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Giving up on {name} after {attempt} attempts")
                    return
    
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._shutdown_in_progress


# Global shutdown handler instance
_shutdown_handler: Optional[ShutdownHandler] = None


def get_shutdown_handler() -> ShutdownHandler:
    """Get or create global shutdown handler."""
    global _shutdown_handler
    if _shutdown_handler is None:
        _shutdown_handler = ShutdownHandler()
    return _shutdown_handler


def register_shutdown_handler(name: str, shutdown_fn: Callable):
    """
    Register a component for graceful shutdown.
    
    Args:
        name: Component name
        shutdown_fn: Function to call during shutdown
    """
    handler = get_shutdown_handler()
    handler.register_component(name, shutdown_fn)


async def initiate_shutdown():
    """Initiate graceful shutdown sequence."""
    handler = get_shutdown_handler()
    await handler.shutdown()


def is_shutting_down() -> bool:
    """Check if system is shutting down."""
    handler = get_shutdown_handler()
    return handler.is_shutting_down()
