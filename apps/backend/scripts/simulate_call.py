import os
import asyncio
import logging
from dotenv import load_dotenv

# Load production environment variables from .env
load_dotenv()

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
    
    # We mock Qdrant and Embeddings for this test so we don't need a real DB running
    os.environ["QDRANT_HOST"] = "mock"
    registry.register("VectorDBProvider", QdrantProvider())
    registry.register("EmbeddingProvider", LocalEmbeddingProvider())
    
    # Simulate a call state machine
    print("[2/3] Connecting Call (Channel: SIM-123)...")
    state_machine = CallStateMachine(initial_state=CallStateEnum.PROCESSING)
    channel_id = "SIM-123"
    
    # The utterance the customer just screamed into the phone
    original_utterance = "This is ridiculous! Where the hell is my shipment? I've been waiting all week and your company is completely useless!"
    print(f"\n📞 [CUSTOMER SPEAKS]: \"{original_utterance}\"")
    
    # -------------------------------------------------------------
    # THIS REPLICATES THE EXACT LOGIC IN event_handler.py
    # -------------------------------------------------------------
    utterance_for_ai = original_utterance
    
    try:
        emotion_provider = registry.get("EmotionProvider")
        emotion_result = emotion_provider.detect_emotion(original_utterance)
        emotion = emotion_result.get("emotion", "neutral")
        score = emotion_result.get("score", 0.0)
        
        print(f"\n🧠 [EMOTION DETECTION]: {emotion.upper()} (Confidence: {score:.2f})")
        
        if emotion == "anger" and score > 0.6:
            print(f"🚨 [ALERT]: High frustration detected. Intercepting transcript before AI processing...")
            utterance_for_ai = f"{original_utterance} [SYSTEM HINT: The customer is currently speaking with {emotion}]"
            
    except Exception as e:
        print(f"Emotion detection failed: {e}")

    print("\n🤖 [LANGGRAPH AI THINKING]...")
    response_text = await process_utterance(channel_id, utterance_for_ai)
    
    print("\n" + "="*60)
    print("🎤 [AI RESPONSE TTS]:")
    print(f"\"{response_text}\"")
    print("="*60 + "\n")
    
if __name__ == "__main__":
    asyncio.run(simulate_live_call())
