import logging
import os
import io
from abc import abstractmethod
from typing import Optional
from app.core.providers.base import BaseProvider, ProviderHealth, HealthState
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class ObjectStorageProvider(BaseProvider):
    @abstractmethod
    def upload_audio(self, object_name: str, audio_data: bytes) -> bool:
        pass
        
    @abstractmethod
    def delete_audio(self, object_name: str) -> bool:
        pass
        
    @abstractmethod
    def generate_presigned_url(self, object_name: str, expiration_seconds: int = 3600) -> str:
        pass

class MinIOProvider(ObjectStorageProvider):
    """
    S3-compatible client for storing raw call recordings.
    """
    def __init__(self):
        self.settings = get_settings()
        self.endpoint = os.getenv("MINIO_ENDPOINT", f"http://{self.settings.MINIO_HOST}:{self.settings.MINIO_PORT}")
        self.access_key = self.settings.MINIO_ROOT_USER
        self.secret_key = self.settings.MINIO_ROOT_PASSWORD
        self.bucket_name = "vensora-recordings"
        self.enabled = True
        
        try:
            import boto3
            from botocore.client import Config
            self.s3 = boto3.client(
                's3',
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                config=Config(signature_version='s3v4')
            )
            self._ensure_bucket()
            logger.info("MinIOProvider initialized.")
        except ImportError:
            logger.warning("boto3 not installed. Storage running in MOCK mode.")
            self.s3 = None
            self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    async def check_health(self) -> ProviderHealth:
        if not self.enabled or not self.s3:
            return ProviderHealth(HealthState.MOCK, "boto3 missing or disabled")
        try:
            # A fast metadata check to ensure connectivity
            self.s3.head_bucket(Bucket=self.bucket_name)
            return ProviderHealth(HealthState.HEALTHY)
        except Exception as e:
            return ProviderHealth(HealthState.UNAVAILABLE, str(e))

    def _ensure_bucket(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except Exception:
            logger.info(f"Creating MinIO bucket: {self.bucket_name}")
            try:
                self.s3.create_bucket(Bucket=self.bucket_name)
            except Exception as e:
                logger.error(f"Failed to create bucket: {e}")

    def upload_audio(self, object_name: str, audio_data: bytes) -> bool:
        if not self.enabled or not self.s3:
            logger.info(f"MOCK: Uploaded {len(audio_data)} bytes to {object_name}")
            return True
        try:
            self.s3.upload_fileobj(io.BytesIO(audio_data), self.bucket_name, object_name)
            return True
        except Exception as e:
            logger.error(f"MinIO upload failed: {e}")
            return False

    def delete_audio(self, object_name: str) -> bool:
        if not self.enabled or not self.s3:
            return True
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except Exception as e:
            logger.error(f"MinIO deletion failed: {e}")
            return False

    def generate_presigned_url(self, object_name: str, expiration_seconds: int = 3600) -> str:
        if not self.enabled or not self.s3:
            return f"http://mock-storage/{self.bucket_name}/{object_name}"
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration_seconds
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return ""
