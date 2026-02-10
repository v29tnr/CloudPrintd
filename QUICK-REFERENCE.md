# CloudPrintd Quick Reference

## Quick Start Commands

### Development
```bash
# Backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd webui && npm run dev
```

### Test Setup
```bash
python test-setup.py
```

## API Quick Reference

### Authentication
All requests (except setup endpoints) require:
```bash
-H "Authorization: Bearer YOUR_TOKEN"
```

### Essential Endpoints

**Health Check:**
```bash
curl http://localhost:8000/api/v1/health
```

**Generate Token (during setup):**
```bash
curl -X POST http://localhost:8000/api/v1/setup/token
```

**List Printers:**
```bash
curl http://localhost:8000/api/v1/printers \
  -H "Authorization: Bearer TOKEN"
```

**Submit Print Job:**
```bash
curl -X POST http://localhost:8000/api/v1/print \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "printer": "zebra_warehouse",
    "content": "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ",
    "format": "zpl",
    "copies": 1
  }'
```

**Discover Printers:**
```bash
curl -X POST http://localhost:8000/api/v1/discover?ip_range=192.168.1.0/24 \
  -H "Authorization: Bearer TOKEN"
```

**Add Printer:**
```bash
curl -X POST http://localhost:8000/api/v1/printers \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "warehouse_zebra",
    "config": {
      "type": "zebra_raw",
      "display_name": "Warehouse Zebra ZT411",
      "ip": "192.168.1.100",
      "port": 9100,
      "location": "Warehouse Bay 3"
    }
  }'
```

**Check for Updates:**
```bash
curl http://localhost:8000/api/v1/system/version \
  -H "Authorization: Bearer TOKEN"
```

**List Available Versions:**
```bash
curl http://localhost:8000/api/v1/system/versions \
  -H "Authorization: Bearer TOKEN"
```

**Update to Version:**
```bash
curl -X POST http://localhost:8000/api/v1/system/update/1.2.3 \
  -H "Authorization: Bearer TOKEN"
```

**Rollback:**
```bash
curl -X POST http://localhost:8000/api/v1/system/rollback \
  -H "Authorization: Bearer TOKEN"
```

## System Commands

### Service Management (Raspberry Pi)
```bash
# Status
sudo systemctl status CloudPrintd

# Start
sudo systemctl start CloudPrintd

# Stop
sudo systemctl stop CloudPrintd

# Restart
sudo systemctl restart CloudPrintd

# Enable on boot
sudo systemctl enable CloudPrintd

# View logs
sudo journalctl -u CloudPrintd -f
```

### File Locations
```
/opt/CloudPrintd/               # Installation directory
├── packages/current/           # Active version
├── config/                     # Configuration files
├── downloads/                  # Downloaded packages
└── backups/                    # Configuration backups

/home/CloudPrintd/
├── logs/                       # Application logs
└── data/                       # Application data
```

### Configuration Files
```bash
# Main config
nano /opt/CloudPrintd/config/config.json

# Printers
nano /opt/CloudPrintd/config/printers.json

# Update settings
nano /opt/CloudPrintd/config/update.json
```

### Log Files
```bash
# Application logs
tail -f /home/CloudPrintd/logs/CloudPrintd.log
tail -f /home/CloudPrintd/logs/CloudPrintd-error.log

# System logs
sudo journalctl -u CloudPrintd -f
sudo journalctl -u CloudPrintd -n 100 --no-pager
```

## Troubleshooting Quick Reference

### Service Won't Start
```bash
# Check logs
sudo journalctl -u CloudPrintd -n 50

# Check port
sudo netstat -tlnp | grep 8000

# Test manually
sudo -u CloudPrintd /opt/CloudPrintd/packages/current/venv/bin/python \
  -m uvicorn app.main:app
```

### Printer Not Found
```bash
# Ping printer
ping 192.168.1.100

# Test port
nc -zv 192.168.1.100 9100

# Test ZPL
echo "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ" | nc 192.168.1.100 9100
```

### API Returns 401
```bash
# Check token in config
cat /opt/CloudPrintd/config/config.json | grep api_tokens

# Regenerate token via setup wizard or:
curl -X POST http://localhost:8000/api/v1/setup/token
```

### Rollback Update
```bash
# Via API
curl -X POST http://localhost:8000/api/v1/system/rollback \
  -H "Authorization: Bearer TOKEN"

# Or manually
sudo systemctl stop CloudPrintd
cd /opt/CloudPrintd/packages
rm current
ln -s v1.0.0 current  # Replace with previous version
sudo systemctl start CloudPrintd
```

## Salesforce Integration Quick Reference

### Named Credential Setup
1. Setup → Named Credentials → New
2. Label: `CloudPrintd_Server`
3. URL: Your CloudPrintd URL
4. Authentication: Password Authentication
5. Username: `api`
6. Password: Your API token

### Apex Example
```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:CloudPrintd_Server/api/v1/print');
req.setMethod('POST');
req.setHeader('Content-Type', 'application/json');
req.setBody(JSON.serialize(new Map<String, Object>{
    'printer' => 'warehouse_zebra',
    'content' => '^XA^FO50,50^A0N,50,50^FDLabel^FS^XZ',
    'format' => 'zpl'
}));

Http http = new Http();
HttpResponse res = http.send(req);
```

## ZPL Quick Reference

### Basic Label
```zpl
^XA
^FO50,50^A0N,50,50^FDHello World^FS
^XZ
```

### Label with Barcode
```zpl
^XA
^FO50,50^A0N,30,30^FDProduct Name^FS
^FO50,100^BY2^BCN,70,Y,N,N^FD123456789^FS
^XZ
```

### Commands
- `^XA` - Start label
- `^XZ` - End label
- `^FO` - Field origin (position)
- `^A0` - Font
- `^FD` - Field data
- `^FS` - Field separator
- `^BY` - Barcode parameters
- `^BC` - Code 128 barcode

## Build & Release

### Build Release
```bash
./build-release.sh 1.0.0 stable
```

### Deploy Package
```bash
# Copy to update server
cp CloudPrintd-v1.0.0.pbpkg update-server/packages/

# Update manifest
nano update-server/manifest.json

# Reload manifest
curl -X POST http://localhost:3000/api/v1/reload
```

## URLs

- **API Documentation:** http://localhost:8000/docs
- **Setup Wizard:** http://localhost:8000/setup
- **Dashboard:** http://localhost:8000/
- **Update Server:** http://localhost:3000/

## Important Notes

- Always backup config before updates
- Keep at least 2 previous versions
- Test updates in dev environment first
- Monitor logs after updates
- Health checks run automatically after updates
- Automatic rollback on health check failure

## Support

- Documentation: [docs/](docs/)
- Project Summary: [PROJECT-SUMMARY.md](PROJECT-SUMMARY.md)
- Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)
