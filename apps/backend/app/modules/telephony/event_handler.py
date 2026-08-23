import logging
from typing import Dict, Any

from app.modules.telephony.state_machine import CallStateMachine
from app.modules.telephony.schemas import CallStateEnum
from app.modules.ai.agent import process_utterance
import asyncio

logger = logging.getLogger(__name__)

# In-memory store of active call state machines (use Redis in Phase 2)
active_calls: Dict[str, CallStateMachine] = {}

class ARIEventHandler:
    """
    Dispatches and processes Asterisk ARI WebSocket events.
    """
    
    @staticmethod
    def handle_event(event: Dict[str, Any]):
        event_type = event.get("type")
        if not event_type:
            return
            
        logger.debug(f"Received ARI Event: {event_type}")
        
        handler_method = getattr(ARIEventHandler, f"handle_{event_type.lower()}", None)
        if handler_method:
            handler_method(event)
        else:
            logger.debug(f"No explicit handler for {event_type}")
            
    @staticmethod
    def handle_stasisstart(event: Dict[str, Any]):
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        
        if not channel_id:
            return
            
        logger.info(f"StasisStart for channel {channel_id}. Initiating Call State Machine.")
        
        # Initialize state machine for this call
        state_machine = CallStateMachine(initial_state=CallStateEnum.INITIATING)
        active_calls[channel_id] = state_machine
        
        # Transition to RINGING (since Stasis just started)
        state_machine.transition_to(CallStateEnum.RINGING, reason="Stasis Start")
        
        # In a real scenario, we would trigger ARI to Answer() the channel here.
        # This triggers the handoff to the AI engine (listening phase).

    @staticmethod
    def handle_channelhanguprequest(event: Dict[str, Any]):
        channel = event.get("channel", {})
        channel_id = channel.get("id")
        
        if not channel_id:
            return
            
        logger.info(f"ChannelHangupRequest for {channel_id}")
        
        state_machine = active_calls.get(channel_id)
        if state_machine:
            state_machine.transition_to(CallStateEnum.COMPLETED, reason="Hangup Request")
            # Cleanup
            del active_calls[channel_id]

    @staticmethod
    def handle_speech_recognized(event: Dict[str, Any]):
        """
        Mock event for when STT engine (Faster Whisper) finishes transcribing an utterance.
        """
        channel_id = event.get("channel_id")
        utterance = event.get("text")
        
        if not channel_id or not utterance:
            return
            
        state_machine = active_calls.get(channel_id)
        if not state_machine:
            logger.warning(f"Speech recognized for unknown channel {channel_id}")
            return
            
        logger.info(f"User said: {utterance}")
        state_machine.transition_to(CallStateEnum.PROCESSING, reason="Processing utterance")
        
        # Fire off the AI processing in the background so we don't block the WebSocket loop
        asyncio.create_task(ARIEventHandler._process_ai_response(channel_id, utterance, state_machine))
        
    @staticmethod
    async def _process_ai_response(channel_id: str, utterance: str, state_machine: CallStateMachine):
        # Call the LangGraph agent
        response_text = await process_utterance(channel_id, utterance)
        logger.info(f"AI Response: {response_text}")
        
        # In a real scenario, this response_text goes to TTS (Piper)
        # Then Asterisk is instructed to play the resulting audio file.
        
        state_machine.transition_to(CallStateEnum.RESPONDING, reason="Playing TTS")
