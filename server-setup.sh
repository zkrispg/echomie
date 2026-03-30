#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "  EchoMie Server Setup & Deploy"
echo "  Target: 39.101.68.238"
echo "========================================="

# 1. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[1/6] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "[1/6] Docker already installed, skipping..."
fi

# 2. Install Docker Compose plugin if needed
if ! docker compose version &> /dev/null; then
    echo "[2/6] Installing Docker Compose plugin..."
    apt-get update && apt-get install -y docker-compose-plugin
else
    echo "[2/6] Docker Compose already available, skipping..."
fi

# 3. Clone the repo
echo "[3/6] Cloning EchoMie repository..."
if [ -d /opt/echomie ]; then
    echo "  /opt/echomie already exists, pulling latest..."
    cd /opt/echomie
    git pull origin main
else
    git clone https://github.com/zkrispg/echomie.git /opt/echomie
    cd /opt/echomie
fi

# 4. Generate .env with secure random passwords
echo "[4/6] Generating secure .env configuration..."
if [ -f .env ]; then
    echo "  .env already exists, backing up to .env.bak"
    cp .env .env.bak
fi

cat > .env << ENVEOF
DB_USER=echomie
DB_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=')
DB_NAME=echomie
REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=')
JWT_SECRET_KEY=$(openssl rand -hex 32)
INTERNAL_TOKEN=$(openssl rand -hex 16)
APP_PORT=80
ENVEOF

echo "  .env created with secure random passwords"

# 5. Open firewall ports (BT Panel uses firewalld)
echo "[5/6] Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    echo "  Firewall ports 80/443 opened"
elif command -v ufw &> /dev/null; then
    ufw allow 80/tcp 2>/dev/null || true
    ufw allow 443/tcp 2>/dev/null || true
    echo "  UFW ports 80/443 opened"
else
    echo "  No firewall tool detected, skipping..."
fi

# 6. Build and start all services
echo "[6/6] Building and starting EchoMie (this may take 5-10 minutes)..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "========================================="
echo "  Checking service status..."
echo "========================================="
sleep 10
docker compose -f docker-compose.prod.yml ps

echo ""
echo "========================================="
echo "  DEPLOYMENT COMPLETE!"
echo ""
echo "  App URL: http://39.101.68.238"
echo ""
echo "  Useful commands:"
echo "    View logs:    cd /opt/echomie && docker compose -f docker-compose.prod.yml logs -f"
echo "    Restart:      cd /opt/echomie && docker compose -f docker-compose.prod.yml restart"
echo "    Stop:         cd /opt/echomie && docker compose -f docker-compose.prod.yml down"
echo "========================================="
