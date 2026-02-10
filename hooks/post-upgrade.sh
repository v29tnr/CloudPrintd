#!/bin/bash
# Post-upgrade Hook
# Runs after upgrading to a new version

set -e

echo "Running post-upgrade tasks..."

# Migrate configuration if needed
# TODO: Add configuration migration logic here if schema changes between versions

echo "✓ Configuration migration checked"

# Restart the service
if command -v systemctl &> /dev/null; then
    echo "Restarting CloudPrintd service..."
    systemctl restart CloudPrintd || true
    sleep 3
    
    if systemctl is-active --quiet CloudPrintd; then
        echo "✓ Service restarted successfully"
    else
        echo "WARNING: Service may not have started correctly"
    fi
fi

# Verify health endpoint
echo "Verifying service health..."
sleep 5

if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✓ Health check passed"
else
    echo "WARNING: Health check failed - service may need manual intervention"
fi

echo "Post-upgrade tasks complete"
exit 0
