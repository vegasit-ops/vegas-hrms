#!/bin/bash
# VEGAS IT GLOBAL - HRMS Setup Script
# Run this after docker-compose is up

set -e

SITE_NAME="hrms.cloudagents.uk"
ADMIN_PASSWORD="VegasHR@2024Admin"
DB_ROOT_PASSWORD="${DB_PASSWORD:-V3gasHRMS2024Secure}"

echo "=== Creating Frappe Site ==="
docker compose -f docker-compose.prod.yml exec backend bench new-site $SITE_NAME \
  --mariadb-root-password $DB_ROOT_PASSWORD \
  --admin-password $ADMIN_PASSWORD \
  --install-app erpnext

echo "=== Installing HRMS ==="
docker compose -f docker-compose.prod.yml exec backend bench --site $SITE_NAME install-app hrms

echo "=== Setting Host Name ==="
docker compose -f docker-compose.prod.yml exec backend bench --site $SITE_NAME set-config host_name "https://$SITE_NAME"

echo "=== Setup Complete ==="
echo "Login: https://$SITE_NAME"
echo "User: Administrator"
echo "Password: $ADMIN_PASSWORD"
