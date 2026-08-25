import logging
from datetime import datetime, timezone
from app.database.session import SessionLocal
from app.modules.calls.models import CallRecording
from app.modules.storage.minio_client import minio_client
from app.core.audit import log_audit_event

logger = logging.getLogger(__name__)

class RetentionService:
    """
    Background worker process to clean up expired recordings.
    Enforces compliance with 30-180 day retention limits.
    """
    
    def run_cleanup_job(self):
        """
        Queries for all recordings past their expiry date, deletes them from MinIO, 
        removes the DB record, and logs an audit trail.
        """
        logger.info("Starting Recording Retention Cleanup Job...")
        
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            expired_records = db.query(CallRecording).filter(CallRecording.retention_expiry_date < now).all()
            
            if not expired_records:
                logger.info("No expired recordings found.")
                return
                
            deleted_count = 0
            for record in expired_records:
                # 1. Delete physical file
                success = minio_client.delete_audio(record.storage_key)
                
                if success:
                    # 2. Delete DB record
                    db.delete(record)
                    
                    # 3. Create compliance audit log
                    log_audit_event(
                        action="RECORDING_DELETED_RETENTION",
                        resource_id=str(record.call_id),
                        changes={"storage_key": record.storage_key, "expired_on": record.retention_expiry_date.isoformat()}
                    )
                    deleted_count += 1
                    
            db.commit()
            logger.info(f"Retention Cleanup Complete. Deleted {deleted_count} recordings.")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Retention cleanup job failed: {e}")
        finally:
            db.close()

retention_service = RetentionService()
