#!/bin/bash
# Pre-upgrade Hook
# Runs before upgrading to a new version

set -e

echo "Running pre-upgrade tasks..."

# Backup current configuration
BACKUP_DIR="../../backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "../../config/config.json" ]; then
    cp ../../config/config.json "$BACKUP_DIR/"
    echo "✓ Backed up config.json"
fi

if [ -f "../../config/printers.json" ]; then
    cp ../../config/printers.json "$BACKUP_DIR/"
    echo "✓ Backed up printers.json"
fi

if [ -f "../../config/update.json" ]; then
    cp ../../config/update.json "$BACKUP_DIR/"
    echo "✓ Backed up update.json"
fi

echo "✓ Configuration backed up to $BACKUP_DIR"

# Stop the service gracefully (if running)
if systemctl is-active --quiet CloudPrintd 2>/dev/null; then
    echo "Stopping CloudPrintd service..."
    systemctl stop CloudPrintd || true
    echo "✓ Service stopped"
fi

echo "Pre-upgrade tasks complete"
exit 0
