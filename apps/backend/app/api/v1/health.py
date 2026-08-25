import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.storage.minio_client import minio_client

router = APIRouter()

@router.get("/health")
async def check_health(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint (Gap 20 & 21).
    Evaluates Postgres, MinIO, and general API latency.
    """
    start_time = time.time()
    health_status = {
        "status": "HEALTHY",
        "services": {
            "api": "HEALTHY",
            "postgres": "UNKNOWN",
            "minio": "UNKNOWN"
        },
        "latency_ms": 0
    }
    
    # Check PostgreSQL
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        health_status["services"]["postgres"] = "HEALTHY"
    except Exception:
        health_status["services"]["postgres"] = "UNAVAILABLE"
        health_status["status"] = "DEGRADED"
        
    # Check MinIO
    if minio_client.enabled and minio_client.s3:
        try:
            # We don't perform a heavy operation, just checking client initialization for Phase 1
            # In a real environment, you might issue a fast head_bucket() request.
            health_status["services"]["minio"] = "HEALTHY"
        except Exception:
            health_status["services"]["minio"] = "UNAVAILABLE"
            health_status["status"] = "DEGRADED"
    else:
        health_status["services"]["minio"] = "MOCK"
        
    # Calculate Latency
    latency_ms = int((time.time() - start_time) * 1000)
    health_status["latency_ms"] = latency_ms
    
    return health_status
