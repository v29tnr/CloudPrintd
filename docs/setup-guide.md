# CloudPrintd Setup Guide

## 5-Minute Quickstart

### Prerequisites
- Raspberry Pi (Zero 2W or Pi 4) with Raspberry Pi OS Lite installed
- Network connectivity (Ethernet or WiFi)
- SSH access to the Pi

### Step 1: Initial Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv cups nodejs npm

# Create user and directories
sudo useradd -r -s /bin/bash -d /home/CloudPrintd CloudPrintd
sudo mkdir -p /opt/CloudPrintd/packages
sudo mkdir -p /home/CloudPrintd/{logs,data}
sudo chown -R CloudPrintd:CloudPrintd /opt/CloudPrintd /home/CloudPrintd

# Clone or copy CloudPrintd files
cd /opt/CloudPrintd
# ... (copy your files here)

# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Build Frontend

```bash
cd webui
npm install
npm run build
cd ..
```

### Step 3: Create Systemd Service

```bash
# Copy service file
sudo cp CloudPrintd.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable CloudPrintd
sudo systemctl start CloudPrintd

# Check status
sudo systemctl status CloudPrintd
```

### Step 4: Access Setup Wizard

1. Open your browser and navigate to `http://<raspberry-pi-ip>:8000/setup`
2. Follow the wizard steps:
   - Choose connectivity method
   - Discover and configure printers
   - Generate API token
   - Complete setup

### Step 5: Test Print

```bash
curl -X POST http://localhost:8000/api/v1/print \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "printer": "warehouse_zebra",
    "content": "^XA^FO50,50^A0N,50,50^FDTest Label^FS^XZ",
    "format": "zpl",
    "copies": 1
  }'
```

## Connectivity Options

### Option 1: Cloudflare Tunnel (Recommended)

**Advantages:**
- No port forwarding needed
- Free tier available
- Automatic HTTPS
- Easy setup

**Setup:**
1. Create a Cloudflare account
2. Install cloudflared on your Pi:
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb
```
3. Authenticate and create tunnel:
```bash
cloudflared tunnel login
cloudflared tunnel create CloudPrintd
```
4. Copy the tunnel token and paste it in the setup wizard

### Option 2: Tailscale VPN

**Advantages:**
- Secure mesh network
- No port forwarding
- Works across NATs
- Free for personal use

**Setup:**
1. Install Tailscale:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```
2. Authenticate:
```bash
sudo tailscale up
```
3. Get your Tailscale IP and use it in Salesforce

### Option 3: Dynamic DNS + Port Forwarding

**Advantages:**
- Direct connection
- Full control

**Setup:**
1. Register with a DDNS provider (No-IP, DuckDNS, etc.)
2. Install DDNS client on your Pi
3. Configure port forwarding on your router (port 8000 → Pi IP)
4. Use your DDNS hostname in Salesforce

### Option 4: Local Network Only

**For testing or if Salesforce is on the same network:**
- Use the Pi's local IP address directly
- No external connectivity setup needed

## WiFi Configuration

If your Pi doesn't have Ethernet:

```bash
# Edit wpa_supplicant configuration
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Add your network
network={
    ssid="Your_Network_Name"
    psk="Your_Password"
}

# Restart networking
sudo systemctl restart networking
```

## Firewall Configuration

If using UFW:

```bash
sudo apt install ufw
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 8000/tcp # CloudPrintd
sudo ufw enable
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u CloudPrintd -f

# Check Python errors
sudo systemctl status CloudPrintd
```

### Can't discover printers
- Ensure printers are on the same network
- Check firewall rules
- Verify printer IP addresses
- Try manually adding printer

### CUPS not working
```bash
# Install CUPS
sudo apt install cups

# Add user to lpadmin group
sudo usermod -a -G lpadmin CloudPrintd

# Restart CUPS
sudo systemctl restart cups
```

### Health check failing
```bash
# Test API directly
curl http://localhost:8000/api/v1/health

# Check if port is in use
sudo netstat -tlnp | grep 8000
```

## Production Recommendations

1. **Security:**
   - Enable IP whitelisting with Salesforce IP ranges
   - Use HTTPS (via Cloudflare Tunnel or reverse proxy)
   - Rotate API tokens regularly
   - Keep system updated

2. **Monitoring:**
   - Set up log monitoring
   - Configure health check alerts
   - Monitor printer status

3. **Backup:**
   - Backup configuration files regularly
   - Keep previous versions for rollback
   - Document printer configurations

4. **Performance:**
   - Use Raspberry Pi 4 for production
   - Monitor memory usage
   - Limit concurrent print jobs if needed

## Next Steps

- [API Integration Guide](api-integration.md) - Integrate with Salesforce
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Update Management](update-management.md) - Managing versions and updates
