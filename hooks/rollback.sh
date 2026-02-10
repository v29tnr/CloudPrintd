#!/bin/bash
# Rollback Hook
# Runs during version rollback

set -e

echo "Running rollback tasks..."

# Restore backed-up configuration
LATEST_BACKUP=$(ls -td ../../backups/*/ 2>/dev/null | head -1)

if [ -n "$LATEST_BACKUP" ]; then
    echo "Restoring configuration from $LATEST_BACKUP"
    
    if [ -f "$LATEST_BACKUP/config.json" ]; then
        cp "$LATEST_BACKUP/config.json" ../../config/
        echo "✓ Restored config.json"
    fi
    
    if [ -f "$LATEST_BACKUP/printers.json" ]; then
        cp "$LATEST_BACKUP/printers.json" ../../config/
        echo "✓ Restored printers.json"
    fi
    
    if [ -f "$LATEST_BACKUP/update.json" ]; then
        cp "$LATEST_BACKUP/update.json" ../../config/
        echo "✓ Restored update.json"
    fi
else
    echo "WARNING: No backup found to restore"
fi

# Restart service
if command -v systemctl &> /dev/null; then
    echo "Restarting CloudPrintd service..."
    systemctl restart CloudPrintd || true
    echo "✓ Service restarted"
fi

echo "Rollback tasks complete"
exit 0
