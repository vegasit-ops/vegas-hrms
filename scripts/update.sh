#!/bin/bash
# VEGAS IT GLOBAL - HRMS Update Script
# Usage: ./scripts/update.sh [--skip-backup] [--skip-build]
# Run on the server at /opt/frappe_docker

set -euo pipefail

DEPLOY_PATH="/opt/frappe_docker"
SITE_NAME="hrms.cloudagents.uk"
IMAGE_TAG="vegas-hrms:v15"

SKIP_BACKUP=false
SKIP_BUILD=false

for arg in "$@"; do
  case $arg in
    --skip-backup) SKIP_BACKUP=true ;;
    --skip-build)  SKIP_BUILD=true ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

echo "============================================"
echo "  VEGAS IT GLOBAL - HRMS Update"
echo "  $(date)"
echo "============================================"

cd "$DEPLOY_PATH"

# Step 1: Backup
if [ "$SKIP_BACKUP" = false ]; then
  echo "[1/5] Running pre-update backup..."
  if [ -f scripts/backup.sh ]; then
    bash scripts/backup.sh
  else
    docker compose -f docker-compose.prod.yml exec -T backend \
      bench --site "$SITE_NAME" backup --with-files
  fi
else
  echo "[1/5] Skipping backup (--skip-backup)"
fi

# Step 2: Pull latest repo changes
echo "[2/5] Pulling latest configuration..."
if [ -d .git ]; then
  git pull origin main
fi

# Step 3: Rebuild image
if [ "$SKIP_BUILD" = false ]; then
  echo "[3/5] Rebuilding Docker image..."
  export APPS_JSON_BASE64=$(base64 -w 0 apps.json)
  docker build \
    --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
    --build-arg=FRAPPE_BRANCH=version-15 \
    --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
    --tag="$IMAGE_TAG" \
    --file=images/layered/Containerfile .
else
  echo "[3/5] Skipping image build (--skip-build)"
fi

# Step 4: Enable maintenance mode and migrate
echo "[4/5] Running migrations..."
docker compose -f docker-compose.prod.yml exec -T backend \
  bench --site "$SITE_NAME" set-maintenance-mode on || true

docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

echo "Waiting for services to start..."
sleep 30

docker compose -f docker-compose.prod.yml exec -T backend \
  bench --site "$SITE_NAME" migrate

docker compose -f docker-compose.prod.yml exec -T backend \
  bench --site "$SITE_NAME" set-maintenance-mode off

# Step 5: Health check
echo "[5/5] Running health check..."
for i in $(seq 1 10); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$SITE_NAME/api/method/ping" || true)
  if [ "$STATUS" = "200" ]; then
    echo "Health check passed - site is up"
    break
  fi
  echo "  Attempt $i/10 - Status: $STATUS"
  sleep 10
done

echo ""
echo "============================================"
echo "  Update complete"
echo "  Site: https://$SITE_NAME"
echo "============================================"
