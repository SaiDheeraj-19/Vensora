import pytest
import os

# Set required environment variables for tests globally during collection
os.environ["SECRET_KEY"] = "test_secret_key_1234567890"
os.environ["POSTGRES_USER"] = "test_user"
os.environ["POSTGRES_PASSWORD"] = "test_pass"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["MINIO_ROOT_USER"] = "test_minio_user"
os.environ["MINIO_ROOT_PASSWORD"] = "test_minio_pass"
