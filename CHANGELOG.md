# CloudPrintd Changelog

All notable changes to CloudPrintd will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Additional printer types support
- Advanced scheduling features
- Print job queue management

## [1.0.0] - 2026-02-10

### Added
- Initial release of CloudPrintd
- FastAPI-based REST API for print job submission
- Support for Zebra ZPL thermal printers via raw TCP (port 9100)
- Support for CUPS-compatible printers (laser, inkjet, etc.)
- Network printer discovery for Zebra printers
- Web-based setup wizard with step-by-step guidance
- Multiple connectivity options:
  - Cloudflare Tunnel integration
  - Tailscale VPN support
  - Dynamic DNS + port forwarding
  - Cloud relay support
  - Local network mode
- API token-based authentication
- Optional IP whitelisting for enhanced security
- Package-based update system with:
  - Zero-downtime version switching
  - Automatic rollback on failure
  - Multiple simultaneous installed versions
  - Isolated virtual environments per version
- Update management dashboard
- Version upgrade/downgrade capabilities
- Comprehensive API documentation (auto-generated)
- Health check endpoint for monitoring
- Print job statistics and monitoring
- Systemd service integration
- Lifecycle hooks for install/upgrade/rollback operations
- Configuration management system
- Backup and restore functionality
- Responsive React-based web UI
- Real-time printer status monitoring
- Comprehensive logging with rotation
- UK English localisation throughout

### API Endpoints
- `POST /api/v1/print` - Submit print job
- `GET /api/v1/printers` - List configured printers
- `POST /api/v1/printers` - Add printer
- `DELETE /api/v1/printers/{id}` - Remove printer
- `POST /api/v1/discover` - Network printer discovery
- `GET /api/v1/health` - Health check
- `GET /api/v1/stats` - Print statistics
- `POST /api/v1/setup/token` - Generate API token
- `POST /api/v1/setup/complete` - Complete setup
- `GET /api/v1/setup/status` - Check setup status
- `GET /api/v1/system/version` - Get version info
- `GET /api/v1/system/versions` - List all versions
- `POST /api/v1/system/update/{version}` - Update to version
- `POST /api/v1/system/rollback` - Rollback to previous
- `GET /api/v1/system/changelog/{version}` - Get changelog
- `GET /api/v1/system/update-config` - Get update settings
- `PUT /api/v1/system/update-config` - Update settings

### Security
- Bearer token authentication for all API endpoints
- SHA256 checksum verification for packages
- Secure configuration file handling
- Systemd security hardening
- IP whitelisting support
- Token rotation capability

### Documentation
- Complete setup guide with 5-minute quickstart
- Salesforce integration guide with Apex examples
- Comprehensive troubleshooting guide
- Update management documentation
- API reference documentation

### Supported Platforms
- Raspberry Pi Zero 2W (512MB RAM) - tested
- Raspberry Pi 4 (2GB+ RAM) - recommended
- Raspberry Pi OS Lite (Debian-based)
- Python 3.11+

### Dependencies
- FastAPI 0.109.0
- Uvicorn 0.27.0
- Pydantic 2.6.0
- pycups 2.0.1
- httpx 0.26.0
- React 18.2.0
- Node.js (for frontend build)

### Known Limitations
- Maximum 100 print jobs per minute recommended
- Memory limit of 512MB (configurable)
- CUPS support requires manual installation on minimal systems
- Update server must be configured separately

### Notes
- First production-ready release
- Designed as cost-effective alternative to PrintNode
- Optimised for Salesforce integration
- Self-hosted solution with no recurring fees
- Package-based architecture for easy updates
- Zero-downtime update capability

### Breaking Changes
- None (initial release)

### Migration Guide
- None (initial release)

### Contributors
- Initial development team

### Security Advisories
- None

---

## Version Format

- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality additions
- PATCH version for backwards-compatible bug fixes

## Support

For issues and feature requests, please visit:
- GitHub Issues: https://github.com/yourorg/CloudPrintd/issues
- Documentation: https://docs.CloudPrintd.local
