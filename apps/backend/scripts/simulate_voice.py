import sys
import os
import subprocess
import asyncio
import logging
import speech_recognition as sr
import websockets
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.ERROR) # Hide noisy logs for voice sim

import app.main
from groq import Groq
from sarvamai import SarvamAI
from sarvamai.play import save
from app.core.providers.registry import registry
from app.core.providers.emotion import LocalTextEmotionProvider
from app.core.providers.llm import GroqProvider
from app.core.providers.vector import QdrantProvider
from app.core.providers.embedding import LocalEmbeddingProvider
from app.modules.telephony.state_machine import CallStateMachine
from app.modules.telephony.schemas import CallStateEnum
from app.modules.ai.agent import process_utterance

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
sarvam_client = SarvamAI(api_subscription_key=os.environ.get("SARVAM_API_KEY"))

async def simulate_live_voice():
    print("\n" + "="*60)
    print("🚀 VENSORA VOICE SIMULATION (MacOS)")
    print("="*60 + "\n")
    
    registry.register("EmotionProvider", LocalTextEmotionProvider())
    registry.register("LLMProvider", GroqProvider())
    registry.register("VectorDBProvider", QdrantProvider())
    registry.register("EmbeddingProvider", LocalEmbeddingProvider())
    
    channel_id = "VOICE-123"
    ws_connection = None
    
    async def bg_websocket(call_id):
        nonlocal ws_connection
        uri = "ws://localhost:8000/api/v1/telephony/ws/live-calls"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    ws_connection = websocket
                    await websocket.send(json.dumps({"action": "register", "call_id": call_id, "state": "LISTENING", "caller_id": "Local Terminal"}))
                    
                    while True:
                        msg = await websocket.recv()
                        data = json.loads(msg)
                        if data.get("event") == "barge_in" and data.get("call_id") == call_id:
                            print(f"\n🚨 [ADMIN BARGE-IN]: {data.get('message')}")
                            barge_text = data.get("message").replace("'", "").replace('"', "")
                            os.system(f"say '{barge_text}' &")
            except Exception as e:
                ws_connection = None
                await asyncio.sleep(2)
                
    asyncio.create_task(bg_websocket(channel_id))
    
    async def send_transcript(speaker, text):
        if ws_connection:
            try:
                await ws_connection.send(json.dumps({"action": "transcript", "call_id": channel_id, "speaker": speaker, "text": text}))
            except Exception:
                pass
    
    print("📞 Voice Call connected.")
    print("💡 The first time you press ENTER, your Mac terminal will ask for Microphone permission. Please click 'OK' or 'Allow'.\n")
    
    # Initialize speech recognizer
    r = sr.Recognizer()
    r.pause_threshold = 0.5 # Reduce silence wait from 0.8s to 0.5s for faster response
    
    def capture_audio(recognizer):
        with sr.Microphone() as source:
            print("\n🎙️  Listening... (Speak naturally, I'll detect when you stop. Press Ctrl+C to quit)")
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            try:
                return recognizer.listen(source, timeout=10, phrase_time_limit=15)
            except sr.WaitTimeoutError:
                return None
    
    while True:
        try:
            audio = await asyncio.to_thread(capture_audio, r)
            if audio is None:
                continue
                
            # Save audio for Groq Whisper
            with open("/tmp/vensora_input.wav", "wb") as f:
                f.write(audio.get_wav_data())
                
        except (KeyboardInterrupt, EOFError):
            print("\n📞 [CALL ENDED]")
            break
        except Exception as e:
            print(f"\n❌ Microphone error: {e}")
            break
            
        print("⏳ Transcribing...")
        
        try:
            with open("/tmp/vensora_input.wav", "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=("vensora_input.wav", file.read()),
                    model="whisper-large-v3",
                )
            original_utterance = transcription.text
            if not original_utterance.strip():
                print("❌ Didn't catch that. Please try again.\n")
                continue
                
            print(f"👤 [YOU SAID]: \"{original_utterance}\"")
            await send_transcript("customer", original_utterance)
        except Exception as e:
            print(f"❌ Transcription failed: {e}\n")
            continue

        utterance_for_ai = original_utterance
        print("🤖 [VENSORA THINKING]...")
        
        try:
            response_text = await process_utterance(channel_id, utterance_for_ai)
        except Exception as e:
            print(f"AI processing failed: {e}")
            continue
        
        print("\n" + "="*60)
        print(f"🎧 [VENSORA]: \"{response_text}\"")
        print("="*60 + "\n")
        await send_transcript("ai", response_text)
        
        # Clean up text for TTS
        tts_text = response_text.replace("'", "").replace('"', "")
        
        print("🔊 [GENERATING VOICE VIA SARVAM AI]...")
        try:
            sarvam_response = sarvam_client.text_to_speech.convert(
                text=tts_text,
                language_code="en-IN",
                model="bulbul:v3",
                speaker="ritu"
            )
            save(sarvam_response, "/tmp/vensora_output.wav")
            os.system("afplay /tmp/vensora_output.wav")
        except Exception as e:
            print(f"❌ Sarvam AI TTS failed: {e}. Falling back to Mac TTS...")
            os.system(f"say '{tts_text}'")
        
if __name__ == "__main__":
    asyncio.run(simulate_live_voice())
