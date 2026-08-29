import asyncio
import logging
import base64
from typing import Dict, Any, Optional
import audioop

from app.modules.voice.vad_service import VoiceActivityDetector
from app.modules.voice.stt_service import stt_service

logger = logging.getLogger(__name__)

class CallAudioBuffer:
    def __init__(self, stream_sid: str, call_sid: str):
        self.stream_sid = stream_sid
        self.call_sid = call_sid
        self.vad = VoiceActivityDetector()
        self.audio_buffer = bytearray()
        
        # Wire up the VAD callbacks
        self.vad.on_speech_start = self.handle_speech_start
        self.vad.on_speech_stop = self.handle_speech_stop
        
    def handle_speech_start(self, call_id: str):
        self.audio_buffer.clear()
        
        from app.modules.telephony.event_handler import TwilioEventHandler
        TwilioEventHandler.handle_speech_started({"stream_sid": self.stream_sid})
        
    def handle_speech_stop(self, call_id: str):
        asyncio.create_task(self._transcribe_buffer())
        
    async def _transcribe_buffer(self):
        # We need a decent chunk of audio to transcribe
        if len(self.audio_buffer) < 16000:
            return
            
        logger.info(f"[{self.stream_sid}] Sending {len(self.audio_buffer)} bytes to STT")
        
        # Buffer is already 16kHz 16-bit PCM at this point
        transcript, language = await stt_service.transcribe_audio(bytes(self.audio_buffer))
        
        if transcript:
            logger.info(f"[{self.stream_sid}] Transcribed: '{transcript}' (Language: {language})")
            from app.modules.telephony.event_handler import TwilioEventHandler
            TwilioEventHandler.handle_speech_recognized({
                "stream_sid": self.stream_sid, 
                "call_sid": self.call_sid,
                "text": transcript,
                "language": language
            })

    def receive_twilio_media(self, b64_payload: str):
        """
        Receives a base64 encoded string of 8kHz mu-law audio from Twilio.
        Decodes it, resamples to 16kHz PCM, and processes it through the VAD.
        """
        try:
            # 1. Decode base64
            ulaw_audio = base64.b64decode(b64_payload)
            
            # 2. Decode 8kHz mu-law to 8kHz 16-bit PCM
            pcm_8k = audioop.ulaw2lin(ulaw_audio, 2)
            
            # 3. Resample 8kHz PCM to 16kHz PCM
            pcm_16k, _ = audioop.ratecv(pcm_8k, 2, 1, 8000, 16000, None)
            
            # 4. Feed to buffer and VAD
            if self.vad.is_speaking:
                self.audio_buffer.extend(pcm_16k)
                
            # VAD is triggered based on the call_sid and the 16kHz audio chunk
            self.vad.process_audio_chunk(self.call_sid, pcm_16k)
            
        except Exception as e:
            logger.error(f"Error processing Twilio media: {e}")

class TwilioStreamManager:
    """
    Manages active Twilio WebSocket media streams.
    """
    def __init__(self):
        self.active_streams: Dict[str, CallAudioBuffer] = {}
        
    def start_stream(self, stream_sid: str, call_sid: str):
        logger.info(f"Started tracking stream {stream_sid} for call {call_sid}")
        self.active_streams[stream_sid] = CallAudioBuffer(stream_sid, call_sid)
        
    def handle_media(self, stream_sid: str, payload: str):
        if stream_sid in self.active_streams:
            self.active_streams[stream_sid].receive_twilio_media(payload)
            
    def stop_stream(self, stream_sid: str):
        if stream_sid in self.active_streams:
            logger.info(f"Stopped tracking stream {stream_sid}")
            del self.active_streams[stream_sid]

# Singleton instance for managing Twilio streams
twilio_stream_manager = TwilioStreamManager()
