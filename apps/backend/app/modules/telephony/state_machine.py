from typing import Optional, Dict, Any
from app.modules.telephony.schemas import CallStateEnum
import logging

logger = logging.getLogger(__name__)

class CallStateMachine:
    """
    Manages state transitions for an Asterisk call.
    Validates that a transition from current_state to new_state is allowed.
    """
    
    VALID_TRANSITIONS = {
        CallStateEnum.INITIATING: {CallStateEnum.RINGING, CallStateEnum.FAILED},
        CallStateEnum.RINGING: {CallStateEnum.CONNECTED, CallStateEnum.FAILED},
        CallStateEnum.CONNECTED: {
            CallStateEnum.LISTENING, 
            CallStateEnum.SPEAKING, 
            CallStateEnum.COMPLETED, 
            CallStateEnum.FAILED,
            CallStateEnum.ESCALATING
        },
        CallStateEnum.LISTENING: {CallStateEnum.PROCESSING, CallStateEnum.INTERRUPTED, CallStateEnum.FAILED},
        CallStateEnum.PROCESSING: {CallStateEnum.SPEAKING, CallStateEnum.FAILED, CallStateEnum.ESCALATING},
        CallStateEnum.SPEAKING: {CallStateEnum.LISTENING, CallStateEnum.INTERRUPTED, CallStateEnum.COMPLETED, CallStateEnum.FAILED},
        CallStateEnum.INTERRUPTED: {CallStateEnum.LISTENING, CallStateEnum.PROCESSING, CallStateEnum.FAILED},
        CallStateEnum.ESCALATING: {CallStateEnum.TRANSFERRED, CallStateEnum.FAILED},
        CallStateEnum.TRANSFERRED: {CallStateEnum.COMPLETED},
        CallStateEnum.COMPLETED: set(),
        CallStateEnum.FAILED: set()
    }

    def __init__(self, initial_state: CallStateEnum = CallStateEnum.INITIATING):
        self.state = initial_state
        self.context: Dict[str, Any] = {}

    def transition_to(self, new_state: CallStateEnum, reason: Optional[str] = None) -> bool:
        """Attempts to transition to a new state."""
        allowed_states = self.VALID_TRANSITIONS.get(self.state, set())
        
        if new_state not in allowed_states:
            logger.error(f"Invalid transition attempted: {self.state} -> {new_state}. Reason: {reason}")
            return False
            
        logger.info(f"Transitioning: {self.state} -> {new_state}. Reason: {reason}")
        self.state = new_state
        return True
