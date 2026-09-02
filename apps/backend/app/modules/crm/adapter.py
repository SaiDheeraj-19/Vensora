import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.modules.crm.models import CustomerProfile, Ticket, TicketStatus, TicketPriority
from sqlalchemy import desc

logger = logging.getLogger(__name__)

class CrmAdapter:
    """
    Interface for integrating with the external logistics company CRM and internal ticketing database.
    """
    def __init__(self):
        pass
        
    async def get_customer_by_phone(self, phone_number: str) -> Dict[str, Any] | None:
        """
        Lookup customer details based on caller ID.
        """
        db: Session = SessionLocal()
        try:
            customer = db.query(CustomerProfile).filter(CustomerProfile.phone_number == phone_number).first()
            if customer:
                return {
                    "customer_id": str(customer.id),
                    "phone_number": customer.phone_number,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "email": customer.email,
                }
            return None
        finally:
            db.close()
            
    async def get_shipment_status(self, tracking_number: str) -> Dict[str, Any] | None:
        """
        Lookup the real-time status of a shipment.
        """
        from app.modules.crm.models import Shipment
        db: Session = SessionLocal()
        try:
            shipment = db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
            if not shipment:
                return None
                
            return {
                "tracking_number": shipment.tracking_number,
                "status": shipment.status.value,
                "estimated_delivery": shipment.estimated_delivery,
                "current_location": shipment.current_location
            }
        except Exception as e:
            logger.error(f"Failed to lookup shipment {tracking_number}: {e}")
            return None
        finally:
            db.close()
        
    async def create_support_ticket(self, phone_number: str, issue_summary: str) -> Dict[str, Any]:
        """
        Create a new ticket in the internal database.
        Automatically creates a customer profile if one does not exist.
        """
        db: Session = SessionLocal()
        try:
            customer = db.query(CustomerProfile).filter(CustomerProfile.phone_number == phone_number).first()
            if not customer:
                logger.info(f"Creating new customer profile for {phone_number}")
                customer = CustomerProfile(phone_number=phone_number, metadata_tags={"source": "voice_ai"})
                db.add(customer)
                db.commit()
                db.refresh(customer)
            
            logger.info(f"Creating ticket for customer {customer.id}")
            ticket = Ticket(
                title=f"AI Support: {issue_summary[:50]}...",
                description=issue_summary,
                status=TicketStatus.OPEN,
                priority=TicketPriority.MEDIUM,
                customer_id=customer.id
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
            return {
                "ticket_id": str(ticket.id),
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "title": ticket.title
            }
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            db.rollback()
            return {"error": "Failed to create ticket in database"}
        finally:
            db.close()

    async def check_ticket_status(self, phone_number: str) -> List[Dict[str, Any]]:
        """
        Finds all active or recent tickets for a given phone number.
        """
        db: Session = SessionLocal()
        try:
            customer = db.query(CustomerProfile).filter(CustomerProfile.phone_number == phone_number).first()
            if not customer:
                return []
                
            tickets = db.query(Ticket).filter(
                Ticket.customer_id == customer.id
            ).order_by(desc(Ticket.status == TicketStatus.OPEN)).limit(5).all()
            
            results = []
            for t in tickets:
                results.append({
                    "ticket_id": str(t.id),
                    "title": t.title,
                    "status": t.status.value,
                    "description": t.description
                })
            return results
        finally:
            db.close()

crm_adapter = CrmAdapter()
