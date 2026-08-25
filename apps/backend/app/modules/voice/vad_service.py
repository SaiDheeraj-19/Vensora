import logging
from typing import Callable, Any
import webrtcvad

logger = logging.getLogger(__name__)

class VoiceActivityDetector:
    """
    Voice Activity Detection using WebRTC VAD.
    Analyzes incoming 16kHz PCM audio chunks to detect speech state.
    """
    def __init__(self, sample_rate: int = 16000, aggressiveness: int = 3):
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(aggressiveness)
        
        self.is_speaking = False
        self.consecutive_speech_frames = 0
        self.consecutive_silence_frames = 0
        
        # Thresholds (assuming 20ms frames)
        self.speech_start_threshold = 3  # 60ms of speech
        self.speech_stop_threshold = 25  # 500ms of silence
        
        # Callbacks
        self.on_speech_start: Callable[[str], Any] | None = None
        self.on_speech_stop: Callable[[str], Any] | None = None

    def process_audio_chunk(self, call_id: str, audio_bytes: bytes):
        """
        Process a 20ms chunk (320 samples / 640 bytes at 16kHz 16-bit PCM).
        """
        if len(audio_bytes) != 640:
            # VAD requires exactly 10, 20, or 30ms frames.
            # For this phase, we skip malformed frames or buffer them appropriately in the audio stream handler.
            return
            
        try:
            is_speech = self.vad.is_speech(audio_bytes, self.sample_rate)
            
            if is_speech:
                self.consecutive_speech_frames += 1
                self.consecutive_silence_frames = 0
                
                if not self.is_speaking and self.consecutive_speech_frames >= self.speech_start_threshold:
                    self.is_speaking = True
                    logger.debug(f"[{call_id}] SPEECH_START detected")
                    if self.on_speech_start:
                        self.on_speech_start(call_id)
            else:
                self.consecutive_silence_frames += 1
                self.consecutive_speech_frames = 0
                
                if self.is_speaking and self.consecutive_silence_frames >= self.speech_stop_threshold:
                    self.is_speaking = False
                    logger.debug(f"[{call_id}] SPEECH_STOP detected")
                    if self.on_speech_stop:
                        self.on_speech_stop(call_id)
                        
        except Exception as e:
            logger.error(f"VAD processing error: {e}")
