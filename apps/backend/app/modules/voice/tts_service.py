import logging
import time
import os
import asyncio

logger = logging.getLogger(__name__)

class TTSService:
    """
    Text-to-Speech service utilizing Piper for ultra-low latency voice synthesis.
    Integrates with a local Piper HTTP server (e.g., Wyoming-Piper or a custom FastAPI wrapper).
    """
    def __init__(self, default_voice_model: str = "en_US-lessac-medium"):
        # Map detected languages to their corresponding Piper models
        self.voice_models = {
            "en": default_voice_model,
            "hi": "hi_IN-swara-medium",  # Hindi voice
            "ne": "ne_NP-google-medium", # Nepali voice
        }
        # Use an environment variable for the Piper server URL
        self.piper_url = os.getenv("PIPER_URL", "http://localhost:5000/api/tts")
        self.enabled = True
        
        try:
            import httpx
            self.httpx_client = httpx.AsyncClient(timeout=5.0)
        except ImportError:
            logger.warning("httpx not installed. TTS running in MOCK mode.")
            self.httpx_client = None
            self.enabled = False

    async def synthesize_speech(self, text: str, speed: float = 1.0, language: str = "en") -> bytes:
        """
        Synthesize text into raw 16kHz PCM audio bytes for Asterisk playback.
        Includes timeout handling and cancellation support for barge-in.
        """
        start_time = time.time()
        logger.debug(f"Synthesizing TTS for: '{text}' (Speed: {speed}, Language: {language})")
        
        # Select the correct Piper voice for the language, fallback to English
        voice_model = self.voice_models.get(language, self.voice_models["en"])
        
        if not self.enabled or not self.httpx_client:
            # Mock mode fallback
            await asyncio.sleep(0.1) # Simulate minimal processing time
            latency = time.time() - start_time
            logger.info(f"MOCK TTS Synthesis Latency: {latency:.3f}s")
            return b'\x00\x00' * 16000 # 1 second of silence
            
        try:
            # We use an HTTP POST to the Piper server.
            # The server is expected to return raw PCM audio (16kHz, 16-bit, mono) or WAV.
            # If WAV, the AudioSocket server logic will handle stripping the header.
            response = await self.httpx_client.post(
                self.piper_url,
                json={"text": text, "model": voice_model, "length_scale": 1.0 / speed},
            )
            response.raise_for_status()
            audio_bytes = response.content
            
            latency = time.time() - start_time
            logger.info(f"Piper TTS Synthesis Latency: {latency:.3f}s for {len(audio_bytes)} bytes")
            
            return audio_bytes
            
        except asyncio.CancelledError:
            # Triggered during barge-in if the task is cancelled mid-flight
            logger.warning("TTS Synthesis cancelled (likely due to user interruption).")
            raise
        except Exception as e:
            logger.error(f"Piper TTS Synthesis failed: {e}")
            # Fallback to silence to prevent crashing the Asterisk stream
            return b'\x00\x00' * 16000

tts_service = TTSService()
