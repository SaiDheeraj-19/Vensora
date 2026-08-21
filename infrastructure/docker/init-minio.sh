#!/bin/sh

# Wait for MinIO to be available
sleep 3

echo "Configuring MinIO client..."
mc alias set myminio http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

echo "Creating buckets..."
mc mb myminio/vensora-documents --ignore-existing
mc mb myminio/vensora-recordings --ignore-existing

echo "Buckets created successfully."
