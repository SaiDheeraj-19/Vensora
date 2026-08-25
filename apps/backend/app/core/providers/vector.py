import logging
from abc import abstractmethod
from typing import List, Dict, Any
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class VectorDBProvider(BaseProvider):
    @abstractmethod
    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def ingest_chunks(self, chunks: List[str], vectors: List[List[float]]) -> bool:
        pass

class QdrantProvider(VectorDBProvider):
    """
    Qdrant implementation for RAG vector retrieval.
    """
    def __init__(self):
        self.settings = get_settings()
        self.collection_name = "vensora_knowledge"
        self.enabled = True
        
        try:
            from qdrant_client import QdrantClient
            self.client = QdrantClient(host=self.settings.QDRANT_HOST, port=self.settings.QDRANT_PORT)
            self._ensure_collection()
            logger.info("QdrantProvider initialized.")
        except ImportError:
            logger.warning("qdrant-client not installed. Vector DB running in MOCK mode.")
            self.client = None
            self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled or not self.client:
            return ProviderHealth(HealthState.MOCK, "qdrant-client missing")
        try:
            self.client.get_collections()
            return ProviderHealth(HealthState.HEALTHY)
        except Exception as e:
            return ProviderHealth(HealthState.UNAVAILABLE, str(e))

    def _ensure_collection(self):
        if not self.client:
            return
        try:
            from qdrant_client.models import Distance, VectorParams
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")

    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        if not self.enabled or not self.client:
            logger.info(f"MOCK: Returning empty search results for: '{query}'")
            return []
            
        try:
            from app.core.providers.registry import registry
            try:
                embedding_provider = registry.get("EmbeddingProvider")
            except ValueError:
                logger.error("EmbeddingProvider not found in registry")
                return []
                
            query_vector = embedding_provider.embed_texts([query])[0]
            
            logger.info(f"Searching Qdrant for: '{query}'")
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            return [{"text": hit.payload.get("text", ""), "score": hit.score} for hit in results]
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    def ingest_chunks(self, chunks: List[str], vectors: List[List[float]]) -> bool:
        if not self.enabled or not self.client:
            logger.info(f"MOCK: Ingested {len(chunks)} chunks")
            return True
        try:
            from qdrant_client.models import PointStruct
            import uuid
            
            points = []
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={"text": chunk}
                    )
                )
                
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant ingestion failed: {e}")
            return False
