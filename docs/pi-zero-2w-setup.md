# CloudPrintd Setup Guide for Raspberry Pi Zero 2 W

## Quick Start for Raspberry Pi Zero 2 W

This guide will help you deploy CloudPrintd on a Raspberry Pi Zero 2 W in under 15 minutes.

### Hardware Requirements

- **Raspberry Pi Zero 2 W** (recommended) or any Pi model
- **MicroSD Card:** 16GB+ (Class 10 or better)
- **Power Supply:** 5V 2.5A minimum
- **Network:** Wi-Fi or USB Ethernet adapter

### Performance Notes

The Pi Zero 2 W has:
- **CPU:** Quad-core ARM Cortex-A53 @ 1GHz
- **RAM:** 512MB
- **Wi-Fi:** 2.4GHz 802.11n

CloudPrintd is optimized for low-resource environments and runs excellently on the Pi Zero 2 W for:
- Up to 5 printers
- Up to 100 print jobs per day
- Response time < 500ms

For higher workloads (10+ printers, 500+ jobs/day), use a Pi 4 (2GB+).

---

## Installation Steps

### 1. Prepare Raspberry Pi OS

Download and flash **Raspberry Pi OS Lite (64-bit)** to your microSD card:

**Recommended: 64-bit OS** for better performance and future compatibility.

```bash
# Using Raspberry Pi Imager (recommended)
# Select: Raspberry Pi OS Lite (64-bit)
# Configure: hostname, WiFi, SSH, user
```

**Note:** The Pi Zero 2 W supports both 32-bit and 64-bit OS. While 32-bit uses slightly less RAM, **64-bit is recommended** for:
- Better performance with modern Python packages
- Official Raspberry Pi recommendation (as of 2023+)
- Future software compatibility
- CloudPrintd is tested on both but optimized for 64-bit

**Your Configuration:**
- **Hostname:** `cloudprintd` ✓ (you configured this)
- **Username:** `admin` ✓ (you configured this)
- **Enable SSH:** Yes
- **Configure WiFi:** Your network credentials

**Note:** This guide uses your actual configuration values.

---

### First Boot - What to Expect

**When you first power on your Pi:**

1. **Green LED will flash rapidly** (0-30 seconds)
   - This is normal - the Pi is reading from the SD card
   - Flashing = booting and loading files

2. **First boot takes 1-2 minutes** (Pi Zero 2 W)
   - Pi 4/5 are faster (30-60 seconds)
   - The Pi is resizing partitions and configuring itself

3. **LED behavior guide:**
   - **Solid green** = Ready, idle
   - **Rapid flashing** = Reading SD card (booting)
   - **Slow flashing** (1-2 blinks/sec) = Normal activity
   - **No LED after 3 minutes** = Problem (see troubleshooting below)

4. **When is it ready?**
   - LED stops rapid flashing (becomes slow/occasional blinks)
   - Wait **2 minutes total** from power-on to be safe
   - Then check if WiFi network is available (if using WiFi AP mode)
   - Or ping the hostname: `ping cloudprintd.local`

**WiFi AP Mode (for commercial CloudPrintd products):**
- **Only activates if NO WiFi is configured in the OS image**
- After 2 minutes, look for WiFi network: `CloudPrintd-SETUP-XXXX`
- If you see this network, the Pi is ready for setup!
- Connect using password: `cloudprintd`
- Browser should auto-open to `http://192.168.4.1:8000`

**Normal Mode (WiFi pre-configured - YOUR SITUATION):**
- **If you configured WiFi in Raspberry Pi Imager, this is what happens:**
- Pi connects to your WiFi automatically
- **No AP mode network** - CloudPrintd-SETUP-XXXX won't appear
- Find it on your network: `ping cloudprintd.local`
- Access via: `http://cloudprintd.local:8000`
- The WiFi configuration UI is still available in Dashboard → Network tab

**Troubleshooting first boot:**
- **No LED at all:** Check power supply (needs 5V 2.5A minimum)
- **LED solid red only (no green):** SD card not detected - reseat card
- **Continuous rapid flashing (5+ minutes):** SD card error - reflash OS
- **Can't find on network:** Check router DHCP leases for IP address
- **⚠️ 6 blinks then pause (repeating):** **BOOT FAILURE** - See detailed fix below

---

## ⚠️ CRITICAL: 6-Blink Pattern = Boot Failure

**If your Pi LED blinks exactly 6 times, pauses, then repeats - this is a boot error code.**

Your Pi **cannot load the operating system**. This is fixable! Here's what to do:

### Quick Fix (Try These In Order)

**1. Reseat the SD Card**
```
Power off Pi completely (unplug power)
Remove SD card from slot
Push SD card back in firmly (should click)
Power back on
```
Sometimes the card isn't seated properly.

**2. Reflash the SD Card** ⭐ **MOST LIKELY FIX**

The OS image is probably corrupt or incompatible. Reflash it:

**Use Raspberry Pi Imager (Official Tool):**
- Download: https://www.raspberrypi.com/software/

**Settings:**
```
Device: Raspberry Pi Zero 2 W
OS: Raspberry Pi OS Lite (64-bit) ← IMPORTANT
Storage: Your SD card

Click ⚙️ (Settings gear):
✓ Set hostname: cloudprintd
✓ Enable SSH (use password authentication)
✓ Username: admin
✓ Password: [your choice]
✓ Configure WiFi SSID: [your network name]
✓ WiFi Password: [your password]
✓ WiFi country: US (or your country)
```

**Click WRITE and wait for verification to complete!**

**3. Try Different SD Card**
- Your card might be fake/faulty
- Use known brands: SanDisk, Samsung, Kingston
- Minimum: Class 10, 8GB
- Recommended: 16GB or 32GB

**4. Check Power Supply**
- Must be **5V 2.5A** (2500mA minimum)
- Official Raspberry Pi power supply works best
- Phone chargers are usually only 1A - not enough!
- Bad USB cable can cause voltage drop

**5. Try 32-bit OS (if 64-bit fails)**
```
In Raspberry Pi Imager:
OS: Raspberry Pi OS Lite (32-bit)
```
32-bit uses less RAM and might work if 64-bit doesn't.

### Why This Happens

The 6-blink code means:
- Bootloader started successfully ✓
- But cannot load `start.elf` or kernel ✗

Common causes:
1. ❌ **Corrupt SD card write** (most common)
2. ❌ **Wrong OS image** (used Pi 3/4 image instead of Zero 2 W)
3. ❌ **Interrupted flash** (unplugged during write)
4. ❌ **Fake SD card** (shows 32GB but actually 4GB)
5. ❌ **Insufficient power** (brownout during boot)

### Verify SD Card on Computer

Insert SD card into your PC and check:

**On Windows:**
1. Open "Disk Management"
2. You should see:
   - ~256MB partition (FAT32) labeled "boot"
   - Larger partition (ext4 format)

**In boot partition, check these files exist:**
- `start.elf` ← Bootloader needs this!
- `kernel8.img` (64-bit) or `kernel7.img` (32-bit)
- `config.txt`
- `bootcode.bin`

**Missing files = Incomplete flash → Reflash SD card**

### Advanced: Manual config.txt Check

If files are present, open `config.txt` in boot partition:

**For Pi Zero 2 W (64-bit), should contain:**
```ini
[pi0w2]
arm_64bit=1

[all]
dtparam=audio=on
camera_auto_detect=1
display_auto_detect=1
```

**Wrong config = Boot failure**

### LED Blink Code Reference

| Blinks | Meaning | Fix |
|--------|---------|-----|
| 3 | SD card error | Check card inserted fully |
| 4 | start.elf not found | Reflash - boot files missing |
| **6** | **Cannot load kernel/OS** | **Reflash or try 32-bit OS** |
| 7 | Kernel.img not found | Wrong OS image |
| 8 | SDRAM failure | Hardware issue - RMA |

### Still Having Issues?

**Test with stock Raspberry Pi OS:**
1. Flash official "Raspberry Pi OS (32-bit)" with no customization
2. Don't configure WiFi/SSH yet
3. Just boot and see if LED pattern changes
4. If this works → Your settings were wrong
5. If this fails → SD card or hardware problem

**Next steps if nothing works:**
- Try a completely different SD card (borrow from friend)
- Try a different power supply (official Pi adapter)
- If still failing → Hardware defect, contact support

**Email support@cloudprintd.com with:**
- LED blink pattern (video helpful!)
- SD card brand and size
- Power supply specs
- What you've tried

---

**Once you get past the 6-blink and Pi boots normally, continue below:**

---

## CloudPrintd Installation

**⚠️ IMPORTANT: You must have a BOOTING Pi before installing CloudPrintd!**

If your Pi won't boot (6-blinks), fix that first using the troubleshooting guide above.

### Installation Flow

```
Step 1: Flash STOCK Raspberry Pi OS
        ↓
        Configure WiFi, SSH, username in Raspberry Pi Imager
        ↓
Step 2: Boot Pi and verify it works
        ↓
        ping cloudprintd.local (should get replies)
        ↓
Step 3: SSH into Pi
        ↓
        ssh admin@cloudprintd.local
        ↓
Step 4: Install CloudPrintd (choose one method below)
        ↓
        Method A: Automated installer (recommended)
        Method B: Manual installation (detailed control)
        ↓
Step 5: Access Dashboard
        ↓
        http://cloudprintd.local:8000
```

---

### Method A: Automated Installation (Recommended)

**One command, installs everything automatically:**

```bash
# SSH into your Pi first
ssh admin@cloudprintd.local

# Run automated installer
curl -sSL https://raw.githubusercontent.com/v29tnr/CloudPrintd/main/scripts/install-cloudprintd.sh | bash

# OR download and run:
wget https://raw.githubusercontent.com/v29tnr/CloudPrintd/main/scripts/install-cloudprintd.sh
chmod +x install-cloudprintd.sh
./install-cloudprintd.sh
```

**What it does:**
- ✅ Updates system packages
- ✅ Installs all dependencies (Python, Node.js, CUPS)
- ✅ Creates cloudprintd service user
- ✅ Downloads latest CloudPrintd release
- ✅ Builds frontend
- ✅ Installs systemd service
- ✅ Generates API token
- ✅ Starts CloudPrintd
- ✅ Optional: Installs WiFi AP mode (for commercial products)

**After installation completes:**
```bash
# Access dashboard:
http://cloudprintd.local:8000

# Check service status:
sudo systemctl status cloudprintd

# View logs:
sudo journalctl -u cloudprintd -f
```

---

### Method B: Manual Installation (Step-by-Step)

**For full control over the installation process:**

**Now continue with manual setup:**

Insert the SD card and boot the Pi. Find its IP address:

```bash
# From another computer on the same network
ping cloudprintd.local

# Or check your router's DHCP leases
```

SSH into your Pi:

```bash
ssh admin@cloudprintd.local
# Or: ssh admin@192.168.1.XXX
```

### 2. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Install Dependencies

```bash
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
```

**For Node.js (frontend build):**

```bash
# Install Node.js 20 LTS (supported until April 2026)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version  # Should show v20.x.x
npm --version
```

### 4. Create CloudPrintd User

```bash
sudo useradd -r -s /bin/bash -d /home/cloudprintd -m cloudprintd
sudo mkdir -p /opt/cloudprintd/packages
sudo mkdir -p /home/cloudprintd/{logs,data}
sudo chown -R cloudprintd:cloudprintd /opt/cloudprintd /home/cloudprintd
```

### 5. Install CloudPrintd

**Option A: From Source**

```bash
# Clone repository
cd /opt/cloudprintd/packages
sudo git clone https://github.com/yourorg/cloudprintd.git v1.0.0

# Or download release
cd /opt/cloudprintd/packages
sudo wget https://github.com/yourorg/cloudprintd/releases/download/v1.0.0/cloudprintd-v1.0.0.tar.gz
sudo tar -xzf cloudprintd-v1.0.0.tar.gz
sudo mv cloudprintd-v1.0.0 v1.0.0

# Set ownership
sudo chown -R cloudprintd:cloudprintd /opt/cloudprintd/packages/v1.0.0
```

**Create symlink:**

```bash
cd /opt/cloudprintd/packages
sudo ln -s v1.0.0 current
```

### 6. Install Python Dependencies

```bash
cd /opt/cloudprintd/packages/current
sudo -u cloudprintd python3 -m venv venv
sudo -u cloudprintd venv/bin/pip install --upgrade pip
sudo -u cloudprintd venv/bin/pip install -r requirements.txt
```

**⚠️ Pi Zero 2 W Note:** This step may take 10-15 minutes due to limited resources. Be patient!

### 7. Build Frontend

```bash
cd /opt/cloudprintd/packages/current/webui
sudo -u cloudprintd npm install
sudo -u cloudprintd npm run build
```

**Note:** Building on Pi Zero 2 W takes 5-10 minutes. For faster deployment, build on a more powerful machine and copy `dist/` folder.

### 8. Configure CUPS (for standard printers)

```bash
# Add cloudprintd user to lpadmin group
sudo usermod -a -G lpadmin cloudprintd

# Enable CUPS web interface (optional)
sudo cupsctl --remote-any
sudo systemctl restart cups
```

### 9. Install Systemd Service

```bash
sudo cp /opt/cloudprintd/packages/current/cloudprintd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cloudprintd
```

### 10. Start CloudPrintd

```bash
sudo systemctl start cloudprintd

# Check status
sudo systemctl status cloudprintd

# View logs
sudo journalctl -u cloudprintd -f
```

### 11. Access Setup Wizard

Open your browser and navigate to:

```
http://cloudprintd.local:8000/setup
```

Or use the IP address:

```
http://192.168.1.XXX:8000/setup
```

Follow the 5-step setup wizard to configure:
1. Welcome
2. Network connectivity (Cloudflare/Tailscale/etc)
3. Printer discovery and configuration
4. API token generation
5. Complete setup

---

## Network Connectivity Options

### Option 1: Cloudflare Tunnel (Recommended for Salesforce)

**Advantages:**
- Free
- No port forwarding
- Automatic HTTPS
- Works behind firewalls

**Setup:**

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm
sudo mv cloudflared-linux-arm /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create cloudprintd

# Configure tunnel
nano ~/.cloudflared/config.yml
```

**config.yml:**
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /home/admin/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: cloudprintd.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

**Run tunnel:**
```bash
cloudflared tunnel route dns YOUR_TUNNEL_ID cloudprintd.yourdomain.com
cloudflared tunnel run cloudprintd
```

**Make it a service:**
```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

### Option 2: Tailscale VPN

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Access via Tailscale IP (found in admin console).

### Option 3: Local Network Only

If Salesforce resources are on the same network:
- Use local IP: `http://192.168.1.XXX:8000`
- Configure firewall to allow port 8000

---

## Creating Master Image for Commercial Products

**Once you have CloudPrintd working perfectly on ONE Pi, create a master image to duplicate to other SD cards.**

### Step 1: Prepare Master Pi

SSH into your working CloudPrintd Pi:

```bash
ssh admin@cloudprintd.local
```

### Step 2: Test Everything

```bash
# Verify CloudPrintd is running
sudo systemctl status cloudprintd

# Test dashboard access
curl http://localhost:8000/api/v1/health

# Test a printer (if configured)
```

### Step 3: Clear WiFi Configuration

**For commercial products, customers need to configure THEIR WiFi:**

```bash
# Stop CloudPrintd
sudo systemctl stop cloudprintd

# Clear WiFi credentials (enables AP mode for customers)
sudo bash -c 'cat > /etc/wpa_supplicant/wpa_supplicant.conf' << 'EOF'
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US
EOF

# Clear network history
sudo rm -f /etc/NetworkManager/system-connections/*

# Verify WiFi AP setup service is enabled
sudo systemctl enable cloudprintd-wifi-setup.service
```

### Step 4: Clean Up Logs and History

```bash
# Clear bash history
history -c
rm -f ~/.bash_history
sudo rm -f /home/cloudprintd/.bash_history
sudo rm -f /root/.bash_history

# Clear logs
sudo journalctl --vacuum-time=1s
sudo rm -f /var/log/*.log
sudo rm -f /var/log/cloudprintd/*.log

# Remove SSH host keys (will regenerate on first customer boot)
sudo rm -f /etc/ssh/ssh_host_*

# Regenerate SSH keys script (runs on first boot)
sudo bash -c 'cat > /etc/rc.local' << 'EOF'
#!/bin/bash
test -f /etc/ssh/ssh_host_dsa_key || dpkg-reconfigure openssh-server
exit 0
EOF
sudo chmod +x /etc/rc.local
```

### Step 5: Set Unique Per-Unit Values

**Create script to run on first customer boot:**

```bash
sudo nano /usr/local/bin/first-boot-setup.sh
```

```bash
#!/bin/bash
# First boot customization - runs once per unit

FIRST_BOOT_FLAG="/opt/cloudprintd/.first_boot_done"

if [ -f "$FIRST_BOOT_FLAG" ]; then
    exit 0  # Already ran
fi

# Generate unique API token
TOKEN=$(openssl rand -hex 32)
echo "INITIAL_TOKEN=cp-${TOKEN}" | sudo tee /opt/cloudprintd/.env
sudo chmod 600 /opt/cloudprintd/.env
sudo chown cloudprintd:cloudprintd /opt/cloudprintd/.env

# Print token to serial console (for manufacturing)
echo "========================================" > /dev/console
echo "CloudPrintd Initial API Token:" > /dev/console
echo "cp-${TOKEN}" > /dev/console
echo "========================================" > /dev/console

# Log to file
echo "cp-${TOKEN}" | sudo tee /opt/cloudprintd/.initial_token.txt

# Mark as complete
sudo touch "$FIRST_BOOT_FLAG"

# Restart CloudPrintd with new token
sudo systemctl restart cloudprintd

exit 0
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/first-boot-setup.sh

# Add to systemd
sudo bash -c 'cat > /etc/systemd/system/first-boot-setup.service' << 'EOF'
[Unit]
Description=CloudPrintd First Boot Setup
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/first-boot-setup.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable first-boot-setup.service
```

### Step 6: Final Shutdown

```bash
# Final system shutdown (for imaging)
sudo shutdown -h now
```

### Step 7: Create Image from SD Card

**On Windows:**

1. **Remove SD card from Pi**
2. **Insert into PC**
3. **Use Win32 Disk Imager:**
   - Download: https://sourceforge.net/projects/win32diskimager/
   - Click "Read"
   - Save as: `cloudprintd-master-v1.0.0.img`
   - Wait for completion (5-10 minutes for 32GB card)

4. **Compress image:**
   ```powershell
   # PowerShell
   Compress-Archive -Path "cloudprintd-master-v1.0.0.img" -DestinationPath "cloudprintd-master-v1.0.0.zip"
   
   # OR use 7-Zip for better compression:
   # Right-click → 7-Zip → Add to archive... → Choose .xz format
   ```

**On Mac/Linux:**

```bash
# Insert SD card and find device
diskutil list  # Mac
lsblk          # Linux

# Create image (replace /dev/diskX with your SD card)
sudo dd if=/dev/diskX of=cloudprintd-master-v1.0.0.img bs=4M status=progress

# Compress
xz -9 cloudprintd-master-v1.0.0.img
# Creates: cloudprintd-master-v1.0.0.img.xz
```

### Step 8: Duplicate to Production Cards

**Write master image to new SD cards:**

```powershell
# Windows - Win32 Disk Imager
# 1. Decompress .zip/.xz file
# 2. Open Win32 Disk Imager
# 3. Select cloudprintd-master-v1.0.0.img
# 4. Select drive letter (SD card)
# 5. Click "Write"
# 6. Repeat for each card
```

**For mass production (100+ units):**
- Use SD card duplicator hardware (10-port, ~$300)
- Or send master image to contract manufacturer

### Step 9: First Customer Boot

**What happens when customer powers on:**

```
0:00 - Pi boots from cloned SD card
0:30 - first-boot-setup.sh runs
       Generates unique API token
       Saves to /opt/cloudprintd/.initial_token.txt
0:45 - wifi-setup-check.sh runs
       Detects no WiFi configured
       Starts AP mode
1:30 - WiFi network appears: "CloudPrintd-SETUP-A1B2"
       Customer connects with password: cloudprintd
2:00 - Customer configures WiFi through captive portal
       Pi reboots
3:00 - Pi connects to customer's WiFi
       CloudPrintd accessible at: http://cloudprintd.local:8000
```

### Quality Control Checklist

Before imaging, verify:

- [ ] CloudPrintd service starts automatically
- [ ] Dashboard loads at http://localhost:8000
- [ ] WiFi configuration is cleared
- [ ] first-boot-setup.service is enabled
- [ ] cloudprintd-wifi-setup.service is enabled
- [ ] No personal data (WiFi passwords, API tokens)
- [ ] Logs are cleared
- [ ] SSH host keys are cleared
- [ ] Image size is reasonable (<4GB for 32GB card)

### Updating Master Image

When you release a new version:

1. Boot a Pi with current master image
2. SSH in and update CloudPrintd:
   ```bash
   cd /opt/cloudprintd
   git pull
   sudo systemctl restart cloudprintd
   ```
3. Test new version
4. Repeat Steps 3-8 above to create new master image
5. Version the filename: `cloudprintd-master-v1.1.0.img`

---

## Performance Optimization for Pi Zero 2 W

### 1. Reduce Memory Usage

Edit `/boot/config.txt`:

```bash
sudo nano /boot/config.txt
```

Add:
```bash
# Reduce GPU memory (we don't need graphics)
gpu_mem=16
```

### 2. Enable Swap (recommended for compiling)

```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
```

Change:
```
CONF_SWAPSIZE=1024
```

```bash
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 3. Disable Unused Services

```bash
sudo systemctl disable bluetooth
sudo systemctl disable hciuart
```

### 4. Monitor Resources

```bash
# Check memory
free -h

# Check CPU
top

# Check disk
df -h
```

---

## Testing

### Test API Endpoint

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "running",
  "version": "1.0.0",
  "uptime_seconds": 120,
  "printers_configured": 0,
  "printers_online": 0
}
```

### Access Web Interface

Open your browser:
```
http://cloudprintd.local:8000/setup
# Or: http://192.168.1.XXX:8000/setup
```

### Test Print Job

First, generate an API token from the setup wizard, then:

```bash
curl -X POST http://localhost:8000/api/v1/print \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "printer": "your_printer_id",
    "content": "^XA^FO50,50^A0N,50,50^FDTest from Pi Zero 2 W^FS^XZ",
    "format": "zpl",
    "copies": 1
  }'
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u cloudprintd -n 50

# Check port
sudo netstat -tlnp | grep 8000

# Test manually
sudo -u cloudprintd /opt/cloudprintd/packages/current/venv/bin/python \
  -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Out of Memory During Build

If `npm install` or `pip install` fails with out-of-memory:

**Enable more swap:**
```bash
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**Or build on another machine and copy:**
```bash
# On a more powerful machine
npm install && npm run build
tar -czf dist.tar.gz dist/

# Copy to Pi
scp dist.tar.gz pi@cloudprintd.local:/tmp/
ssh pi@cloudprintd.local
cd /opt/cloudprintd/packages/current/webui
tar -xzf /tmp/dist.tar.gz
```

### Can't Access Setup Wizard

```bash
# Check firewall
sudo ufw allow 8000/tcp

# Or disable firewall temporarily
sudo ufw disable

# Check if service is listening
sudo netstat -tlnp | grep 8000
```

### Printer Not Found

```bash
# Test network connectivity to printer
ping 192.168.1.100

# Test ZPL port
nc -zv 192.168.1.100 9100

# Send test ZPL directly
echo "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ" | nc 192.168.1.100 9100
```

---

## Maintenance

### View Logs

```bash
# Service logs
sudo journalctl -u cloudprintd -f

# Application logs
tail -f /home/cloudprintd/logs/cloudprintd.log
tail -f /home/cloudprintd/logs/cloudprintd-error.log
```

### Restart Service

```bash
sudo systemctl restart cloudprintd
```

### Update CloudPrintd

Use the web dashboard's "Updates" tab, or manually:

```bash
cd /opt/cloudprintd/packages
sudo -u cloudprintd tar -xzf /path/to/cloudprintd-v1.1.0.pbpkg
sudo rm current
sudo ln -s v1.1.0 current
sudo systemctl restart cloudprintd
```

### Backup Configuration

```bash
# Backup config files
sudo cp -r /opt/cloudprintd/config ~/cloudprintd-config-backup-$(date +%Y%m%d)

# Or create a script
sudo nano /usr/local/bin/backup-cloudprintd
```

```bash
#!/bin/bash
BACKUP_DIR="/home/admin/backups/cloudprintd-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp -r /opt/cloudprintd/config "$BACKUP_DIR/"
echo "Backup saved to $BACKUP_DIR"
```

```bash
sudo chmod +x /usr/local/bin/backup-cloudprintd
```

---

## Advanced: Static IP Configuration

For production deployments, set a static IP:

```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```bash
interface wlan0
static ip_address=192.168.1.50/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Restart networking:
```bash
sudo systemctl restart dhcpcd
```

---

## Security Best Practices

1. **Change default password:**
   ```bash
   passwd
   ```

2. **Enable firewall:**
   ```bash
   sudo apt install ufw
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 8000/tcp # CloudPrintd
   sudo ufw enable
   ```

3. **Keep system updated:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

4. **Rotate API tokens regularly** via the web dashboard

5. **Use HTTPS** with Cloudflare Tunnel or Let's Encrypt

---

## Support

- **Documentation:** See `/opt/cloudprintd/packages/current/docs/`
- **Logs:** `/home/cloudprintd/logs/`
- **Service Status:** `sudo systemctl status cloudprintd`
- **Web Dashboard:** `http://cloudprintd.local:8000/` (your hostname)

---

## Next Steps

1. ✅ Complete setup wizard
2. ✅ Add printers via web interface
3. ✅ Test print jobs
4. ✅ Configure Salesforce integration (see [API Integration Guide](api-integration.md))
5. ✅ Set up connectivity (Cloudflare/Tailscale)
6. ✅ Enable automatic updates in dashboard

**You're ready to print from Salesforce! 🎉**
