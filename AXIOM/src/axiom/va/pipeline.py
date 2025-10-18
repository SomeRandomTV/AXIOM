"""Pipeline orchestration for Virtual Assistant processing."""

import logging
import uuid
from typing import Optional, Tuple

from ..bus.event_bus import EventBus
from ..policy.engine import PolicyEngine
from ..policy.validators import ContentFilterPolicy, ResponseLengthPolicy, InputSanitizationPolicy
from .dm import DialogManager

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Main orchestration pipeline for Virtual Assistant processing.
    Coordinates input/output processing and component interaction.
    """

    def __init__(self, event_bus: EventBus, intent_config_path: Optional[str] = None, config: Optional[dict] = None):
        """
        Initialize the pipeline.
        Args:
            event_bus: Event bus instance
            intent_config_path: Path to intent patterns JSON config
            config: Optional pipeline configuration dictionary
        """
        self._event_bus = event_bus
        self._dialog_manager = DialogManager(event_bus, intent_config_path=intent_config_path)
        self._session_id = None
        # Initialize and register policies
        self._policy_engine = PolicyEngine()
        self._policy_engine.add_policy(ContentFilterPolicy())
        self._policy_engine.add_policy(ResponseLengthPolicy())
        self._policy_engine.add_policy(InputSanitizationPolicy())
        self.config = config or {}
        self._performance_stats = []
        # Import and initialize state store
        from ..state.store import StateStore
        from ..state.models import ConversationTurn
        db_path = None
        if config and "database" in config and "path" in config["database"]:
            db_path = config["database"]["path"]
        else:
            # Fallback to default path
            from ..config import ROOT_DIR
            db_path = ROOT_DIR / "data" / "axiom.db"
        self._state_store = StateStore(db_path)
        self._ConversationTurn = ConversationTurn
    def set_config(self, config: dict) -> None:
        """Update pipeline configuration."""
        self.config = config

    def get_performance_stats(self) -> list:
        """Return collected performance stats."""
        return self._performance_stats

    
    def start_session(self) -> str:
        """
        Start a new conversation session.
        
        Returns:
            New session ID
        """
        self._session_id = str(uuid.uuid4())
        return self._session_id
    
    def end_session(self) -> None:
        """End the current conversation session."""
        self._session_id = None
    
    async def process_text_input(self, text: str, session_id: Optional[str] = None) -> str:
        """
        Process text input through the pipeline.
        
        Args:
            text: User input text
            session_id: Optional session ID (uses current session if None)
            
        Returns:
            Assistant response text
        """
        # Ensure we have a session
        if session_id is None:
            if self._session_id is None:
                self._session_id = self.start_session()
            session_id = self._session_id
        
        # Policy check for input
        input_result = self._policy_engine.evaluate_input(text)
        if not input_result.passed:
            return f"Input rejected due to policy violation: {input_result.violations}"
        import time
        start_time = time.perf_counter()
        try:
            # Process through dialog manager
            response = await self._dialog_manager.process_input(session_id, text)
            # Policy check for response
            response_result = self._policy_engine.evaluate_response(response)
            elapsed = time.perf_counter() - start_time
            self._performance_stats.append({
                "session_id": session_id,
                "input": text,
                "response": response,
                "processing_time": elapsed,
                "input_policy": input_result.__dict__,
                "response_policy": response_result.__dict__
            })
            # Log conversation turn
            try:
                turn = self._ConversationTurn(
                    session_id=session_id,
                    user_input=text,
                    assistant_response=response,
                    detected_intent=None,  # Could be set if available
                    processing_time=int(elapsed * 1000),
                    timestamp=None,
                    metadata=None
                )
                import datetime
                turn.timestamp = datetime.datetime.now()
                self._state_store.log_conversation_turn(turn)
            except Exception as log_exc:
                logger.error(f"Failed to log conversation turn: {log_exc}")
            if not response_result.passed:
                return f"Response blocked due to policy violation: {response_result.violations}"
            return response
        except Exception as e:
            logger.error(f"Error in pipeline processing: {e}")
            return "I'm sorry, but something went wrong. Please try again."