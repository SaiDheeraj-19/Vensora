import logging
import time
import io
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy initialization flag
_MODEL_INITIALIZED = False
_WHISPER_MODEL = None

class STTService:
    """
    Speech-to-Text service utilizing Faster Whisper for low-latency transcription.
    """
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

    def _initialize_model(self):
        """Lazy load the Whisper model into memory on first use and warm it up."""
        global _MODEL_INITIALIZED, _WHISPER_MODEL
        if not _MODEL_INITIALIZED:
            try:
                from faster_whisper import WhisperModel
                import numpy as np
                logger.info(f"Initializing Faster Whisper (model={self.model_size}, device={self.device})")
                _WHISPER_MODEL = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
                
                # Model Warm-up
                logger.info("Running STT model warm-up...")
                warmup_audio = np.zeros(16000, dtype=np.float32) # 1 second of silence
                _WHISPER_MODEL.transcribe(warmup_audio, beam_size=1)
                logger.info("STT model warm-up complete.")
                
                _MODEL_INITIALIZED = True
            except ImportError:
                logger.warning("faster-whisper not installed. STT running in MOCK mode.")
                _MODEL_INITIALIZED = True
                _WHISPER_MODEL = None

    async def transcribe_audio(self, audio_data: bytes) -> tuple[str, str]:
        """
        Transcribe raw PCM audio bytes. Returns (transcript, language_code).
        """
        self._initialize_model()
        
        start_time = time.time()
        
        if not _WHISPER_MODEL:
            # Mock mode
            latency = time.time() - start_time
            logger.info(f"STT Latency (MOCK): {latency:.3f}s")
            return "This is a mock transcription because faster-whisper is not installed.", "en"
            
        try:
            import numpy as np
            import asyncio
            
            # Convert raw 16-bit PCM bytes to a float32 numpy array normalized to [-1.0, 1.0]
            # This is the format faster_whisper expects if not providing a file with a header.
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Run the blocking transcribe call in a separate thread to prevent blocking the async loop.
            # We apply a strict timeout to prevent hung inference from breaking the call flow.
            def _blocking_transcribe():
                segments, info = _WHISPER_MODEL.transcribe(audio_array, beam_size=1, vad_filter=True)
                transcript = "".join(segment.text + " " for segment in segments)
                return transcript.strip(), info

            transcript, info = await asyncio.wait_for(
                asyncio.to_thread(_blocking_transcribe),
                timeout=10.0
            )
            
            latency = time.time() - start_time
            logger.info(f"STT Latency: {latency:.3f}s (Audio-to-STT) - Language: {info.language} - Confidence: {info.language_probability:.2f}")
            
            return transcript, info.language
            
        except asyncio.TimeoutError:
            logger.error("Faster Whisper inference timed out after 10 seconds.")
            return "", "en"
        except Exception as e:
            logger.error(f"Faster Whisper transcription failed: {e}", exc_info=True)
            return "", "en"

stt_service = STTService()
