#!/bin/bash
#
# CloudPrintd Automated Installation Script
# Run this on a fresh Raspberry Pi OS installation
#
# Usage: curl -sSL https://install.cloudprintd.com | bash
# Or: wget -qO- https://install.cloudprintd.com | bash
#

set -e

echo "======================================"
echo "CloudPrintd Automated Installer"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Please do not run as root/sudo"
    echo "Run as: bash install-cloudprintd.sh"
    exit 1
fi

# Check OS
if ! grep -q "Raspbian\|Debian" /etc/os-release; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi OS"
    echo "Other Linux distributions may work but are untested"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    cups \
    libcups2-dev \
    git \
    curl \
    build-essential

# Install Node.js
echo "📦 Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
else
    echo "Node.js already installed: $(node --version)"
fi

# Create cloudprintd user
echo "👤 Creating cloudprintd service user..."
if ! id "cloudprintd" &>/dev/null; then
    sudo useradd -r -s /bin/bash -m -d /home/cloudprintd cloudprintd
    sudo usermod -a -G lp,lpadmin cloudprintd
fi

# Install CloudPrintd
echo "⬇️  Installing CloudPrintd..."
if [ -d "/opt/cloudprintd" ]; then
    echo "Directory /opt/cloudprintd already exists. Backing up..."
    sudo mv /opt/cloudprintd "/opt/cloudprintd.backup.$(date +%Y%m%d-%H%M%S)"
fi

sudo mkdir -p /opt/cloudprintd
cd /opt

# Download latest release
echo "Downloading latest CloudPrintd release..."
LATEST_URL=$(curl -s https://api.github.com/repos/yourusername/cloudprintd/releases/latest | grep "tarball_url" | cut -d '"' -f 4)
sudo wget -O cloudprintd.tar.gz "$LATEST_URL"
sudo tar -xzf cloudprintd.tar.gz -C /opt/cloudprintd --strip-components=1
sudo rm cloudprintd.tar.gz

# Set ownership
sudo chown -R cloudprintd:cloudprintd /opt/cloudprintd

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
cd /opt/cloudprintd
sudo -u cloudprintd python3 -m venv venv
sudo -u cloudprintd ./venv/bin/pip install --upgrade pip
sudo -u cloudprintd ./venv/bin/pip install -r requirements.txt

# Build frontend
echo "⚛️  Building frontend..."
cd /opt/cloudprintd/webui
sudo -u cloudprintd npm install
sudo -u cloudprintd npm run build

# Create directories
echo "📁 Creating directories..."
sudo mkdir -p /home/cloudprintd/{logs,data,config,downloads}
sudo chown -R cloudprintd:cloudprintd /home/cloudprintd

# Install WiFi AP setup (optional)
read -p "Install WiFi AP setup mode for commercial products? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📡 Installing WiFi AP packages..."
    sudo apt install -y hostapd dnsmasq wireless-tools
    
    # Disable services (will be controlled by wifi-setup-check.sh)
    sudo systemctl unmask wpa_supplicant
    sudo systemctl disable hostapd
    sudo systemctl disable dnsmasq
    
    # Copy scripts
    sudo cp /opt/cloudprintd/scripts/wifi-setup-check.sh /usr/local/bin/
    sudo chmod +x /usr/local/bin/wifi-setup-check.sh
    
    # Install service
    sudo cp /opt/cloudprintd/systemd/cloudprintd-wifi-setup.service /etc/systemd/system/
    sudo systemctl enable cloudprintd-wifi-setup.service
    
    echo "✅ WiFi AP mode installed"
fi

# Setup sudoers
echo "🔐 Configuring permissions..."
sudo bash -c 'cat > /etc/sudoers.d/cloudprintd' << 'EOF'
# CloudPrintd service permissions
cloudprintd ALL=(ALL) NOPASSWD: /bin/systemctl restart cloudprintd
cloudprintd ALL=(ALL) NOPASSWD: /bin/systemctl stop cloudprintd
cloudprintd ALL=(ALL) NOPASSWD: /bin/systemctl start cloudprintd
cloudprintd ALL=(ALL) NOPASSWD: /usr/bin/cupsctl
cloudprintd ALL=(ALL) NOPASSWD: /usr/sbin/lpadmin
EOF
sudo chmod 440 /etc/sudoers.d/cloudprintd

# Install systemd service
echo "🔧 Installing CloudPrintd service..."
sudo cp /opt/cloudprintd/systemd/cloudprintd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cloudprintd.service

# Generate initial API token
echo "🔑 Generating initial API token..."
initial_token=$(openssl rand -hex 32)
sudo -u cloudprintd bash -c "echo 'INITIAL_TOKEN=cp-${initial_token}' > /opt/cloudprintd/.env"
sudo chmod 600 /opt/cloudprintd/.env

# Start service
echo "🚀 Starting CloudPrintd..."
sudo systemctl start cloudprintd

# Wait for service to start
sleep 3

# Check service status
if sudo systemctl is-active --quiet cloudprintd; then
    echo ""
    echo "======================================"
    echo "✅ CloudPrintd Installation Complete!"
    echo "======================================"
    echo ""
    echo "📍 Access Dashboard:"
    echo "   http://$(hostname).local:8000"
    echo "   http://$(hostname -I | awk '{print $1}'):8000"
    echo ""
    echo "🔑 Initial API Token:"
    echo "   cp-${initial_token}"
    echo ""
    echo "📖 Next Steps:"
    echo "   1. Open dashboard in browser"
    echo "   2. Run setup wizard"
    echo "   3. Add printers"
    echo "   4. Configure Salesforce integration"
    echo ""
    echo "📚 Documentation:"
    echo "   /opt/cloudprintd/docs/"
    echo ""
    echo "🔧 Service Management:"
    echo "   sudo systemctl status cloudprintd"
    echo "   sudo systemctl restart cloudprintd"
    echo "   sudo journalctl -u cloudprintd -f"
    echo ""
else
    echo ""
    echo "❌ CloudPrintd service failed to start"
    echo "Check logs: sudo journalctl -u cloudprintd -xe"
    exit 1
fi
