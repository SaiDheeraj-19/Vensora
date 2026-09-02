import logging
import os
import io

logger = logging.getLogger(__name__)

class MinioClient:
    """
    S3-compatible client for storing raw call recordings.
    """
    def __init__(self):
        endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        if not endpoint.startswith("http"):
            endpoint = f"http://{endpoint}"
            
        self.endpoint = endpoint
        self.access_key = os.getenv("MINIO_ROOT_USER", "admin")
        self.secret_key = os.getenv("MINIO_ROOT_PASSWORD", "password")
        self.bucket_name = "vensora-recordings"
        self.enabled = True
        
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

    def _ensure_bucket(self):
        """Create the recording bucket if it doesn't exist."""
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except Exception:
            logger.info(f"Creating MinIO bucket: {self.bucket_name}")
            try:
                self.s3.create_bucket(Bucket=self.bucket_name)
            except Exception as e:
                logger.error(f"Failed to create bucket: {e}")

    def upload_audio(self, object_name: str, audio_data: bytes) -> bool:
        """Upload raw audio bytes to MinIO."""
        try:
            self.s3.upload_fileobj(io.BytesIO(audio_data), self.bucket_name, object_name)
            logger.info(f"Successfully uploaded {object_name} to MinIO")
            return True
        except Exception as e:
            logger.error(f"MinIO upload failed: {e}")
            return False

    def delete_audio(self, object_name: str) -> bool:
        """Delete an audio file from MinIO (used for retention cleanup)."""
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"Successfully deleted {object_name} from MinIO")
            return True
        except Exception as e:
            logger.error(f"MinIO deletion failed: {e}")
            return False

    def generate_presigned_url(self, object_name: str, expiration_seconds: int = 3600) -> str:
        """
        Generate a time-bound presigned URL for secure frontend audio playback.
        Does not expose the MinIO bucket publicly.
        """
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

minio_client = MinioClient()
