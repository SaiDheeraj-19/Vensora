from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.config import get_settings
from app.modules.crm.models import CustomerProfile
from app.modules.calls.models import Call
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.post("/seed")
def seed_database(db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="Forbidden: Database seeding is disabled in production environments.")
        
    # Check if we already seeded
    if db.query(CustomerProfile).first():
        return {"message": "Database already contains data!"}
        
    # Create some mock customers
    c1 = CustomerProfile(
        phone_number="+15550192834", 
        first_name="Jane", 
        last_name="Doe", 
        metadata_tags={"vip": True, "facts": ["Prefers morning calls", "Needs accessibility support"]}
    )
    c2 = CustomerProfile(
        phone_number="+15558881122", 
        first_name="Michael", 
        last_name="Smith", 
        metadata_tags={"vip": False, "facts": ["No active shipments"]}
    )
    
    db.add_all([c1, c2])
    db.commit()
    
    # Create some mock calls
    call1 = Call(
        contact_id=c1.id,
        status="AI Handled",
        duration_seconds=252,
        end_time=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    call2 = Call(
        contact_id=c2.id,
        status="Escalated",
        duration_seconds=65,
        end_time=datetime.now(timezone.utc) - timedelta(hours=4)
    )
    call3 = Call(
        contact_id=c1.id,
        status="AI Handled",
        duration_seconds=120,
        end_time=datetime.now(timezone.utc) - timedelta(days=1)
    )
    
    db.add_all([call1, call2, call3])
    db.commit()
    
    return {"message": "Database seeded with beautiful mock data!"}
