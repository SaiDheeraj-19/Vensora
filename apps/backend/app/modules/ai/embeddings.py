import logging
from typing import List
import time

logger = logging.getLogger(__name__)

_MODEL_INITIALIZED = False
_EMBEDDING_MODEL = None

class EmbeddingsService:
    """
    Local embeddings generator using sentence-transformers.
    Defaults to bge-small-en-v1.5 for fast CPU ingestion.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name

    def _initialize_model(self):
        global _MODEL_INITIALIZED, _EMBEDDING_MODEL
        if not _MODEL_INITIALIZED:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                # We use CPU by default for the phase 1 local setup unless torch detects otherwise
                _EMBEDDING_MODEL = SentenceTransformer(self.model_name)
                _MODEL_INITIALIZED = True
            except ImportError:
                logger.warning("sentence-transformers not installed. Running embeddings in MOCK mode.")
                _MODEL_INITIALIZED = True
                _EMBEDDING_MODEL = None

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate dense vector embeddings for a list of text chunks.
        """
        if not texts:
            return []
            
        self._initialize_model()
        
        start_time = time.time()
        
        if not _EMBEDDING_MODEL:
            # Mock mode returns dummy vectors (length 384 for bge-small)
            latency = time.time() - start_time
            logger.debug(f"Mock embedded {len(texts)} chunks in {latency:.3f}s")
            return [[0.1] * 384 for _ in texts]
            
        embeddings = _EMBEDDING_MODEL.encode(texts, normalize_embeddings=True)
        latency = time.time() - start_time
        logger.info(f"Embedded {len(texts)} chunks in {latency:.3f}s")
        
        return embeddings.tolist()

embeddings_service = EmbeddingsService()
