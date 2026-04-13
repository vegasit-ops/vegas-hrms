#!/bin/bash
# VEGAS IT GLOBAL - HRMS Backup Script
# Usage: ./scripts/backup.sh [retention_days]
# Run on the server at /opt/frappe_docker

set -euo pipefail

DEPLOY_PATH="/opt/frappe_docker"
SITE_NAME="hrms.cloudagents.uk"
BACKUP_DIR="/opt/backups/hrms"
RETENTION_DAYS="${1:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEST="$BACKUP_DIR/$TIMESTAMP"

echo "============================================"
echo "  VEGAS IT GLOBAL - HRMS Backup"
echo "  $(date)"
echo "============================================"

# Create backup directory
mkdir -p "$DEST"

# Run bench backup with files
echo "[1/4] Running bench backup..."
cd "$DEPLOY_PATH"
docker compose -f docker-compose.prod.yml exec -T backend \
  bench --site "$SITE_NAME" backup --with-files

# Copy backups out of Docker volume
echo "[2/4] Copying backup files..."
CONTAINER=$(docker compose -f docker-compose.prod.yml ps -q backend)
SITE_PATH="/home/frappe/frappe-bench/sites/$SITE_NAME/private/backups"

LATEST_SQL=$(docker exec "$CONTAINER" ls -t "$SITE_PATH"/*database*.sql.gz 2>/dev/null | head -1)
LATEST_FILES=$(docker exec "$CONTAINER" ls -t "$SITE_PATH"/*files*.tar 2>/dev/null | head -1)
LATEST_PRIVATE=$(docker exec "$CONTAINER" ls -t "$SITE_PATH"/*private-files*.tar 2>/dev/null | head -1)

[ -n "$LATEST_SQL" ] && docker cp "$CONTAINER:$LATEST_SQL" "$DEST/"
[ -n "$LATEST_FILES" ] && docker cp "$CONTAINER:$LATEST_FILES" "$DEST/"
[ -n "$LATEST_PRIVATE" ] && docker cp "$CONTAINER:$LATEST_PRIVATE" "$DEST/"

echo "[3/4] Backup contents:"
ls -lh "$DEST/"

# Cleanup old backups
echo "[4/4] Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \;

echo ""
echo "Backup saved to: $DEST"
echo "Remaining backups:"
du -sh "$BACKUP_DIR"/*/
echo "============================================"
echo "  Backup complete"
echo "============================================"
