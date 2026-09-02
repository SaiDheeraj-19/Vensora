import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
import logging
from dotenv import load_dotenv

# Load production environment variables from .env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path=env_path)

# Setup basic logging to see everything output to terminal
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Import main to ensure all SQLAlchemy models are registered correctly
import app.main

from app.core.providers.registry import registry
from app.core.providers.emotion import LocalTextEmotionProvider
from app.core.providers.llm import GroqProvider
from app.core.providers.vector import QdrantProvider
from app.core.providers.embedding import LocalEmbeddingProvider
from app.modules.telephony.state_machine import CallStateMachine
from app.modules.telephony.schemas import CallStateEnum
from app.modules.ai.agent import process_utterance

async def simulate_live_call():
    print("\n" + "="*60)
    print("🚀 INITIALIZING VENSORA CALL SIMULATION")
    print("="*60 + "\n")
    
    # Register Core Providers
    print("[1/3] Registering Providers (Emotion, LLM, VectorDB)...")
    registry.register("EmotionProvider", LocalTextEmotionProvider())
    registry.register("LLMProvider", GroqProvider())
    
    registry.register("VectorDBProvider", QdrantProvider())
    registry.register("EmbeddingProvider", LocalEmbeddingProvider())
    
    # Simulate a call state machine
    print("[2/3] Connecting Call (Channel: SIM-123)...")
    state_machine = CallStateMachine(initial_state=CallStateEnum.PROCESSING)
    channel_id = "SIM-123"
    
    print("\n📞 Call connected. Type 'exit' to hang up.")
    
    while True:
        try:
            original_utterance = input("\n👤 [YOU]: ")
        except (KeyboardInterrupt, EOFError):
            break
            
        if not original_utterance.strip():
            continue
            
        if original_utterance.strip().lower() in ['exit', 'quit', 'hangup', 'q']:
            print("📞 [CALL ENDED]")
            break
        
        utterance_for_ai = original_utterance
        
        try:
            emotion_provider = registry.get("EmotionProvider")
            emotion_result = emotion_provider.detect_emotion(original_utterance)
            emotion = emotion_result.get("emotion", "neutral")
            score = emotion_result.get("score", 0.0)
            
            if emotion == "anger" and score > 0.6:
                print(f"🚨 [SYSTEM]: High frustration detected ({score:.2f}). Adjusting AI tone...")
                utterance_for_ai = f"{original_utterance} [SYSTEM HINT: The customer is currently speaking with {emotion}]"
        except Exception:
            pass

        print("🤖 [VENSORA THINKING]...")
        response_text = await process_utterance(channel_id, utterance_for_ai)
        
        print("\n" + "="*60)
        print(f"🎧 [VENSORA]: \"{response_text}\"")
        print("="*60)
    
if __name__ == "__main__":
    asyncio.run(simulate_live_call())
