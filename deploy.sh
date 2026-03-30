#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# EchoMie One-Click Deploy Script
# Usage: bash deploy.sh
# ============================================================

echo "========================================="
echo "  EchoMie Deployment"
echo "========================================="

# Check .env exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo "  Copy the template:  cp .env.production .env"
    echo "  Then edit it with real passwords/secrets."
    exit 1
fi

# Validate critical env vars
source .env
for var in DB_PASSWORD REDIS_PASSWORD JWT_SECRET_KEY INTERNAL_TOKEN; do
    val="${!var:-}"
    if [ -z "$val" ] || [[ "$val" == CHANGE_ME* ]]; then
        echo "[ERROR] $var is not set or still has placeholder value."
        echo "  Edit .env and set a real value."
        exit 1
    fi
done

echo "[1/4] Building Docker images..."
docker compose -f docker-compose.prod.yml build

echo "[2/4] Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo "[3/4] Waiting for services to be healthy..."
sleep 10

echo "[4/4] Checking service status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "========================================="
echo "  Deployment complete!"
echo "  App: http://$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'YOUR_SERVER_IP'):${APP_PORT:-80}"
echo "========================================="
