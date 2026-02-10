#!/bin/bash
# Pre-install Hook
# Runs before package installation

set -e

echo "Running pre-install checks..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "ERROR: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python version check passed ($PYTHON_VERSION)"

# Check disk space (require at least 500MB free)
AVAILABLE_SPACE=$(df -BM . | awk 'NR==2 {print $4}' | sed 's/M//')

if [ "$AVAILABLE_SPACE" -lt 500 ]; then
    echo "ERROR: Insufficient disk space (need 500MB, have ${AVAILABLE_SPACE}MB)"
    exit 1
fi

echo "✓ Disk space check passed (${AVAILABLE_SPACE}MB available)"

# Check if CUPS is available (optional, just warn)
if ! command -v cupsd &> /dev/null; then
    echo "WARNING: CUPS not found - CUPS printer support will be unavailable"
else
    echo "✓ CUPS found"
fi

# Check network connectivity (optional)
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    echo "WARNING: No internet connectivity detected"
else
    echo "✓ Network connectivity check passed"
fi

echo "Pre-install checks complete"
exit 0
