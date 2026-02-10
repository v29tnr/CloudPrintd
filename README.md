# CloudPrintd

**A self-hosted print server for Raspberry Pi that bridges Salesforce cloud to on-site printers**

CloudPrintd is a cost-effective alternative to paid SaaS print services like PrintNode. It provides enterprise-grade printing capabilities with zero monthly fees, complete data privacy, and flexible deployment options.

## Features

- 🖨️ **Multi-Printer Support:** Zebra ZPL thermal printers (raw TCP) and CUPS-compatible printers
- 🔒 **Secure API:** Bearer token authentication with optional IP whitelisting
- 🌐 **Flexible Connectivity:** Cloudflare Tunnel, Tailscale, DDNS, relay server, or static IP
- 🎨 **Web-Based Setup:** 5-step wizard to get running in 5 minutes
- 📦 **Package Management:** Install, upgrade, downgrade, and rollback versions with atomic updates
- 🔄 **Auto-Discovery:** Scan your network for Zebra printers automatically
- 📊 **Dashboard:** Monitor printer status, job history, and system health
- 🔧 **Zero-Downtime Updates:** Automatic rollback on failure with health checks
- 📱 **Salesforce Integration:** Complete API with Apex code examples

## Quick Start

### 1. Test Your Setup
```bash
python test-setup.py
```

### 2. Run Development Server
```bash
# Backend (Terminal 1)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd webui && npm install && npm run dev
```

### 3. Access Setup Wizard
Open http://localhost:8000/setup and follow the 5-step wizard.

### 4. Production Deployment
See [docs/setup-guide.md](docs/setup-guide.md) for complete Raspberry Pi deployment instructions.

## Documentation

| Document | Description |
|----------|-------------|
| [QUICK-REFERENCE.md](QUICK-REFERENCE.md) | Quick commands and API reference card |
| [PROJECT-SUMMARY.md](PROJECT-SUMMARY.md) | Complete project overview and architecture |
| [docs/setup-guide.md](docs/setup-guide.md) | 5-minute Raspberry Pi deployment guide |
| [docs/api-integration.md](docs/api-integration.md) | Salesforce integration with Apex examples |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues and solutions |
| [docs/update-management.md](docs/update-management.md) | Package build and update system guide |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Architecture

```
CloudPrintd
├── app/                    # FastAPI backend
│   ├── main.py            # API endpoints (print, printers, setup, system)
│   ├── models.py          # Pydantic models
│   ├── config.py          # Configuration manager
│   ├── security.py        # Authentication & IP whitelisting
│   └── printer.py         # Printer communication (ZPL/CUPS)
├── webui/                 # React frontend
│   ├── components/        # Setup wizard & dashboard
│   └── api.js            # API client
├── update_manager/        # Package management
│   └── manager.py        # Version control & rollback
├── update-server/         # Optional update hosting
│   └── server.js         # Express server for packages
├── config/               # Configuration files
├── docs/                 # Documentation
└── hooks/                # Lifecycle hooks
```

## Key Components

### Print Service (app/)
- **FastAPI backend** with async printer communication
- **Zebra ZPL:** Direct TCP connection to port 9100
- **CUPS integration:** Standard printer support via python-cups
- **Auto-discovery:** Parallel network scanning for Zebra printers
- **Job history:** Track print jobs, success/failure, and timestamps

### Update System (update_manager/)
- **Package format:** .pbpkg (tar.gz with manifest and checksums)
- **Atomic updates:** Symlink swapping with automatic rollback
- **Health checks:** Verify service after updates
- **Lifecycle hooks:** Pre/post install/upgrade and rollback scripts
- **Version retention:** Keep multiple versions for downgrade

### Web Interface (webui/)
- **Setup wizard:** 5 steps (Welcome → Connectivity → Printers → API → Complete)
- **Dashboard:** System overview, printer status, and update management
- **Update UI:** Check for updates, upgrade/downgrade, view changelogs

### Update Server (update-server/)
- **Version management:** Host packages and serve update manifests
- **Changelog API:** Deliver version-specific release notes
- **Package downloads:** Secure distribution with SHA256 verification

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/printers` | GET | List configured printers |
| `/api/v1/printers` | POST | Add printer |
| `/api/v1/discover` | POST | Discover Zebra printers |
| `/api/v1/print` | POST | Submit print job |
| `/api/v1/setup/token` | POST | Generate API token |
| `/api/v1/setup/complete` | POST | Complete setup |
| `/api/v1/system/version` | GET | Current version info |
| `/api/v1/system/versions` | GET | Available versions |
| `/api/v1/system/update/{version}` | POST | Install version |
| `/api/v1/system/rollback` | POST | Rollback to previous |

See [QUICK-REFERENCE.md](QUICK-REFERENCE.md) for curl examples.

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI 0.109.0** - Modern async web framework
- **Uvicorn 0.27.0** - ASGI server
- **Pydantic 2.6.0** - Data validation
- **pycups 2.0.1** - CUPS integration
- **httpx 0.26.0** - Async HTTP client

### Frontend
- **React 18.2.0**
- **Vite 5.0.8** - Build tool
- **Axios 1.6.2** - HTTP client

### Update Server
- **Node.js 18+**
- **Express 4.18.2**

### Deployment
- **Systemd** - Service management
- **Raspberry Pi OS Lite (64-bit)** - Debian-based Linux (64-bit recommended, 32-bit also supported)

## Configuration

Configuration files are in `/opt/CloudPrintd/config/` (production) or `config/` (development):

- **config.json:** Server settings, API tokens, IP whitelist
- **printers.json:** Printer definitions and configurations
- **update.json:** Update server URL, channel, auto-update settings

## Testing

### Test API
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Generate token (during setup)
curl -X POST http://localhost:8000/api/v1/setup/token

# List printers
curl http://localhost:8000/api/v1/printers \
  -H "Authorization: Bearer YOUR_TOKEN"

# Submit test print
curl -X POST http://localhost:8000/api/v1/print \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "printer": "zebra_test",
    "content": "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ",
    "format": "zpl"
  }'
```

### Test Printer Directly
```bash
# Zebra ZPL printer on 192.168.1.100
echo "^XA^FO50,50^A0N,50,50^FDDirect Test^FS^XZ" | nc 192.168.1.100 9100
```

## Build & Release

### Build Package
```bash
./build-release.sh 1.0.0 stable
```

This creates `CloudPrintd-v1.0.0.pbpkg` with:
- Application code (app/, webui/)
- Configuration files
- Lifecycle hooks
- SHA256 checksums
- Manifest with version metadata

### Host Update Server
```bash
cd update-server
npm install
npm start  # Runs on port 3000
```

See [docs/update-management.md](docs/update-management.md) for details.

## Raspberry Pi Deployment

**Recommended Hardware:**
- **Raspberry Pi 4** (2GB+ RAM) for production
- **Raspberry Pi Zero 2W** (512MB RAM) for testing/light use (see [Pi Zero 2W Setup Guide](docs/pi-zero-2w-setup.md))
- **MicroSD card** (16GB+ Class 10)
- **OS:** Raspberry Pi OS Lite 64-bit (32-bit also works, but 64-bit recommended)

**Quick Deploy:**
```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-venv python3-pip cups libcups2-dev nodejs npm

# Create user
sudo useradd -r -s /bin/bash -d /home/CloudPrintd -m CloudPrintd

# Deploy application
sudo mkdir -p /opt/CloudPrintd
sudo cp -r . /opt/CloudPrintd/packages/v1.0.0
sudo ln -s v1.0.0 /opt/CloudPrintd/packages/current

# Create virtualenv and install
cd /opt/CloudPrintd/packages/current
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd webui
npm install
npm run build

# Install service
sudo cp CloudPrintd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable CloudPrintd
sudo systemctl start CloudPrintd
```

Full deployment guide: [docs/setup-guide.md](docs/setup-guide.md)

## Salesforce Integration

### Setup Named Credential
1. **Setup → Named Credentials → New**
2. **Label:** `CloudPrintd_Server`
3. **URL:** Your CloudPrintd URL (e.g., `https://CloudPrintd.example.com`)
4. **Authentication:** Password Authentication
5. **Username:** `api`
6. **Password:** Your API token from setup

### Apex Example
```apex
public class ShippingLabelPrinter {
    public static void printShippingLabel(String orderId) {
        // Generate ZPL content
        String zplContent = generateZPL(orderId);
        
        // Print via CloudPrintd
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:CloudPrintd_Server/api/v1/print');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{
            'printer' => 'warehouse_zebra',
            'content' => zplContent,
            'format' => 'zpl',
            'copies' => 1
        }));
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() == 200) {
            System.debug('Label printed successfully');
        } else {
            System.debug('Print failed: ' + res.getBody());
        }
    }
    
    private static String generateZPL(String orderId) {
        // Fetch order data and generate ZPL
        // ...
        return '^XA^FO50,50^A0N,50,50^FDOrder: ' + orderId + '^FS^XZ';
    }
}
```

Complete integration guide: [docs/api-integration.md](docs/api-integration.md)

## Connectivity Options

CloudPrintd supports multiple ways to connect Salesforce to your on-premise server:

### 1. Cloudflare Tunnel (Recommended)
- ✓ Free, secure tunnel
- ✓ No port forwarding required
- ✓ Automatic HTTPS with cert
- ✓ DDoS protection

### 2. Tailscale
- ✓ Zero-config VPN mesh network
- ✓ No exposed ports
- ✓ Point-to-point encryption

### 3. Dynamic DNS
- ✓ Use your own domain
- ✓ Router port forwarding
- ⚠ Requires HTTPS cert (Let's Encrypt)

### 4. Relay Server
- ✓ Intermediate server in cloud
- ✓ No local network changes
- ⚠ Additional hosting cost

### 5. Static IP
- ✓ Direct connection
- ⚠ Requires static IP from ISP
- ⚠ Port forwarding needed

Setup instructions: [docs/setup-guide.md](docs/setup-guide.md#connectivity-options)

## Security

- **Bearer Token Authentication:** All API endpoints require valid token
- **IP Whitelisting:** Optional restriction to Salesforce IP ranges
- **HTTPS:** Recommended for production (via Cloudflare or Let's Encrypt)
- **Systemd Hardening:** NoNewPrivileges, PrivateTmp, ProtectSystem
- **No Default Tokens:** Token generated during setup only
- **Config Backups:** Automatic backup before updates

## Troubleshooting

**Service won't start:**
```bash
sudo journalctl -u CloudPrintd -n 50
```

**Printer not responding:**
```bash
nc -zv 192.168.1.100 9100  # Test connectivity
```

**API returns 401:**
```bash
# Check token
cat /opt/CloudPrintd/config/config.json | grep api_tokens
```

**Rollback update:**
```bash
curl -X POST http://localhost:8000/api/v1/system/rollback \
  -H "Authorization: Bearer TOKEN"
```

See [docs/troubleshooting.md](docs/troubleshooting.md) for comprehensive troubleshooting.

## License

This project is provided as-is without warranty. See LICENSE file for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Support

- **Documentation:** [docs/](docs/)
- **API Docs:** http://localhost:8000/docs (interactive)
- **Quick Reference:** [QUICK-REFERENCE.md](QUICK-REFERENCE.md)

---

**CloudPrintd** - Self-hosted printing for Salesforce. No subscriptions, no limits, complete control.
