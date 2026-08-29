import logging
import json
import base64
import asyncio
import audioop
from typing import Dict, Any
from fastapi import WebSocket

from app.modules.telephony.state_machine import CallStateMachine
from app.modules.telephony.schemas import CallStateEnum
from app.modules.ai.agent import process_utterance
from app.modules.telephony.audio_stream import twilio_stream_manager

logger = logging.getLogger(__name__)

# In-memory store of active call state machines
active_calls: Dict[str, CallStateMachine] = {}
# Active Twilio WebSockets for streaming audio back
active_websockets: Dict[str, WebSocket] = {}

class TwilioEventHandler:
    """
    Dispatches and processes Twilio Media Stream WebSocket events.
    """
    @staticmethod
    async def handle_stream(websocket: WebSocket):
        stream_sid = None
        call_sid = None
        
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            event = data.get("event")
            
            if event == "start":
                stream_sid = data["start"]["streamSid"]
                call_sid = data["start"]["callSid"]
                logger.info(f"Twilio stream started: {stream_sid} for call {call_sid}")
                
                twilio_stream_manager.start_stream(stream_sid, call_sid)
                active_websockets[stream_sid] = websocket
                
                state_machine = CallStateMachine(initial_state=CallStateEnum.INITIATING)
                active_calls[call_sid] = state_machine
                state_machine.transition_to(CallStateEnum.LISTENING, reason="Twilio connected")
                
            elif event == "media":
                if stream_sid:
                    payload = data["media"]["payload"]
                    twilio_stream_manager.handle_media(stream_sid, payload)
                    
            elif event == "stop":
                logger.info(f"Twilio stream stopped: {stream_sid}")
                if stream_sid:
                    twilio_stream_manager.stop_stream(stream_sid)
                    active_websockets.pop(stream_sid, None)
                if call_sid and call_sid in active_calls:
                    active_calls[call_sid].transition_to(CallStateEnum.COMPLETED, reason="Twilio Disconnected")
                    del active_calls[call_sid]
                break

    @staticmethod
    def handle_speech_started(event: Dict[str, Any]):
        """
        Triggered immediately by the VAD when the customer starts speaking.
        Critical for Barge-in (interruption).
        """
        stream_sid = event.get("stream_sid")
        if not stream_sid:
            return
            
        websocket = active_websockets.get(stream_sid)
        if not websocket:
            return
            
        # Clear the Twilio buffer to instantly stop AI audio playback
        clear_msg = {
            "event": "clear",
            "streamSid": stream_sid
        }
        
        # Fire-and-forget the clear message
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(websocket.send_text(json.dumps(clear_msg)))
            logger.info(f"[{stream_sid}] BARGE-IN DETECTED. Sent 'clear' to Twilio.")
        except RuntimeError:
            pass

    @staticmethod
    def handle_speech_recognized(event: Dict[str, Any]):
        """
        Triggered when STT engine finishes transcribing an utterance.
        """
        stream_sid = event.get("stream_sid")
        call_sid = event.get("call_sid")
        utterance = event.get("text")
        language = event.get("language", "en")
        
        if not stream_sid or not utterance:
            return
            
        state_machine = active_calls.get(call_sid)
        if state_machine:
            state_machine.transition_to(CallStateEnum.PROCESSING, reason="Processing utterance")
        
        asyncio.create_task(TwilioEventHandler._process_ai_response(stream_sid, call_sid, utterance, language, state_machine))
        
    @staticmethod
    async def _process_ai_response(stream_sid: str, call_sid: str, utterance: str, language: str, state_machine: CallStateMachine):
        websocket = active_websockets.get(stream_sid)
        if not websocket:
            return

        # 1. Detect Emotion (Mocked here for simplicity, use provider logic in production)
        try:
            from app.core.providers.registry import registry
            emotion_provider = registry.get("EmotionProvider")
            if emotion_provider:
                emotion_result = emotion_provider.detect_emotion(utterance)
                emotion = emotion_result.get("emotion", "neutral")
                if emotion == "anger" and emotion_result.get("score", 0.0) > 0.6:
                    utterance = f"{utterance} [SYSTEM HINT: The customer is currently speaking with {emotion}]"
        except Exception:
            pass

        # 2. Call the LangGraph AI
        response_text = await process_utterance(call_sid, utterance)
        logger.info(f"AI Response: {response_text}")
        
        if state_machine:
            state_machine.transition_to(CallStateEnum.RESPONDING, reason="Playing TTS")
        
        # 3. Generate TTS
        from app.modules.voice.tts_service import tts_service
        try:
            # TTS is 16kHz PCM
            audio_bytes_16k = await tts_service.synthesize_speech(response_text, language=language)
            
            # 4. Convert 16kHz PCM to 8kHz mu-law for Twilio
            pcm_8k, _ = audioop.ratecv(audio_bytes_16k, 2, 1, 16000, 8000, None)
            ulaw_audio = audioop.lin2ulaw(pcm_8k, 2)
            
            b64_audio = base64.b64encode(ulaw_audio).decode("utf-8")
            
            # 5. Send Media payload to Twilio
            media_msg = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": b64_audio
                }
            }
            await websocket.send_text(json.dumps(media_msg))
            logger.info(f"[{stream_sid}] Streamed AI response back to Twilio.")
            
        except Exception as e:
            logger.error(f"TTS streaming failed: {e}")
