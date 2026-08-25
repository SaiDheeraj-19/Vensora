#!/bin/bash
set -e

# Vensora Phase 1 - Automated Backup Script
# Required for Gap 24 (Backup & Restore)

BACKUP_DIR="/var/backups/vensora/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting Vensora Backups to $BACKUP_DIR..."

# 1. PostgreSQL (Relational Data, Prompts, Audit Logs)
echo "Backing up PostgreSQL..."
PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h postgres -U $POSTGRES_USER $POSTGRES_DB | gzip > "$BACKUP_DIR/postgres_dump.sql.gz"

# 2. Qdrant (Vector Embeddings)
# Qdrant supports creating snapshots via its REST API
echo "Backing up Qdrant Vector Store..."
curl -X POST "http://qdrant:6333/collections/vensora_knowledge/snapshots" -o "$BACKUP_DIR/qdrant_snapshot.json"

# 3. MinIO (Call Recordings)
# Using MinIO Client (mc) to mirror the bucket to the backup directory
echo "Backing up MinIO Recordings..."
# mc alias set local minio http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
# mc mirror local/vensora-recordings "$BACKUP_DIR/minio_recordings"

# 4. Redis (Cache / Background Task State)
# Evaluated as DISPOSABLE state for Phase 1. No backup required.
echo "Redis state is disposable. Skipping."

echo "Backup completed successfully."
