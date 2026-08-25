import logging
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_active_user, get_db
from app.modules.users.models import User
from app.modules.crm.models import KnowledgeDocument
from app.modules.ai.document_processor import document_processor
from app.modules.ai.embeddings import embeddings_service


logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document (TXT), parse it, chunk it, embed it, and index it into Qdrant.
    Requires knowledge:write permission (or admin).
    """
    # Permission check - assuming 'admin' or explicit 'knowledge:write' for now
    if current_user.role.name not in ["SUPER_ADMIN", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized to upload knowledge")

    if not file.filename.endswith(".txt"):
        # For Phase 1 we only support basic text without heavy PyMuPDF dependencies
        raise HTTPException(status_code=400, detail="Only .txt files are supported currently")

    content = await file.read()
    text = content.decode("utf-8")
    
    # 1. Save to Database
    doc_id = uuid.uuid4()
    db_doc = KnowledgeDocument(
        id=doc_id,
        title=file.filename,
        content=text,
        created_by=current_user.id
    )
    db.add(db_doc)
    db.commit()
    
    logger.info(f"Saved Document '{file.filename}' to DB (ID: {doc_id})")
    
    # 2. Chunking
    metadata = {"document_id": str(doc_id), "title": file.filename}
    chunks = document_processor.process_text(text, metadata)
    
    if not chunks:
        raise HTTPException(status_code=500, detail="Failed to chunk document")
        
    # 3. Embedding
    texts_to_embed = [c["text"] for c in chunks]
    vectors = embeddings_service.generate_embeddings(texts_to_embed)
    
    # 4. Ingestion
    from app.core.providers.registry import registry
    qdrant_provider = registry.get("VectorDBProvider")
    
    success = qdrant_provider.ingest_chunks(chunks, vectors)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to ingest chunks into vector database")
        
    return {
        "status": "success", 
        "document_id": str(doc_id), 
        "chunks_indexed": len(chunks)
    }
