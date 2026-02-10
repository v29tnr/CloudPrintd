# CloudPrintd Troubleshooting Guide

## Common Issues and Solutions

### Service Issues

#### Service Won't Start

**Symptoms:**
- `systemctl status CloudPrintd` shows "failed" or "inactive"
- No response on port 8000

**Solutions:**

1. Check service logs:
```bash
sudo journalctl -u CloudPrintd -n 50 --no-pager
```

2. Check for port conflicts:
```bash
sudo netstat -tlnp | grep 8000
```

3. Verify Python environment:
```bash
cd /opt/CloudPrintd/packages/current/app
source ../venv/bin/activate
python3 -c "import fastapi; print('FastAPI OK')"
```

4. Check file permissions:
```bash
ls -la /opt/CloudPrintd/packages/current/
sudo chown -R CloudPrintd:CloudPrintd /opt/CloudPrintd
```

5. Test manual start:
```bash
sudo -u CloudPrintd /opt/CloudPrintd/packages/current/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Service Keeps Restarting

**Check logs for errors:**
```bash
sudo journalctl -u CloudPrintd -f
```

**Common causes:**
- Configuration file errors
- Missing dependencies
- Database connection issues
- Port binding failures

### Printer Issues

#### Printer Discovery Not Working

**Checklist:**
- [ ] Printers are powered on
- [ ] Printers are on the same network as the Raspberry Pi
- [ ] Firewall isn't blocking port 9100
- [ ] Correct IP range specified

**Test printer connectivity:**
```bash
# Ping printer
ping 192.168.1.100

# Test port 9100
nc -zv 192.168.1.100 9100

# Or using telnet
telnet 192.168.1.100 9100
```

**Manual ZPL test:**
```bash
echo "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ" | nc 192.168.1.100 9100
```

#### Printer Shows as Offline

**Troubleshooting steps:**

1. Verify network connectivity:
```bash
ping <printer-ip>
```

2. Check printer status on its web interface (if available)

3. Restart the printer

4. Check CloudPrintd logs:
```bash
grep -i "printer.*error" /home/CloudPrintd/logs/CloudPrintd.log
```

5. Remove and re-add the printer in the dashboard

#### Print Jobs Not Printing

**Debugging:**

1. Check API response:
```bash
curl -X POST http://localhost:8000/api/v1/print \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"printer":"test","content":"^XA^FDTest^FS^XZ","format":"zpl"}' \
  -v
```

2. Verify ZPL syntax (for Zebra printers)

3. Check printer queue (for CUPS printers):
```bash
lpstat -p
lpq
```

4. Review job logs:
```bash
grep "job_" /home/CloudPrintd/logs/CloudPrintd.log | tail -20
```

#### CUPS Printer Issues

**Install CUPS if missing:**
```bash
sudo apt install cups
```

**Add user to lpadmin group:**
```bash
sudo usermod -a -G lpadmin CloudPrintd
```

**List CUPS printers:**
```bash
lpstat -p -d
```

**Add printer to CUPS:**
```bash
sudo lpadmin -p officePrinter -v ipp://printer-ip/ipp/print -E
```

**Test CUPS printing:**
```bash
echo "Test" | lp -d officePrinter
```

### Network & Connectivity Issues

#### Can't Access Web Interface

**Checklist:**
- [ ] Service is running: `systemctl status CloudPrintd`
- [ ] Port 8000 is open: `sudo netstat -tlnp | grep 8000`
- [ ] Firewall allows connections
- [ ] Using correct IP address

**Test locally:**
```bash
curl http://localhost:8000/api/v1/health
```

**Test from another device:**
```bash
curl http://<pi-ip>:8000/api/v1/health
```

**Check firewall:**
```bash
sudo ufw status
sudo ufw allow 8000/tcp
```

#### Cloudflare Tunnel Not Working

**Check cloudflared status:**
```bash
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -n 50
```

**Restart tunnel:**
```bash
sudo systemctl restart cloudflared
```

**Verify tunnel configuration:**
```bash
cat ~/.cloudflared/config.yml
```

#### Tailscale Connection Issues

**Check Tailscale status:**
```bash
sudo tailscale status
```

**Restart Tailscale:**
```bash
sudo systemctl restart tailscaled
```

**Re-authenticate:**
```bash
sudo tailscale up
```

### Authentication Issues

#### 401 Unauthorized Error

**Solutions:**

1. Verify token is correct:
```bash
# Check configured tokens
cat /opt/CloudPrintd/config/config.json | grep api_tokens
```

2. Ensure Bearer token format:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

3. Regenerate token if needed (via setup wizard or API)

4. Check token isn't expired (if expiration implemented)

#### 403 Forbidden Error

**Cause:** IP whitelisting is enabled and your IP isn't allowed

**Solutions:**

1. Add your IP to whitelist:
```bash
# Edit config
nano /opt/CloudPrintd/config/config.json

# Add IP to ip_whitelist array
"ip_whitelist": ["13.110.54.0/24", "YOUR_IP"]
```

2. Temporarily disable IP whitelist:
```json
"ip_whitelist_enabled": false
```

3. Restart service:
```bash
sudo systemctl restart CloudPrintd
```

### Update Issues

#### Update Failed

**Check update manager logs:**
```bash
grep -i "update" /home/CloudPrintd/logs/CloudPrintd.log | tail -50
```

**Verify download directory has space:**
```bash
df -h /opt/CloudPrintd/downloads
```

**Manual rollback:**
```bash
cd /opt/CloudPrintd/packages
rm current
ln -s v1.0.0 current  # Replace with previous version
sudo systemctl restart CloudPrintd
```

#### Health Check Fails After Update

**Automatic rollback should trigger, but if manual rollback needed:**

1. Stop service:
```bash
sudo systemctl stop CloudPrintd
```

2. Switch to previous version:
```bash
cd /opt/CloudPrintd/packages
ls -la  # Find previous version
rm current
ln -s <previous-version> current
```

3. Start service:
```bash
sudo systemctl start CloudPrintd
```

#### Package Checksum Mismatch

**Cause:** Downloaded package is corrupted

**Solutions:**

1. Delete corrupted package:
```bash
rm /opt/CloudPrintd/downloads/CloudPrintd-v*.pbpkg
```

2. Try download again through dashboard

3. If persistent, check update server connectivity

### Performance Issues

#### High Memory Usage

**Check memory usage:**
```bash
free -h
ps aux | grep python
```

**Solutions:**
- Restart service: `sudo systemctl restart CloudPrintd`
- Reduce concurrent jobs
- Upgrade to Pi 4 if using Zero 2W

#### Slow Print Job Processing

**Possible causes:**
- Network latency to printer
- Large print content
- Printer processing speed

**Check job timing:**
```bash
grep "job_.*completed" /home/CloudPrintd/logs/CloudPrintd.log | tail -20
```

### Configuration Issues

#### Configuration File Corrupted

**Restore from backup:**
```bash
ls -la /opt/CloudPrintd/backups/
cp /opt/CloudPrintd/backups/latest/config.json /opt/CloudPrintd/config/
sudo systemctl restart CloudPrintd
```

**Reset to defaults:**
```bash
cp /opt/CloudPrintd/packages/current/config/defaults.json /opt/CloudPrintd/config/config.json
# Re-run setup wizard
```

### System Issues

#### Disk Space Full

**Check space:**
```bash
df -h
```

**Clean up:**
```bash
# Old logs
sudo journalctl --vacuum-time=7d

# Old packages
cd /opt/CloudPrintd/packages
ls -la  # Manually remove old versions

# Downloads
rm /opt/CloudPrintd/downloads/*.pbpkg
```

#### Permission Denied Errors

**Fix permissions:**
```bash
sudo chown -R CloudPrintd:CloudPrintd /opt/CloudPrintd
sudo chown -R CloudPrintd:CloudPrintd /home/CloudPrintd
sudo chmod -R 755 /opt/CloudPrintd/packages
sudo chmod -R 644 /opt/CloudPrintd/config/*.json
```

## Diagnostic Commands

**Complete system check:**
```bash
#!/bin/bash
echo "=== CloudPrintd Diagnostic ==="
echo ""
echo "Service Status:"
systemctl status CloudPrintd --no-pager
echo ""
echo "Listening Ports:"
sudo netstat -tlnp | grep 8000
echo ""
echo "Recent Logs:"
sudo journalctl -u CloudPrintd -n 20 --no-pager
echo ""
echo "Disk Space:"
df -h /opt/CloudPrintd
echo ""
echo "Memory:"
free -h
echo ""
echo "Current Version:"
ls -la /opt/CloudPrintd/packages/current
echo ""
echo "Health Check:"
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
```

## Getting Help

If issues persist:

1. **Collect diagnostics:**
```bash
sudo journalctl -u CloudPrintd -n 100 > CloudPrintd-logs.txt
cat /opt/CloudPrintd/config/config.json > config-sanitized.json
# Remove sensitive tokens before sharing
```

2. **Check documentation:**
   - [Setup Guide](setup-guide.md)
   - [API Integration](api-integration.md)

3. **Community support:**
   - GitHub Issues
   - Community forums

4. **Include in support request:**
   - CloudPrintd version
   - Raspberry Pi model
   - OS version: `cat /etc/os-release`
   - Error logs
   - Steps to reproduce
