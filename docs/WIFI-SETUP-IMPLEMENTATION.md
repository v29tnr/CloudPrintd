# WiFi Setup Feature - Implementation Guide

## Overview

This guide explains how to implement the WiFi Access Point setup mode for CloudPrintd, enabling end users to configure their WiFi network through a captive portal without command-line access.

**Perfect for:** Commercial hardware products (preconfigured Raspberry Pi boards)

---

## Architecture

### How It Works

1. **First Boot:** Pi checks if WiFi is configured
2. **No WiFi?** → Enters **AP Mode**:
   - Creates WiFi hotspot: `CloudPrintd-SETUP-XXXX`
   - Starts web server at `192.168.4.1:8000`
   - User connects phone/laptop to hotspot
   - Captive portal opens automatically
   - User selects WiFi network and enters password
   - Pi reboots and connects to user's network
3. **WiFi Configured?** → **Normal Mode**:
   - Connects to configured network
   - Accessible at `cloudprintd.local:8000`

### Components

- **Backend:** `/app/routers/network.py` - Network configuration API
- **Frontend:** `/webui/src/components/NetworkSetup.jsx` - WiFi setup UI
- **Boot Script:** `/scripts/wifi-setup-check.sh` - AP mode detection
- **Service:** `/systemd/cloudprintd-wifi-setup.service` - Systemd service

---

## Installation Steps

### 1. Install Required Packages

```bash
sudo apt update
sudo apt install -y hostapd dnsmasq wireless-tools
```

**Package roles:**
- `hostapd` - Creates WiFi access point
- `dnsmasq` - DHCP server + DNS (for captive portal)
- `wireless-tools` - WiFi utilities (iwconfig, iwlist)

### 2. Configure hostapd

```bash
sudo nano /etc/default/hostapd
```

Add this line:
```bash
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

**Note:** The actual config is generated dynamically by `wifi-setup-check.sh`

### 3. Configure dnsmasq

Disable default dnsmasq config:
```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```

**Note:** CloudPrintd creates `/etc/dnsmasq.d/cloudprintd-ap.conf` dynamically

### 4. Prevent Auto-Start

We only want these services running in AP mode:
```bash
sudo systemctl unmask wpa_supplicant
sudo systemctl disable hostapd
sudo systemctl disable dnsmasq
```

### 5. Install WiFi Setup Script

```bash
sudo cp scripts/wifi-setup-check.sh /opt/cloudprintd/scripts/
sudo chmod +x /opt/cloudprintd/scripts/wifi-setup-check.sh
```

### 6. Install WiFi Setup Service

```bash
sudo cp systemd/cloudprintd-wifi-setup.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cloudprintd-wifi-setup.service
```

This service runs on boot and decides: AP mode or normal mode?

### 7. Grant Permissions

The CloudPrintd service needs sudo access to manage networking:

```bash
sudo visudo -f /etc/sudoers.d/cloudprintd
```

Add:
```
# CloudPrintd network management
cloudprintd ALL=(ALL) NOPASSWD: /bin/systemctl start hostapd
cloudprintd ALL=(ALL) NOPASSWD: /bin/systemctl stop hostapd
cloudprintd ALL=(ALL) NOPASSWD: /bin/systemctl start dnsmasq
cloudprintd ALL=(ALL) NOPASSWD: /bin/systemctl stop dnsmasq
cloudprintd ALL=(ALL) NOPASSWD: /usr/sbin/wpa_cli *
cloudprintd ALL=(ALL) NOPASSWD: /usr/sbin/iwlist wlan0 scan
cloudprintd ALL=(ALL) NOPASSWD: /bin/cp /tmp/wpa_supplicant.conf* /etc/wpa_supplicant/*
cloudprintd ALL=(ALL) NOPASSWD: /bin/mv /tmp/wpa_supplicant.conf* /etc/wpa_supplicant/*
cloudprintd ALL=(ALL) NOPASSWD: /bin/chmod 600 /etc/wpa_supplicant/wpa_supplicant.conf
cloudprintd ALL=(ALL) NOPASSWD: /sbin/shutdown -r *
cloudprintd ALL=(ALL) NOPASSWD: /sbin/hostnamectl set-hostname *
cloudprintd ALL=(ALL) NOPASSWD: /bin/mv /tmp/hostname /etc/hostname
cloudprintd ALL=(ALL) NOPASSWD: /bin/mv /tmp/hosts /etc/hosts
```

**Security note:** These commands are restricted to specific paths and the CloudPrintd user only.

### 8. Build Frontend

The NetworkSetup component is now part of the Dashboard:

```bash
cd webui
npm install
npm run build
```

### 9. Deploy

Copy built files to server:
```bash
sudo cp -r dist/* /opt/cloudprintd/packages/current/webui/dist/
```

### 10. Restart Services

```bash
sudo systemctl restart cloudprintd-wifi-setup
sudo systemctl restart cloudprintd
```

---

## Testing

### Test AP Mode

1. Clear WiFi configuration:
```bash
sudo bash -c 'cat > /etc/wpa_supplicant/wpa_supplicant.conf' << 'EOF'
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

EOF
```

2. Reboot:
```bash
sudo reboot
```

3. After boot, check for WiFi network named `CloudPrintd-SETUP-XXXX`

4. Connect using password: `cloudprintd`

5. Browser should auto-open captive portal, or navigate to: `http://192.168.4.1:8000`

6. Click "Network" tab in Dashboard

7. Scan for networks, select yours, enter password, click Connect

8. Pi reboots and connects to your network

### Test Normal Mode

After connecting WiFi, check:

1. Find Pi on your network:
```bash
ping cloudprintd.local
```

2. Access dashboard:
```
http://cloudprintd.local:8000
```

3. Go to Network tab → verify connection status shows your WiFi

### Test WiFi Reset

1. In Dashboard → Network tab
2. Click "Reset WiFi Settings"
3. Confirm
4. Pi reboots to AP mode
5. Start from step 3 of AP mode test

---

## Troubleshooting

### Pi doesn't create AP

**Check logs:**
```bash
sudo journalctl -u cloudprintd-wifi-setup -f
cat /var/log/cloudprintd-wifi-setup.log
```

**Check hostapd status:**
```bash
sudo systemctl status hostapd
```

**Common issues:**
- WiFi already configured (check `/etc/wpa_supplicant/wpa_supplicant.conf`)
- hostapd not installed
- Permission issues (check sudoers)

### Can't connect to AP

**Check if AP is active:**
```bash
iwconfig wlan0
# Should show: Mode:Master (not Mode:Managed)
```

**Check hostapd:**
```bash
sudo systemctl status hostapd
sudo hostapd /etc/hostapd/hostapd.conf
# Run in foreground to see errors
```

**Check dnsmasq:**
```bash
sudo systemctl status dnsmasq
sudo dnsmasq --test
```

### Captive portal doesn't open

**Check iptables:**
```bash
sudo iptables -t nat -L PREROUTING
# Should see REDIRECT rules for ports 80/443 → 8000
```

**Check CloudPrintd is running:**
```bash
sudo systemctl status cloudprintd
curl http://192.168.4.1:8000/api/v1/health
```

**Manual access:**
- Open browser
- Navigate to `http://192.168.4.1:8000`
- Click "Network" tab

### WiFi won't connect after configuration

**Check wpa_supplicant.conf:**
```bash
sudo cat /etc/wpa_supplicant/wpa_supplicant.conf
# Should have your network with correct SSID/password
```

**Test WiFi manually:**
```bash
sudo wpa_cli -i wlan0 reconfigure
sudo wpa_cli -i wlan0 status
```

**Check WiFi signal:**
```bash
sudo iwlist wlan0 scan | grep -A 5 "Your SSID"
```

### Network scan returns no results

**Check WiFi interface:**
```bash
ip link show wlan0
# Should be UP
```

**Try manual scan:**
```bash
sudo iwlist wlan0 scan
```

**Check rfkill:**
```bash
rfkill list
# WiFi should not be blocked
```

If blocked:
```bash
sudo rfkill unblock wifi
```

---

## Production Image Creation

### Custom Image Setup

For selling preconfigured boards, create a custom image with CloudPrintd preinstalled and WiFi setup enabled by default.

**Base image:** Raspberry Pi OS Lite 64-bit

### Image Builder Script

Use this script to create a CloudPrintd image:

```bash
#!/bin/bash
# build-cloudprintd-image.sh

set -e

# Configuration
BASE_IMAGE="2025-11-19-raspios-bookworm-arm64-lite.img"
OUTPUT_IMAGE="cloudprintd-v1.0.0-$(date +%Y%m%d).img"
MOUNT_BOOT="/mnt/cloudprintd-boot"
MOUNT_ROOT="/mnt/cloudprintd-root"

echo "Building CloudPrintd Image..."

# Download base image if needed
if [ ! -f "$BASE_IMAGE" ]; then
    echo "Downloading base image..."
    wget https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2025-11-19/$BASE_IMAGE.xz
    xz -d $BASE_IMAGE.xz
fi

# Copy to output
echo "Creating output image..."
cp "$BASE_IMAGE" "$OUTPUT_IMAGE"

# Mount partitions
echo "Mounting image..."
LOOP_DEVICE=$(sudo losetup -fP --show "$OUTPUT_IMAGE")
sudo mkdir -p "$MOUNT_BOOT" "$MOUNT_ROOT"
sudo mount "${LOOP_DEVICE}p1" "$MOUNT_BOOT"
sudo mount "${LOOP_DEVICE}p2" "$MOUNT_ROOT"

# Enable SSH
echo "Enabling SSH..."
sudo touch "$MOUNT_BOOT/ssh"

# Configure WiFi country
echo "Setting WiFi country to US..."
echo 'country=US' | sudo tee "$MOUNT_BOOT/wpa_supplicant.conf"

# Create cloudprintd user
echo "Creating cloudprintd user..."
sudo chroot "$MOUNT_ROOT" useradd -m -s /bin/bash cloudprintd
echo 'cloudprintd:cloudprintd' | sudo chroot "$MOUNT_ROOT" chpasswd
sudo chroot "$MOUNT_ROOT" usermod -aG sudo cloudprintd

# Copy CloudPrintd files
echo "Installing CloudPrintd..."
sudo mkdir -p "$MOUNT_ROOT/opt/cloudprintd"
sudo cp -r ../PrinterServer/* "$MOUNT_ROOT/opt/cloudprintd/"
sudo chroot "$MOUNT_ROOT" chown -R cloudprintd:cloudprintd /opt/cloudprintd

# Install dependencies
echo "Installing packages (chroot)..."
sudo chroot "$MOUNT_ROOT" apt update
sudo chroot "$MOUNT_ROOT" apt install -y \
    python3 python3-pip python3-venv \
    cups libcups2-dev \
    nodejs npm \
    hostapd dnsmasq wireless-tools \
    git

# Build Python venv
echo "Creating Python environment..."
sudo chroot "$MOUNT_ROOT" bash -c 'cd /opt/cloudprintd && python3 -m venv venv'
sudo chroot "$MOUNT_ROOT" bash -c 'cd /opt/cloudprintd && ./venv/bin/pip install -r requirements.txt'

# Build frontend
echo "Building frontend..."
sudo chroot "$MOUNT_ROOT" bash -c 'cd /opt/cloudprintd/webui && npm install && npm run build'

# Install services
echo "Installing services..."
sudo cp "$MOUNT_ROOT/opt/cloudprintd/systemd/cloudprintd.service" "$MOUNT_ROOT/etc/systemd/system/"
sudo cp "$MOUNT_ROOT/opt/cloudprintd/systemd/cloudprintd-wifi-setup.service" "$MOUNT_ROOT/etc/systemd/system/"
sudo chroot "$MOUNT_ROOT" systemctl enable cloudprintd
sudo chroot "$MOUNT_ROOT" systemctl enable cloudprintd-wifi-setup

# Configure sudoers
echo "Configuring permissions..."
sudo cp ../deployment/sudoers-cloudprintd "$MOUNT_ROOT/etc/sudoers.d/cloudprintd"
sudo chmod 440 "$MOUNT_ROOT/etc/sudoers.d/cloudprintd"

# Cleanup
echo "Cleaning up..."
sudo chroot "$MOUNT_ROOT" apt clean
sudo rm -rf "$MOUNT_ROOT/var/log/*"
sudo rm -rf "$MOUNT_ROOT/home/pi/.bash_history"

# Unmount
echo "Unmounting..."
sudo umount "$MOUNT_BOOT"
sudo umount "$MOUNT_ROOT"
sudo losetup -d "$LOOP_DEVICE"
sudo rmdir "$MOUNT_BOOT" "$MOUNT_ROOT"

# Compress
echo "Compressing image..."
xz -9 -T 0 "$OUTPUT_IMAGE"

echo "====================================="
echo "CloudPrintd image ready!"
echo "Output: ${OUTPUT_IMAGE}.xz"
echo "Size: $(ls -lh ${OUTPUT_IMAGE}.xz | awk '{print $5}')"
echo "====================================="
echo ""
echo "Flash to SD card:"
echo "  sudo dd if=${OUTPUT_IMAGE}.xz of=/dev/sdX bs=4M status=progress"
echo "  OR use Raspberry Pi Imager"
```

### Per-Unit Customization

For commercial products, each unit should have:

1. **Unique API token** (generated on first boot)
2. **Unique AP SSID** (based on MAC address last 4 digits)
3. **Serial number** (printed on label)

**First-boot script** (`/opt/cloudprintd/scripts/firstboot.sh`):

```bash
#!/bin/bash
# Run once on first boot to customize each unit

FIRSTBOOT_FLAG="/opt/cloudprintd/.firstboot_done"

if [ -f "$FIRSTBOOT_FLAG" ]; then
    exit 0
fi

echo "Running first-boot customization..."

# Generate unique API token
TOKEN=$(openssl rand -hex 32)
echo "INITIAL_TOKEN=$TOKEN" > /opt/cloudprintd/.env

# Print to label/QR code (if printer connected)
# TODO: Integrate with label printer

# Mark as done
touch "$FIRSTBOOT_FLAG"

echo "First-boot complete. Token: $TOKEN"
```

---

## Commercial Packaging

### Quick Start Card Template

```
╔═════════════════════════════════════════════════════╗
║           CloudPrintd Quick Start                   ║
╠═════════════════════════════════════════════════════╣
║                                                     ║
║  1. POWER ON                                        ║
║     Plug in USB-C power supply                      ║
║     Wait 2 minutes (LED blinks while booting)       ║
║                                                     ║
║  2. CONNECT WIFI                                    ║
║     On phone/laptop, connect to WiFi:               ║
║                                                     ║
║        Network: CloudPrintd-SETUP-XXXX              ║
║        Password: cloudprintd                        ║
║                                                     ║
║     Setup page opens automatically                  ║
║     (If not, go to: http://192.168.4.1:8000)        ║
║                                                     ║
║     Select your WiFi network and enter password     ║
║     Pi will reboot (wait 1 minute)                  ║
║                                                     ║
║  3. ACCESS DASHBOARD                                ║
║     Open browser on your network:                   ║
║        http://cloudprintd.local:8000                ║
║                                                     ║
║     Initial API Token:                              ║
║     [QR CODE HERE]                                  ║
║     cp-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX             ║
║                                                     ║
║  4. ADD PRINTERS                                    ║
║     Dashboard → Setup Wizard                        ║
║     Or: Dashboard → Printers → Discover             ║
║                                                     ║
╠═════════════════════════════════════════════════════╣
║  Support: support@cloudprintd.com                   ║
║  Docs: https://docs.cloudprintd.com                 ║
║  Serial: CDP-XXXXXXXX                               ║
╚═════════════════════════════════════════════════════╝
```

### Package Contents Checklist

- [ ] Raspberry Pi (4/5) with CloudPrintd preloaded
- [ ] 32GB+ microSD card (Kingston/SanDisk)
- [ ] USB-C power supply (15W+ official)
- [ ] Aluminum case with cooling
- [ ] Ethernet cable (for Pi 4/5)
- [ ] Quick Start card (printed, laminated)
- [ ] API token card (unique per unit)
- [ ] Product sticker (CloudPrintd branding + serial)
- [ ] Anti-static bag

---

## Security Considerations

### Production Hardening

1. **Change default AP password**:
   Edit `wifi-setup-check.sh`:
   ```bash
   AP_PASSWORD="YourSecurePassword2024!"
   ```
   Update Quick Start card accordingly.

2. **Limit sudo commands**:
   Review `/etc/sudoers.d/cloudprintd` - only include necessary commands

3. **API rate limiting**:
   Add to `network.py`:
   ```python
   from fastapi_limiter import FastAPILimiter
   from fastapi_limiter.depends import RateLimiter
   
   @router.post("/wifi/configure", dependencies=[Depends(RateLimiter(times=5, seconds=300))])
   ```

4. **HTTPS only** (production):
   - Use Let's Encrypt for SSL certificates
   - Or reverse proxy (Nginx) with SSL

5. **Change default hostname**:
   - Let users customize during setup
   - Or use serial number: `cloudprintd-A1B2.local`

### Compliance

For commercial products, ensure:

- **FCC Part 15** compliance (Raspberry Pi pre-certified)
- **CE marking** (if selling in EU)
- **Privacy policy** (WiFi password handling)
- **Open source licenses** (include COPYING file)

---

## Cost Analysis

### Bill of Materials (per unit)

| Component | Cost | Supplier |
|-----------|------|----------|
| Raspberry Pi 4 (4GB) | $55 | Official distributors |
| 32GB microSD (Kingston) | $8 | Amazon |
| USB-C Power Supply (15W) | $8 | CanaKit |
| Aluminum Case | $12 | Flirc/Argon |
| Ethernet Cable (3ft) | $2 | Monoprice |
| Packaging + Labels | $3 | Local print shop |
| **Total Hardware** | **$88** | |
| Labor (assembly, QC) | $12 | 15 min @ $48/hr |
| **Total Cost** | **$100** | |

**Retail Price:** $149.99  
**Margin:** $50 (50%)  
**Break-even:** 120 units (to cover FCC testing $5K + dev time)

---

## Roadmap

### Phase 1: MVP (Current)
- [x] WiFi AP mode
- [x] Captive portal
- [x] Network configuration UI
- [x] Hostname configuration

### Phase 2: Enhanced Setup (Next)
- [ ] Bluetooth configuration (mobile app)
- [ ] QR code WiFi setup
- [ ] Multi-language support
- [ ] Ethernet DHCP/static IP UI

### Phase 3: Advanced Features
- [ ] VPN configuration (Tailscale, WireGuard)
- [ ] Multiple WiFi networks (auto-switch)
- [ ] WiFi diagnostics tool
- [ ] Remote SSH access control

### Phase 4: Cloud Integration
- [ ] CloudPrintd Cloud service
- [ ] Remote management portal
- [ ] Firmware OTA updates
- [ ] Analytics dashboard

---

## Support & Documentation

### User Documentation

Create docs site (docs.cloudprintd.com) with:

1. **Getting Started**
   - Unboxing
   - WiFi setup
   - First print job

2. **Network Configuration**
   - Changing WiFi networks
   - Static IP setup
   - Hostname customization
   - Troubleshooting connectivity

3. **Printer Setup**
   - Supported printers
   - Adding printers
   - Testing print jobs

4. **Salesforce Integration**
   - OAuth setup
   - Print templates
   - Troubleshooting

### Reseller Documentation

For VARs/MSPs:

1. **Deployment Guide**
   - Bulk configuration
   - Network best practices
   - Enterprise WiFi (WPA2-Enterprise)

2. **Support Playbook**
   - Common issues
   - Diagnostic commands
   - RMA process

---

## Next Steps

1. **Deploy to test Pi:**
   ```bash
   # On your Pi
   cd /opt/cloudprintd
   git pull
   ./deploy.sh
   ```

2. **Test AP mode:**
   - Clear WiFi config
   - Reboot
   - Connect to AP
   - Configure WiFi via UI

3. **Build custom image:**
   - Run image builder script
   - Flash to new SD card
   - Test from scratch

4. **Order prototype hardware:**
   - 10x Pi 4 (4GB)
   - Cases, power supplies
   - Test packaging

5. **Beta testing:**
   - Recruit 5-10 testers
   - Gather feedback
   - Iterate

**Ready to go to market!** 🚀
