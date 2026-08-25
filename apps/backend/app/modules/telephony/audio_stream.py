import asyncio
import logging
from typing import Dict
from app.modules.voice.vad_service import VoiceActivityDetector
from app.modules.voice.stt_service import stt_service

logger = logging.getLogger(__name__)

class CallAudioBuffer:
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.vad = VoiceActivityDetector()
        self.audio_buffer = bytearray()
        
        # Wire up the VAD callbacks
        self.vad.on_speech_start = self.handle_speech_start
        self.vad.on_speech_stop = self.handle_speech_stop
        
    def handle_speech_start(self, call_id: str):
        # Clear any residual audio, start fresh recording for this utterance
        self.audio_buffer.clear()
        
        # Dispatch event to the central handler for Barge-in logic
        from app.modules.telephony.event_handler import ARIEventHandler
        ARIEventHandler.handle_speech_started({"channel_id": self.call_id})
        
    def handle_speech_stop(self, call_id: str):
        # Trigger STT on the buffered audio
        asyncio.create_task(self._transcribe_buffer())
        
    async def _transcribe_buffer(self):
        # Avoid transcribing silence or extremely short clips
        if len(self.audio_buffer) < 16000: # Less than 0.5 seconds of audio
            return
            
        logger.info(f"[{self.call_id}] Sending {len(self.audio_buffer)} bytes to Faster Whisper")
        transcript, language = await stt_service.transcribe_audio(bytes(self.audio_buffer))
        
        if transcript:
            logger.info(f"[{self.call_id}] Transcribed: '{transcript}' (Language: {language})")
            # Fire an event back to the Telephony Event Handler so the CallStateMachine can process it
            from app.modules.telephony.event_handler import ARIEventHandler
            ARIEventHandler.handle_speech_recognized({
                "channel_id": self.call_id, 
                "text": transcript,
                "language": language
            })

    def receive_chunk(self, chunk: bytes):
        """
        Receives a 20ms chunk (640 bytes) of 16kHz PCM from Asterisk.
        """
        if self.vad.is_speaking:
            self.audio_buffer.extend(chunk)
            
        self.vad.process_audio_chunk(self.call_id, chunk)

class AsteriskAudioSocketServer:
    """
    Listens for raw PCM audio streams from Asterisk via TCP AudioSocket.
    """
    def __init__(self, host: str = "0.0.0.0", port: int = 9090):
        self.host = host
        self.port = port
        self.active_streams: Dict[str, CallAudioBuffer] = {}
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # AudioSocket protocol sends a UUID connecting the stream to a call
        try:
            # 1. Read UUID (16 bytes)
            uuid_bytes = await reader.readexactly(16)
            import uuid
            call_id = str(uuid.UUID(bytes=uuid_bytes))
            logger.info(f"New AudioSocket connection for call {call_id}")
            
            # Initialize buffer and VAD for this call
            self.active_streams[call_id] = CallAudioBuffer(call_id)
            
            # 2. Read audio chunks indefinitely until disconnect
            while True:
                chunk = await reader.read(640) # 20ms at 16kHz 16-bit
                if not chunk:
                    break
                    
                # Pad chunk if it's too small right before disconnect
                if len(chunk) < 640:
                    chunk += b'\x00' * (640 - len(chunk))
                    
                self.active_streams[call_id].receive_chunk(chunk)
                
        except asyncio.IncompleteReadError:
            logger.warning("AudioSocket connection closed prematurely")
        except Exception as e:
            logger.error(f"AudioSocket error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logger.info(f"AudioSocket server listening on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()

audio_server = AsteriskAudioSocketServer()
