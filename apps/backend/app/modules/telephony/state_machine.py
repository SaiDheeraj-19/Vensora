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

    def transition_to(self, new_state: CallStateEnum, reason: str = ""):
        """
        Transitions the call to a new state and records the history.
        """
        logger.info(f"[{self.call_id}] State transition: {self.current_state.name} -> {new_state.name} ({reason})")
        self.current_state = new_state
        self.history.append({
            "state": new_state.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason
        })
        
        # Broadcast the transition to the Admin Dashboard
        import asyncio
        from app.modules.telephony.router import broadcast_call_update
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast_call_update(str(self.call_id), new_state.name, self.caller_id))
        except RuntimeError:
            pass # No running event loop
            
        # If the call ends, persist the final state
        if new_state in [CallStateEnum.COMPLETED, CallStateEnum.FAILED]:
            self._persist_final_state()
        return True
