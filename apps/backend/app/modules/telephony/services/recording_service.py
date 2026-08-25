import logging
import uuid
from datetime import datetime, timezone, timedelta
from app.modules.storage.minio_client import minio_client
from app.database.session import SessionLocal
from app.modules.calls.models import CallRecording
from app.core.audit import log_audit_event

logger = logging.getLogger(__name__)

class RecordingService:
    def __init__(self, default_retention_days: int = None):
        # Configurable retention per company policy (30, 60, 90, 180)
        from app.config.settings import get_settings
        self.retention_days = default_retention_days or get_settings().RECORDING_RETENTION_DAYS
        
    def save_recording(self, call_id: str, raw_audio_bytes: bytes, duration_seconds: int):
        """
        Uploads the final call audio to MinIO and records metadata in PostgreSQL.
        """
        try:
            # 1. Generate unique storage key
            storage_key = f"recordings/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{call_id}.wav"
            
            # 2. Upload to MinIO
            success = minio_client.upload_audio(storage_key, raw_audio_bytes)
            if not success:
                logger.error(f"Failed to upload recording for call {call_id}")
                return
                
            # 3. Save to DB with retention expiry
            db = SessionLocal()
            expiry_date = datetime.now(timezone.utc) + timedelta(days=self.retention_days)
            
            record = CallRecording(
                call_id=uuid.UUID(call_id),
                storage_key=storage_key,
                format="wav",
                duration_seconds=duration_seconds,
                retention_expiry_date=expiry_date
            )
            
            db.add(record)
            db.commit()
            db.close()
            
            logger.info(f"Successfully saved recording metadata for {call_id}. Expires: {expiry_date.date()}")
            
            # 4. Audit Log
            log_audit_event(
                action="RECORDING_SAVED",
                resource_id=call_id,
                changes={"storage_key": storage_key, "retention_days": self.retention_days}
            )
            
        except Exception as e:
            logger.error(f"Failed to process recording for {call_id}: {e}")

recording_service = RecordingService()
