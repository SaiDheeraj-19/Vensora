from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from sqlalchemy import desc
from app.database.session import get_db
from app.modules.calls.models import Call

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_calls(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    # Production-grade pagination and database-level sorting
    calls = db.query(Call).order_by(desc(Call.end_time)).offset(skip).limit(limit).all()
    
    result = []
    for c in calls:
        caller_id = c.contact.phone_number if c.contact else "Unknown"
        
        result.append({
            "id": str(c.id),
            "caller_id": caller_id,
            "duration": c.duration_seconds or 0,
            "status": c.status,
            "timestamp": c.end_time.isoformat() if c.end_time else None,
            "recording_url": c.recording_url
        })
        
    return result
