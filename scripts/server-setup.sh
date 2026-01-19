#!/bin/bash

# ============================================================
# Army Memo Maker - DigitalOcean Server Setup Script
# Run this ONCE on a fresh Ubuntu droplet
# ============================================================

set -e

echo "=========================================="
echo "Army Memo Maker - Server Setup"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./server-setup.sh)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose (v2 comes with Docker now)
echo "🐳 Verifying Docker Compose..."
docker compose version

# Install useful tools
echo "🔧 Installing useful tools..."
apt-get install -y git curl htop

# Create project directory
echo "📁 Setting up project directory..."
mkdir -p /root/armymarkdown
cd /root/armymarkdown

# Clone repository (if not already cloned)
if [ ! -d ".git" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/jschless/armymarkdown.git .
else
    echo "✅ Repository already exists"
    git pull origin main
fi

# Create .env file template
echo "📝 Creating .env file template..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Flask Configuration
FLASK_SECRET=CHANGE_ME_TO_A_RANDOM_STRING

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY

# ReCAPTCHA Configuration (get from Google reCAPTCHA admin)
RECAPTCHA_PUBLIC_KEY=YOUR_RECAPTCHA_PUBLIC_KEY
RECAPTCHA_PRIVATE_KEY=YOUR_RECAPTCHA_PRIVATE_KEY

# Optional: Slack notifications for Watchtower
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx
EOF
    echo ""
    echo "⚠️  IMPORTANT: Edit /root/armymarkdown/.env with your actual secrets!"
    echo "   Run: nano /root/armymarkdown/.env"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Set up firewall
echo "🔒 Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo "✅ Firewall configured"

# Create systemd service for auto-start on reboot
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/armymarkdown.service << 'EOF'
[Unit]
Description=Army Memo Maker
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/root/armymarkdown
ExecStart=/usr/bin/docker compose -f infrastructure/compose/docker-compose-production.yaml up -d
ExecStop=/usr/bin/docker compose -f infrastructure/compose/docker-compose-production.yaml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable armymarkdown
echo "✅ Systemd service created"

echo ""
echo "=========================================="
echo "✅ Server setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your secrets:"
echo "   nano /root/armymarkdown/.env"
echo ""
echo "2. Start the application:"
echo "   cd /root/armymarkdown"
echo "   docker compose -f infrastructure/compose/docker-compose-production.yaml up -d"
echo ""
echo "3. Check status:"
echo "   docker compose -f infrastructure/compose/docker-compose-production.yaml ps"
echo "   docker compose -f infrastructure/compose/docker-compose-production.yaml logs -f"
echo ""
echo "4. Caddy will automatically get SSL certificates for armymemomaker.com"
echo "   (Make sure DNS points to this server's IP)"
echo ""
