#!/bin/bash
# VEGAS IT GLOBAL - HRMS Restore Script
# Usage: ./scripts/restore.sh <backup_directory>
# Example: ./scripts/restore.sh /opt/backups/hrms/20240115_020000
# Run on the server at /opt/frappe_docker

set -euo pipefail

DEPLOY_PATH="/opt/frappe_docker"
SITE_NAME="hrms.cloudagents.uk"

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <backup_directory>"
  echo ""
  echo "Available backups:"
  ls -la /opt/backups/hrms/ 2>/dev/null || echo "  No backups found at /opt/backups/hrms/"
  exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Error: Backup directory not found: $BACKUP_DIR"
  exit 1
fi

echo "============================================"
echo "  VEGAS IT GLOBAL - HRMS Restore"
echo "  $(date)"
echo "============================================"
echo ""
echo "WARNING: This will restore the site from backup."
echo "Backup source: $BACKUP_DIR"
echo ""

# Find backup files
SQL_FILE=$(ls "$BACKUP_DIR"/*database*.sql.gz 2>/dev/null | head -1)
FILES_TAR=$(ls "$BACKUP_DIR"/*files*.tar 2>/dev/null | grep -v private | head -1)
PRIVATE_TAR=$(ls "$BACKUP_DIR"/*private-files*.tar 2>/dev/null | head -1)

if [ -z "$SQL_FILE" ]; then
  echo "Error: No database backup found in $BACKUP_DIR"
  exit 1
fi

echo "Files to restore:"
echo "  Database: $(basename "$SQL_FILE")"
[ -n "$FILES_TAR" ] && echo "  Public files: $(basename "$FILES_TAR")"
[ -n "$PRIVATE_TAR" ] && echo "  Private files: $(basename "$PRIVATE_TAR")"
echo ""

read -p "Continue with restore? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Restore cancelled."
  exit 0
fi

cd "$DEPLOY_PATH"

# Copy backup files into the container
echo "[1/4] Copying backup files to container..."
CONTAINER=$(docker compose -f docker-compose.prod.yml ps -q backend)
RESTORE_PATH="/home/frappe/frappe-bench/sites/$SITE_NAME/private/backups"

docker cp "$SQL_FILE" "$CONTAINER:$RESTORE_PATH/"
[ -n "$FILES_TAR" ] && docker cp "$FILES_TAR" "$CONTAINER:$RESTORE_PATH/"
[ -n "$PRIVATE_TAR" ] && docker cp "$PRIVATE_TAR" "$CONTAINER:$RESTORE_PATH/"

# Build restore command
SQL_BASENAME=$(basename "$SQL_FILE")
RESTORE_CMD="bench --site $SITE_NAME restore $RESTORE_PATH/$SQL_BASENAME"
[ -n "$FILES_TAR" ] && RESTORE_CMD="$RESTORE_CMD --with-public-files $RESTORE_PATH/$(basename "$FILES_TAR")"
[ -n "$PRIVATE_TAR" ] && RESTORE_CMD="$RESTORE_CMD --with-private-files $RESTORE_PATH/$(basename "$PRIVATE_TAR")"

# Put site in maintenance mode
echo "[2/4] Enabling maintenance mode..."
docker compose -f docker-compose.prod.yml exec -T backend \
  bench --site "$SITE_NAME" set-maintenance-mode on || true

# Run restore
echo "[3/4] Restoring from backup..."
docker compose -f docker-compose.prod.yml exec -T backend $RESTORE_CMD

# Disable maintenance mode and run migrate
echo "[4/4] Finalizing restore..."
docker compose -f docker-compose.prod.yml exec -T backend \
  bench --site "$SITE_NAME" migrate
docker compose -f docker-compose.prod.yml exec -T backend \
  bench --site "$SITE_NAME" set-maintenance-mode off

# Restart services
docker compose -f docker-compose.prod.yml restart

echo ""
echo "============================================"
echo "  Restore complete"
echo "  Site: https://$SITE_NAME"
echo "============================================"
