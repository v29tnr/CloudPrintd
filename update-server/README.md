# CloudPrintd Update Server

Simple Node.js server for hosting CloudPrintd package updates.

## Setup

1. Install dependencies:
```bash
cd update-server
npm install
```

2. Create directories:
```bash
mkdir -p packages changelogs
```

3. Add your package files to `packages/`

4. Add changelog files to `changelogs/` (named like `1.0.0.md`)

5. Update `manifest.json` with version information

6. Start server:
```bash
npm start

# Or for development with auto-reload:
npm run dev
```

## Adding New Versions

1. Build release package:
```bash
cd ..
./build-release.sh 1.2.3 stable
```

2. Copy package to update server:
```bash
cp CloudPrintd-v1.2.3.pbpkg update-server/packages/
```

3. Create changelog:
```bash
# Extract changelog section for this version
cat CHANGELOG.md | sed -n '/## \[1.2.3\]/,/## \[/p' > update-server/changelogs/1.2.3.md
```

4. Add version to manifest.json:
```json
{
  "version": "1.2.3",
  "channel": "stable",
  "release_date": "2026-02-15T10:00:00Z",
  "size_bytes": 16000000,
  "checksum": "sha256-of-package",
  "download_url": "/downloads/CloudPrintd-v1.2.3.pbpkg"
}
```

5. Reload manifest:
```bash
curl -X POST http://localhost:3000/api/v1/reload
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/v1/updates?current_version=1.0.0&channel=stable` - Check for updates
- `GET /api/v1/versions?channel=stable` - List all versions
- `GET /api/v1/package/{version}` - Get package info
- `GET /api/v1/changelog/{version}` - Get changelog
- `GET /downloads/{filename}` - Download package
- `POST /api/v1/reload` - Reload manifest

## Configuration

Set port via environment variable:
```bash
PORT=3001 npm start
```

## Deployment

### Using PM2

```bash
npm install -g pm2
pm2 start server.js --name CloudPrintd-updates
pm2 save
pm2 startup
```

### Using systemd

Create `/etc/systemd/system/CloudPrintd-updates.service`:
```ini
[Unit]
Description=CloudPrintd Update Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/CloudPrintd-updates
ExecStart=/usr/bin/node server.js
Restart=always

[Install]
WantedBy=multi-user.target
```

### Using Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name updates.CloudPrintd.local;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Cache package downloads
    location /downloads/ {
        proxy_pass http://localhost:3000;
        proxy_cache_valid 200 1d;
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

## Security

For production:
1. Add authentication middleware
2. Use HTTPS (Let's Encrypt)
3. Implement rate limiting
4. Add package signature verification
5. Restrict access by IP if possible

## Monitoring

Check server status:
```bash
curl http://localhost:3000/health
```

View logs:
```bash
pm2 logs CloudPrintd-updates
```
