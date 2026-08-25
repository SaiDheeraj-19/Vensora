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
    def handle_speech_started(event: Dict[str, Any]):
        """
        Triggered immediately by the VAD when the customer starts speaking.
        Critical for Barge-in (interruption).
        """
        channel_id = event.get("channel_id")
        if not channel_id:
            return
            
        state_machine = active_calls.get(channel_id)
        if not state_machine:
            return
            
        # If the AI is currently playing audio (RESPONDING state), interrupt it.
        if state_machine.current_state == CallStateEnum.RESPONDING:
            logger.warning(f"[{channel_id}] BARGE-IN DETECTED. Customer interrupted the AI.")
            state_machine.transition_to(CallStateEnum.INTERRUPTED, reason="Customer Barge-In")
            
            # Send command to Asterisk to stop the current media playback immediately
            from app.modules.telephony.ari_client import ari_ws_client
            # In a real ARI client, we'd delete the active playback ID
            logger.info(f"[{channel_id}] Sent ARI command to STOP playback.")

    @staticmethod
    def handle_speech_recognized(event: Dict[str, Any]):
        """
        Triggered when STT engine (Faster Whisper) finishes transcribing an utterance.
        """
        channel_id = event.get("channel_id")
        utterance = event.get("text")
        language = event.get("language", "en")
        
        if not channel_id or not utterance:
            return
            
        state_machine = active_calls.get(channel_id)
        if not state_machine:
            logger.warning(f"Speech recognized for unknown channel {channel_id}")
            return
            
        logger.info(f"User said: {utterance} (Detected Language: {language})")
        state_machine.transition_to(CallStateEnum.PROCESSING, reason="Processing utterance")
        
        # Fire off the AI processing in the background so we don't block the WebSocket loop
        asyncio.create_task(ARIEventHandler._process_ai_response(channel_id, utterance, language, state_machine))
        
    @staticmethod
    async def _process_ai_response(channel_id: str, utterance: str, language: str, state_machine: CallStateMachine):
        # 1. Detect Emotion
        try:
            from app.core.providers.registry import registry
            emotion_provider = registry.get("EmotionProvider")
            emotion_result = emotion_provider.detect_emotion(utterance)
            emotion = emotion_result.get("emotion", "neutral")
            
            # If the user is angry, we append a strict system hint to the utterance
            # so the LangGraph agent is aware of their emotional state
            if emotion == "anger" and emotion_result.get("score", 0.0) > 0.6:
                logger.warning(f"[{channel_id}] High frustration detected in user utterance!")
                utterance = f"{utterance} [SYSTEM HINT: The customer is currently speaking with {emotion}]"
                
        except Exception as e:
            logger.error(f"Failed to run emotion detection: {e}")

        # 2. Call the LangGraph agent
        response_text = await process_utterance(channel_id, utterance)
        logger.info(f"AI Response: {response_text}")
        
        # Check if the AI decided to escalate
        if "I'm having a little trouble understanding. Please hold while I transfer you" in response_text:
            logger.warning(f"[{channel_id}] AI Escalatation Triggered.")
            state_machine.transition_to(CallStateEnum.ESCALATING, reason="AI Confidence Low")
            
            from app.modules.voice.tts_service import tts_service
            # Generate the "please hold" audio
            audio = await tts_service.synthesize_speech(response_text, language=language)
            
            # Play it (Mocking the ARI playback start)
            logger.info(f"[{channel_id}] Playing Escalation TTS to caller.")
            
            # Trigger Asterisk ARI to route the channel to a human queue
            # POST /channels/{channel_id}/continue
            logger.info(f"[{channel_id}] Sending Asterisk Transfer Command to human queue (context: support, exten: human).")
            
            # Transition to TRANSFERRED
            state_machine.transition_to(CallStateEnum.TRANSFERRED, reason="Connected to Human Queue")
            return
        
        # Normal processing
        state_machine.transition_to(CallStateEnum.RESPONDING, reason="Playing TTS")
        
        # Trigger TTS and stream to AudioSocket
        from app.modules.voice.tts_service import tts_service
        try:
            audio_bytes = await tts_service.synthesize_speech(response_text, language=language)
            # In real implementation, these bytes would be written to the AudioSocket TCP stream
            logger.info(f"[{channel_id}] Streamed {len(audio_bytes)} bytes of TTS audio to Asterisk.")
        except Exception as e:
            logger.error(f"TTS streaming failed: {e}")
