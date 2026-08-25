from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router

from app.core.logger import setup_logging
from app.core.middleware import CorrelationIdMiddleware
from app.core.exceptions import setup_exception_handlers
from contextlib import asynccontextmanager
import asyncio
from app.modules.telephony.services.websocket_client import ari_ws_client
from app.modules.telephony.audio_stream import audio_server

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured JSON logging
    setup_logging()
    # Register Providers
    from app.core.providers.registry import registry
    from app.core.providers.vector import QdrantProvider
    from app.core.providers.embedding import LocalEmbeddingProvider
    from app.core.providers.emotion import LocalTextEmotionProvider
    
    registry.register("VectorDBProvider", QdrantProvider())
    registry.register("EmbeddingProvider", LocalEmbeddingProvider())
    registry.register("EmotionProvider", LocalTextEmotionProvider())
    
    # Start ARI WebSocket Client and AudioSocket server in the background
    ari_task = asyncio.create_task(ari_ws_client.connect())
    audio_task = asyncio.create_task(audio_server.start())
    
    yield
    
    # Graceful shutdown
    await ari_ws_client.disconnect()
    ari_task.cancel()
    audio_task.cancel()

app = FastAPI(
    title="Vensora API",
    description="Vensora Core Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# Register Correlation ID Middleware (Must be before CORS to ensure it runs first in response)
app.add_middleware(CorrelationIdMiddleware)

# Register Exception Handlers
setup_exception_handlers(app)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, use specific origins from settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
