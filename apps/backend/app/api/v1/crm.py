from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from sqlalchemy import desc
from app.database.session import get_db
from app.modules.crm.models import CustomerProfile

router = APIRouter()

@router.get("/contacts", response_model=List[Dict[str, Any]])
def get_contacts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    # Production-grade pagination and sorting
    customers = db.query(CustomerProfile).order_by(desc(CustomerProfile.id)).offset(skip).limit(limit).all()
    
    result = []
    for c in customers:
        name = f"{c.first_name or ''} {c.last_name or ''}".strip()
        result.append({
            "id": str(c.id),
            "phone_number": c.phone_number,
            "name": name or "Unknown",
            "metadata_tags": c.metadata_tags or {}
        })
        
    return result
