from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from sqlalchemy import desc
from app.database.session import get_db
from app.modules.crm.models import CustomerProfile, Ticket

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

@router.get("/tickets", response_model=List[Dict[str, Any]])
def get_tickets(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    # Join with CustomerProfile to get phone number
    tickets = db.query(Ticket).order_by(desc(Ticket.id)).offset(skip).limit(limit).all()
    
    result = []
    for t in tickets:
        result.append({
            "id": str(t.id),
            "title": t.title,
            "description": t.description,
            "status": t.status.value,
            "priority": t.priority.value,
            "customer_id": str(t.customer_id),
            "customer_phone": t.customer.phone_number if t.customer else "Unknown"
        })
        
    return result
