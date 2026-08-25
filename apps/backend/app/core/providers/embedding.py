import logging
import time
from abc import abstractmethod
from typing import List
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState

logger = logging.getLogger(__name__)

class EmbeddingProvider(BaseProvider):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local Embedding provider using sentence-transformers.
    Model: BAAI/bge-small-en-v1.5 (documented in ADR-001).
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self._model = None
        self._initialized = False
        self.enabled = True
        
        try:
            import sentence_transformers
            # We lazy load the model to prevent blocking startup
        except ImportError:
            logger.warning("sentence-transformers not installed. Embeddings running in MOCK mode.")
            self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled:
            return ProviderHealth(HealthState.MOCK, "sentence-transformers missing")
        # Local models are always healthy once initialized
        return ProviderHealth(HealthState.HEALTHY)

    def _initialize(self):
        if not self._initialized and self.enabled:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.enabled = False

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        start_time = time.time()
        
        if not self.enabled:
            # Return dummy vectors of size 384 (BGE-small dimension)
            latency = time.time() - start_time
            logger.info(f"MOCK Embeddings Latency: {latency:.3f}s for {len(texts)} texts")
            return [[0.0] * 384 for _ in texts]
            
        self._initialize()
        
        try:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            latency = time.time() - start_time
            logger.info(f"Generated embeddings for {len(texts)} texts in {latency:.3f}s")
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
