#!/bin/bash
# Post-install Hook
# Runs after package installation

set -e

echo "Running post-install tasks..."

# Set proper permissions
chmod -R 755 app/
chmod -R 755 update_manager/
chmod 644 config/*.json

echo "✓ File permissions set"

# Create log directory if it doesn't exist
mkdir -p ../../logs
chmod 755 ../../logs

echo "✓ Log directory created"

# If this is a first-time install, provide helpful information
if [ ! -f "../../config/config.json" ]; then
    echo ""
    echo "========================================="
    echo "First-time Installation Detected"
    echo "========================================="
    echo "Next steps:"
    echo "1. Start the CloudPrintd service"
    echo "2. Access the setup wizard at http://localhost:8000/setup"
    echo "3. Follow the guided setup process"
    echo ""
fi

echo "Post-install tasks complete"
exit 0
