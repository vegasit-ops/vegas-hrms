# VEGAS IT GLOBAL - HRMS

Human Resource Management System for VEGAS IT GLOBAL (VIG), built on Frappe HRMS v15.

**Live URL:** https://hrms.cloudagents.uk

## Stack

| Component      | Version     |
|----------------|-------------|
| Frappe Framework | v15       |
| ERPNext        | v15         |
| Frappe HRMS    | v15         |
| MariaDB        | 11.8        |
| Redis          | 6.2         |
| Docker Compose | Production  |
| Nginx          | Host reverse proxy with SSL (certbot) |

## Infrastructure

- **Server:** DigitalOcean Droplet at `159.65.23.84`
- **Domain:** `hrms.cloudagents.uk`
- **Docker path:** `/opt/frappe_docker`
- **Nginx:** Host-level reverse proxy (port 80/443 -> 8080)
- **SSL:** Let's Encrypt via certbot (auto-renewed)
- **Company:** VEGAS IT GLOBAL, Currency: INR, Country: India

## Architecture

```
Internet -> Nginx (host, 443/SSL) -> Docker frontend (8080)
                                       |-> backend (Gunicorn)
                                       |-> websocket (Socket.IO)
                                       |-> scheduler
                                       |-> queue-short
                                       |-> queue-long
                                       |-> MariaDB 11.8
                                       |-> Redis cache
                                       |-> Redis queue
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Domain DNS pointing to the server IP
- SSH access to the server

### Initial Deployment

1. Clone this repository on the server:
   ```bash
   cd /opt
   git clone https://github.com/vegasit-ops/vegas-hrms.git frappe_docker
   cd frappe_docker
   ```

2. Copy and configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with secure passwords
   ```

3. Build the Docker image:
   ```bash
   export APPS_JSON_BASE64=$(base64 -w 0 apps.json)
   docker build \
     --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
     --build-arg=FRAPPE_BRANCH=version-15 \
     --build-arg=APPS_JSON_BASE64=$APPS_JSON_BASE64 \
     --tag=vegas-hrms:v15 \
     --file=images/layered/Containerfile .
   ```

4. Start the stack:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

5. Create the site:
   ```bash
   bash setup.sh
   ```

6. Set up Nginx and SSL:
   ```bash
   cp nginx/hrms.conf /etc/nginx/sites-available/
   ln -s /etc/nginx/sites-available/hrms.conf /etc/nginx/sites-enabled/
   certbot --nginx -d hrms.cloudagents.uk
   systemctl reload nginx
   ```

## Operations

### Update / Upgrade

Run the update script on the server:

```bash
cd /opt/frappe_docker
bash scripts/update.sh
```

Options:
- `--skip-backup` - Skip pre-update backup
- `--skip-build` - Skip Docker image rebuild (config-only changes)

### Backup

Manual backup:

```bash
bash scripts/backup.sh [retention_days]
```

Backups are also taken automatically every day at 2 AM UTC via the GitHub Actions workflow.

Backups are stored at `/opt/backups/hrms/` on the server with 7-day retention.

### Restore

```bash
bash scripts/restore.sh /opt/backups/hrms/20240115_020000
```

This will:
1. Enable maintenance mode
2. Restore database and files from the backup
3. Run migrations
4. Disable maintenance mode and restart

## CI/CD

Automated deployment via GitHub Actions:

- **Deploy** (`.github/workflows/deploy.yml`): Triggers on push to `main`. Copies files, rebuilds image if `apps.json` changed, runs migrations, restarts services, and verifies health.
- **Backup** (`.github/workflows/backup.yml`): Runs daily at 2 AM UTC. Creates full backup with files and cleans up backups older than 7 days.

### Required GitHub Secrets

| Secret           | Description                        |
|------------------|------------------------------------|
| `DROPLET_SSH_KEY` | Private SSH key for server access  |
| `DROPLET_IP`      | Server IP (`159.65.23.84`)        |

## File Structure

```
vegas-hrms/
  apps.json                    # Frappe apps to install (ERPNext + HRMS)
  docker-compose.prod.yml      # Production Docker Compose stack
  setup.sh                     # Initial site creation script
  .env.example                 # Environment variable template
  .github/
    workflows/
      deploy.yml               # CI/CD deploy pipeline
      backup.yml               # Scheduled backup workflow
  scripts/
    backup.sh                  # Manual backup script
    restore.sh                 # Restore from backup
    update.sh                  # Update/upgrade script
  nginx/
    hrms.conf                  # Host Nginx reverse proxy config
```

## Troubleshooting

### View logs

```bash
cd /opt/frappe_docker
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Access bench console

```bash
docker compose -f docker-compose.prod.yml exec backend bench --site hrms.cloudagents.uk console
```

### Restart all services

```bash
docker compose -f docker-compose.prod.yml restart
```

### Rebuild from scratch

```bash
docker compose -f docker-compose.prod.yml down -v
# WARNING: -v removes volumes (data loss). Only use for fresh start.
```
