# CloudPrintd Update Management Guide

## Overview

CloudPrintd uses a package-based update system that allows for:
- Zero-downtime version switching
- Automatic rollback on failure
- Version downgrading
- Multiple installed versions
- Isolated virtual environments per version

## Update Architecture

### Directory Structure

```
/opt/CloudPrintd/
├── packages/
│   ├── current -> v1.2.3/       # Symlink to active version
│   ├── v1.2.3/                  # Active version
│   ├── v1.2.2/                  # Previous version (for rollback)
│   └── v1.1.0/                  # Older version
├── config/                      # Shared configuration
├── downloads/                   # Downloaded packages
└── backups/                     # Configuration backups
```

### Version Switching

Version switching is atomic via symlink swapping:
1. Download and extract new version
2. Set up isolated virtualenv
3. Run pre-upgrade hooks
4. Switch `current` symlink to new version
5. Run post-upgrade hooks
6. Restart service
7. Verify health check
8. Rollback if health check fails

## Using the Update Manager

### Via Web Dashboard

1. Navigate to Dashboard → Updates tab
2. Click "Check for Updates"
3. Review available versions
4. Click "Download & Install" or "Activate"
5. Wait for update to complete
6. Verify version in dashboard

### Via API

**Check current version:**
```bash
curl -X GET http://localhost:8000/api/v1/system/version \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**List available versions:**
```bash
curl -X GET http://localhost:8000/api/v1/system/versions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update to specific version:**
```bash
curl -X POST http://localhost:8000/api/v1/system/update/1.2.3 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Rollback to previous version:**
```bash
curl -X POST http://localhost:8000/api/v1/system/rollback \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Update Settings

### Configuration

Edit `/opt/CloudPrintd/config/update.json`:

```json
{
  "auto_update": false,
  "channel": "stable",
  "check_interval_hours": 24,
  "keep_previous_versions": 2,
  "update_server": "https://updates.CloudPrintd.local"
}
```

**Settings:**
- `auto_update`: Enable automatic updates (not recommended for production)
- `channel`: Release channel - "stable", "beta", or "dev"
- `check_interval_hours`: How often to check for updates (1-168 hours)
- `keep_previous_versions`: Number of old versions to keep (1-5)
- `update_server`: URL of your update server

### Release Channels

**Stable (Recommended for Production):**
- Thoroughly tested releases
- Less frequent updates
- Production-ready

**Beta:**
- Pre-release testing
- More frequent updates
- Generally stable but not fully tested

**Dev:**
- Development builds
- Daily or more frequent updates
- May contain bugs
- For testing only

## Manual Updates

### Download and Install Package

1. Download `.pbpkg` file to server
2. Extract and install:

```bash
cd /opt/CloudPrintd/downloads
wget https://updates.CloudPrintd.local/downloads/CloudPrintd-v1.2.3.pbpkg

# Install via API or manually:
cd /opt/CloudPrintd/packages
tar -xzf ../downloads/CloudPrintd-v1.2.3.pbpkg
mv CloudPrintd-v1.2.3 v1.2.3

# Set up virtualenv
cd v1.2.3
python3 -m venv venv
source venv/bin/activate
pip install -r app/requirements.txt

# Activate version
rm /opt/CloudPrintd/packages/current
ln -s /opt/CloudPrintd/packages/v1.2.3 /opt/CloudPrintd/packages/current
sudo systemctl restart CloudPrintd
```

### Verify Installation

```bash
# Check version
curl http://localhost:8000/api/v1/system/version

# Check health
curl http://localhost:8000/api/v1/health

# Check logs
sudo journalctl -u CloudPrintd -n 50
```

## Version Rollback

### Automatic Rollback

CloudPrintd automatically rolls back if:
- Health check fails after activation
- Service fails to start
- Post-upgrade hook fails

### Manual Rollback

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/system/rollback \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Via Command Line:**
```bash
# Stop service
sudo systemctl stop CloudPrintd

# List installed versions
ls -la /opt/CloudPrintd/packages/

# Switch to previous version
cd /opt/CloudPrintd/packages
rm current
ln -s v1.2.2 current  # Replace with desired version

# Start service
sudo systemctl start CloudPrintd

# Verify
curl http://localhost:8000/api/v1/health
```

## Building Custom Releases

### Build Script

Use the provided build script:

```bash
./build-release.sh 1.2.3 stable
```

**Output:**
- `CloudPrintd-v1.2.3.pbpkg` - Package tarball
- Manifest with checksums
- Build information

### Package Contents

A `.pbpkg` package contains:
- `app/` - Python application
- `webui/dist/` - Built frontend
- `migrations/` - Database/config migrations
- `hooks/` - Lifecycle scripts
- `config/` - Default configurations
- `manifest.json` - Version metadata and checksums
- `CHANGELOG.md` - Version changelog

### Manifest.json

```json
{
  "version": "1.2.3",
  "channel": "stable",
  "release_date": "2026-02-10T15:30:00Z",
  "build_date": "2026-02-10T15:30:00Z",
  "checksums": {
    "app/main.py": "abc123...",
    "app/models.py": "def456..."
  }
}
```

## Self-Hosted Update Server

### Simple Node.js Server

Create a simple Express server to host packages:

```javascript
const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;

// Serve static files (packages)
app.use('/downloads', express.static('packages'));

// Serve changelogs
app.use('/changelogs', express.static('changelogs'));

// Load manifest
const manifest = JSON.parse(fs.readFileSync('manifest.json'));

// Check for updates
app.get('/api/v1/updates', (req, res) => {
  const { current_version, channel } = req.query;
  
  const versions = manifest.versions.filter(v => v.channel === channel);
  const latest = versions[0]; // Assuming sorted
  
  if (latest.version !== current_version) {
    res.json({
      update_available: true,
      latest_version: latest
    });
  } else {
    res.json({ update_available: false });
  }
});

// List all versions
app.get('/api/v1/versions', (req, res) => {
  const { channel } = req.query;
  const versions = manifest.versions.filter(v => v.channel === channel);
  res.json({ versions });
});

// Get package info
app.get('/api/v1/package/:version', (req, res) => {
  const version = manifest.versions.find(v => v.version === req.params.version);
  if (version) {
    res.json(version);
  } else {
    res.status(404).json({ error: 'Version not found' });
  }
});

// Get changelog
app.get('/api/v1/changelog/:version', (req, res) => {
  const file = path.join(__dirname, 'changelogs', `${req.params.version}.md`);
  if (fs.existsSync(file)) {
    res.type('text/markdown').send(fs.readFileSync(file, 'utf8'));
  } else {
    res.status(404).send('Changelog not found');
  }
});

app.listen(PORT, () => {
  console.log(`Update server running on port ${PORT}`);
});
```

### Manifest Structure

`manifest.json`:
```json
{
  "versions": [
    {
      "version": "1.2.3",
      "channel": "stable",
      "release_date": "2026-02-10T15:30:00Z",
      "size_bytes": 15728640,
      "checksum": "abc123...",
      "download_url": "/downloads/CloudPrintd-v1.2.3.pbpkg"
    },
    {
      "version": "1.2.2",
      "channel": "stable",
      "release_date": "2026-02-01T12:00:00Z",
      "size_bytes": 15700000,
      "checksum": "def456...",
      "download_url": "/downloads/CloudPrintd-v1.2.2.pbpkg"
    }
  ]
}
```

### Hosting Options

1. **Self-hosted VPS:**
   - Simple Node.js or Python server
   - Nginx for static file serving
   - SSL with Let's Encrypt

2. **GitHub Releases:**
   - Host packages as release assets
   - Use GitHub API as update server
   - Free and reliable

3. **Cloud Storage:**
   - S3, Azure Blob, Google Cloud Storage
   - CloudFront/CDN for distribution
   - Scalable and fast

## Lifecycle Hooks

### Available Hooks

- `pre-install.sh` - Before first installation
- `post-install.sh` - After first installation
- `pre-upgrade.sh` - Before version upgrade
- `post-upgrade.sh` - After version upgrade
- `rollback.sh` - During rollback

### Hook Environment

Hooks run with:
- Working directory: Version directory
- User: `CloudPrintd`
- Exit code 0 = success, non-zero = failure

### Example Hook

```bash
#!/bin/bash
# pre-upgrade.sh
set -e

echo "Backing up configuration..."
BACKUP_DIR="../../backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp ../../config/*.json "$BACKUP_DIR/"
echo "Backup complete: $BACKUP_DIR"

exit 0
```

## Best Practices

### Pre-Update Checklist

- [ ] Verify current version: `curl localhost:8000/api/v1/system/version`
- [ ] Check system health: `curl localhost:8000/api/v1/health`
- [ ] Backup configuration: `cp /opt/CloudPrintd/config/*.json ~/backup/`
- [ ] Review changelog for breaking changes
- [ ] Test update in development environment first
- [ ] Schedule update during low-traffic period
- [ ] Notify users of planned maintenance

### Update Strategy

**For Production:**
1. Test update on staging environment
2. Backup current configuration
3. Schedule maintenance window
4. Update during low-traffic hours
5. Monitor logs after update
6. Verify all printers are online
7. Test print jobs
8. Keep previous version for 24-48 hours before cleanup

**For Development:**
- Enable auto-update
- Use dev channel
- Update frequently

### Rollback Strategy

- Keep at least 2 previous versions installed
- Test rollback procedure in dev environment
- Document rollback commands
- Monitor health checks closely after updates
- Have rollback plan ready before updating

## Troubleshooting Updates

### Update Fails to Download

**Check:**
- Update server connectivity
- Disk space in `/opt/CloudPrintd/downloads`
- Network firewall rules

### Checksum Mismatch

**Cause:** Corrupted download

**Solution:**
- Delete package and retry
- Check network stability
- Verify update server

### Service Won't Start After Update

**Automatic rollback should trigger, but manually:**
```bash
sudo systemctl stop CloudPrintd
cd /opt/CloudPrintd/packages
rm current
ln -s <previous-version> current
sudo systemctl start CloudPrintd
```

### Update Stuck in Progress

**Check:**
```bash
ps aux | grep python
sudo journalctl -u CloudPrintd -f
```

**Force restart:**
```bash
sudo systemctl restart CloudPrintd
```

## Monitoring Updates

### Log Files

- Service logs: `/home/CloudPrintd/logs/CloudPrintd.log`
- System logs: `journalctl -u CloudPrintd`
- Update logs: Check for "update" keyword in logs

### Health Monitoring

After update, monitor:
- Health endpoint: `/api/v1/health`
- Printer status: `/api/v1/printers`
- Print job success rate: `/api/v1/stats`
- Service uptime
- Error logs

## Version Pinning

To prevent automatic updates to a specific version:

```json
{
  "auto_update": false,
  "pinned_version": "1.2.3"
}
```

## Security Considerations

1. **Checksum Verification:**
   - All packages are SHA256 verified
   - Never skip checksum verification

2. **Update Server Security:**
   - Use HTTPS for update server
   - Implement authentication if needed
   - Keep update server secure

3. **Package Signing:**
   - Consider GPG signing packages
   - Verify signatures before installation

4. **Configuration Security:**
   - Backup before updates
   - Never commit tokens to version control
   - Rotate API tokens after suspicious activity

## Examples

### Automated Update Script

```bash
#!/bin/bash
# Auto-update script with safety checks

TOKEN="your-api-token"
API_URL="http://localhost:8000/api/v1"

# Check for updates
UPDATE_INFO=$(curl -s -X GET "$API_URL/system/version" \
  -H "Authorization: Bearer $TOKEN")

if echo "$UPDATE_INFO" | grep -q "update_available"; then
  echo "Update available, starting update..."
  
  # Backup configuration
  cp /opt/CloudPrintd/config/config.json ~/backup-$(date +%Y%m%d).json
  
  # Start update
  curl -X POST "$API_URL/system/update/latest" \
    -H "Authorization: Bearer $TOKEN"
  
  # Wait for update
  sleep 60
  
  # Verify health
  if curl -f "$API_URL/health" > /dev/null 2>&1; then
    echo "Update successful"
  else
    echo "Update failed, rolling back"
    curl -X POST "$API_URL/system/rollback" \
      -H "Authorization: Bearer $TOKEN"
  fi
else
  echo "No updates available"
fi
```

## Support

For update-related issues:
- Check [Troubleshooting Guide](troubleshooting.md)
- Review update logs
- Test in development first
- Contact support with version info and logs
