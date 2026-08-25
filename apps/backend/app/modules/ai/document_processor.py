import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Parses and chunks uploaded documents for RAG ingestion.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_text(self, raw_text: str, source_metadata: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Splits raw text into manageable chunks using LangChain's RecursiveCharacterTextSplitter.
        """
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            logger.error("langchain-text-splitters not installed.")
            return []
            
        logger.info(f"Chunking document '{source_metadata.get('title', 'Unknown')}'")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        docs = text_splitter.create_documents([raw_text], metadatas=[source_metadata])
        
        # Convert Langchain Document objects to simple dicts
        chunks = []
        for i, doc in enumerate(docs):
            chunks.append({
                "chunk_id": f"{source_metadata.get('document_id')}_chunk_{i}",
                "text": doc.page_content,
                "metadata": doc.metadata
            })
            
        logger.info(f"Produced {len(chunks)} chunks.")
        return chunks

document_processor = DocumentProcessor()
