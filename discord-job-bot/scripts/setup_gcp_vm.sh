#!/bin/bash
# ==============================================================================
# 100% FREE TIER GCP Bootstrap Script for Discord Job Bot
# Optimized for Google Compute Engine (e2-micro Always Free Tier)
# Tested on Ubuntu 22.04 LTS / Debian 11 on GCP Compute Engine
# ==============================================================================

set -e

echo "🚀 [1/6] Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git apt-transport-https ca-certificates gnupg lsb-release

echo "🧠 [2/6] Configuring 4GB Virtual Swap Memory for e2-micro ($0 Cost Optimization)..."
# e2-micro free tier has 1GB physical RAM. We configure a 4GB swapfile so
# Playwright Chromium and Discord background services run 24/7 without OOM kills.
if [ ! -f /swapfile ]; then
    echo "Creating 4GB swapfile..."
    sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    # Optimize swappiness for smooth background performance
    sudo sysctl vm.swappiness=20
    echo 'vm.swappiness=20' | sudo tee -a /etc/sysctl.conf
    echo "✅ 4GB Swap Space configured successfully."
else
    echo "Swapfile already exists. Skipping."
fi

echo "🐳 [3/6] Installing Docker & Docker Compose Plugin..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

sudo apt-get install -y docker-compose-plugin

echo "📁 [4/6] Setting up project directory..."
PROJECT_DIR="/opt/discord-job-bot"
sudo mkdir -p $PROJECT_DIR/data/resumes $PROJECT_DIR/data/screenshots
sudo chown -R $USER:$USER $PROJECT_DIR

echo "⚙️ [5/6] Creating Systemd Service for 24/7 Automatic Uptime..."
cat << 'EOF' | sudo tee /etc/systemd/system/discord-job-bot.service
[Unit]
Description=Discord Job Search & Easy Apply Bot (Docker)
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/discord-job-bot
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable discord-job-bot.service

echo "✅ [6/6] 100% Free GCP Setup Complete!"
echo "=========================================================================="
echo "Next Steps to Launch:"
echo "1. Place your bot files in: $PROJECT_DIR"
echo "2. Copy your .env configuration into: $PROJECT_DIR/.env"
echo "   (Make sure to set DISCORD_BOT_TOKEN and GEMINI_API_KEY)"
echo "3. Start the service with: sudo systemctl start discord-job-bot"
echo "4. View live logs with: sudo journalctl -u discord-job-bot -f"
echo "=========================================================================="
