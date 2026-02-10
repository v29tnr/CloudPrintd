# CloudPrintd - Production-Ready Deployment Checklist

## ✅ Pre-Deployment Checklist

### System Requirements
- [ ] Raspberry Pi Zero 2 W or better (Pi 4 2GB+ recommended for production)
- [ ] 16GB+ microSD card (Class 10 or better)
- [ ] Stable power supply (5V 2.5A minimum)
- [ ] Network connectivity (WiFi or Ethernet)

### Software Prerequisites
- [ ] Raspberry Pi OS Lite installed and updated
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed (for frontend build)
- [ ] CUPS installed (for standard printers)
- [ ] Git installed

### Security
- [ ] Changed default user password
- [ ] Firewall configured (ufw)
- [ ] SSH key authentication enabled (optional but recommended)
- [ ] API tokens generated and stored securely
- [ ] IP whitelisting configured (if using Salesforce IP ranges)

### Network Configuration
- [ ] Static IP assigned (recommended for production)
- [ ] Connectivity method chosen:
  - [ ] Cloudflare Tunnel (recommended)
  - [ ] Tailscale VPN
  - [ ] Dynamic DNS
  - [ ] Static IP with port forwarding
- [ ] HTTPS certificate configured (via Cloudflare or Let's Encrypt)
- [ ] Firewall rules configured

---

## 🚀 Deployment Steps

### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-venv python3-pip cups libcups2-dev \
                    git curl build-essential nodejs npm

# Create cloudprintd user
sudo useradd -r -s /bin/bash -d /home/cloudprintd -m cloudprintd
```

### 2. Install CloudPrintd
```bash
# Create directories
sudo mkdir -p /opt/cloudprintd/packages
sudo mkdir -p /home/cloudprintd/{logs,data}

# Copy files
sudo cp -r /path/to/cloudprintd /opt/cloudprintd/packages/v1.0.0
cd /opt/cloudprintd/packages
sudo ln -s v1.0.0 current

# Set ownership
sudo chown -R cloudprintd:cloudprintd /opt/cloudprintd /home/cloudprintd
```

### 3. Install Python Dependencies
```bash
cd /opt/cloudprintd/packages/current
sudo -u cloudprintd python3 -m venv venv
sudo -u cloudprintd venv/bin/pip install -r requirements.txt
```

### 4. Build Frontend
```bash
cd /opt/cloudprintd/packages/current/webui
sudo -u cloudprintd npm install
sudo -u cloudprintd npm run build
```

### 5. Configure Service
```bash
# Install systemd service
sudo cp /opt/cloudprintd/packages/current/cloudprintd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cloudprintd
sudo systemctl start cloudprintd

# Verify
sudo systemctl status cloudprintd
```

### 6. Run Setup Wizard
Navigate to `http://your-pi-ip:8000/setup` and complete the 5-step wizard:
1. Welcome
2. Network connectivity
3. Printer discovery and configuration
4. API token generation
5. Complete setup

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Expected:
```json
{
  "status": "running",
  "version": "1.0.0",
  "uptime_seconds": 120,
  "printers_configured": 0,
  "printers_online": 0
}
```

### Test Print Job
```bash
curl -X POST http://localhost:8000/api/v1/print \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "printer": "test_printer",
    "content": "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ",
    "format": "zpl"
  }'
```

### Service Control (Web UI)
- Service Status: Dashboard → Service Control tab
- View Logs: Click "View Logs" button
- Restart: Click "Restart Service" button

### API Token Management (Web UI)
- Generate Token: Dashboard → API Keys tab → "Generate New Token"
- List Tokens: Dashboard → API Keys tab
- Delete Token: Dashboard → API Keys tab → Select token → "Delete"

---

## 🔒 Security Hardening

### System Level
```bash
# Enable firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # CloudPrintd
sudo ufw enable

# Disable unused services
sudo systemctl disable bluetooth
sudo systemctl disable hciuart

# Keep system updated
sudo apt update && sudo apt upgrade -y
```

### Application Level
- [ ] Rotate API tokens every 90 days
- [ ] Enable IP whitelisting for Salesforce IPs
- [ ] Use HTTPS (Cloudflare Tunnel or Let's Encrypt)
- [ ] Monitor logs regularly
- [ ] Set up log rotation

### Backups
```bash
# Backup configuration
sudo cp -r /opt/cloudprintd/config ~/backup-$(date +%Y%m%d)

# Automated backup script
cat > /usr/local/bin/backup-cloudprintd.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/pi/backups/cloudprintd-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp -r /opt/cloudprintd/config "$BACKUP_DIR/"
echo "Backup saved to $BACKUP_DIR"
EOF

sudo chmod +x /usr/local/bin/backup-cloudprintd.sh

# Schedule weekly backups
(crontab -l 2>/dev/null; echo "0 2 * * 0 /usr/local/bin/backup-cloudprintd.sh") | crontab -
```

---

## 📊 Monitoring

### Service Status
```bash
# Check service
sudo systemctl status cloudprintd

# View logs
sudo journalctl -u cloudprintd -f
tail -f /home/cloudprintd/logs/cloudprintd.log
```

### Resource Monitoring
```bash
# CPU/Memory
top
htop

# Disk usage
df -h

# Network
netstat -tlnp
```

### Web Dashboard
Access `http://your-ip:8000/` to monitor:
- System status and uptime
- Printer status
- Service control
- API token management
- Update status

---

## 🔄 Updates

### Via Web UI (Recommended)
1. Dashboard → Updates tab
2. Click "Check for Updates"
3. Review changelog
4. Click "Update" button
5. System automatically rolls back on failure

### Manual Update
```bash
cd /opt/cloudprintd/packages
sudo -u cloudprintd wget https://updates.yourdomain.com/cloudprintd-v1.1.0.pbpkg
sudo -u cloudprintd tar -xzf cloudprintd-v1.1.0.pbpkg
sudo rm current
sudo ln -s v1.1.0 current
sudo systemctl restart cloudprintd
```

---

## 🆘 Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u cloudprintd -n 100 --no-pager

# Check permissions
ls -la /opt/cloudprintd/packages/current
sudo chown -R cloudprintd:cloudprintd /opt/cloudprintd

# Test manually
sudo -u cloudprintd /opt/cloudprintd/packages/current/venv/bin/python \
  -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Printer Issues
```bash
# Test connectivity
ping 192.168.1.100

# Test ZPL port
nc -zv 192.168.1.100 9100

# Send test label
echo "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ" | nc 192.168.1.100 9100
```

### Memory Issues (Pi Zero 2 W)
```bash
# Increase swap
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Roll Back Update
Via Web UI:
1. Dashboard → Updates tab
2. Click "Rollback" button

Or manually:
```bash
sudo systemctl stop cloudprintd
cd /opt/cloudprintd/packages
sudo rm current
sudo ln -s v1.0.0 current  # Previous version
sudo systemctl start cloudprintd
```

---

## 📞 Support

### Documentation
- Setup Guide: `/docs/pi-zero-2w-setup.md`
- API Integration: `/docs/api-integration.md`
- Troubleshooting: `/docs/troubleshooting.md`
- Update Management: `/docs/update-management.md`

### Logs
- Service: `/home/cloudprintd/logs/cloudprintd.log`
- Errors: `/home/cloudprintd/logs/cloudprintd-error.log`
- System: `sudo journalctl -u cloudprintd`

### Quick Commands
```bash
# Service status
sudo systemctl status cloudprintd

# Restart service
sudo systemctl restart cloudprintd

# View live logs
sudo journalctl -u cloudprintd -f

# Check API health
curl http://localhost:8000/api/v1/health

# Check configuration
cat /opt/cloudprintd/config/config.json
```

---

## ✅ Post-Deployment Verification

### System Health
- [ ] Service running: `sudo systemctl status cloudprintd`
- [ ] Health endpoint responding: `curl http://localhost:8000/api/v1/health`
- [ ] Web interface accessible
- [ ] Dashboard showing correct status

### Printers
- [ ] All printers discovered/configured
- [ ] Test print successful on each printer
- [ ] Printer status showing "online"

### Salesforce Integration
- [ ] Named Credential configured
- [ ] Test API call successful from Salesforce
- [ ] Print job received and processed

### Monitoring
- [ ] Logs rotating properly
- [ ] No errors in logs
- [ ] Resource usage within limits
- [ ] Backups configured

---

## 🎉 You're Ready for Production!

CloudPrintd is now deployed and ready to handle print jobs from Salesforce. Monitor the dashboard and logs regularly, keep the system updated, and rotate API tokens periodically for optimal security.

**For support, refer to:**
- [Quick Reference Guide](QUICK-REFERENCE.md)
- [Complete Documentation](docs/)
- [Troubleshooting Guide](docs/troubleshooting.md)
