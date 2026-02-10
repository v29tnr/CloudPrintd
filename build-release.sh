#!/bin/bash
# Build Release Script for CloudPrintd
# Usage: ./build-release.sh <version> <channel>
# Example: ./build-release.sh 1.0.0 stable

set -e

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <version> <channel>"
    echo "Example: $0 1.0.0 stable"
    exit 1
fi

VERSION=$1
CHANNEL=$2
BUILD_DIR="build/CloudPrintd-v${VERSION}"
PACKAGE_NAME="CloudPrintd-v${VERSION}.pbpkg"

echo "Building CloudPrintd v${VERSION} (${CHANNEL})"

# Clean previous build
rm -rf build
mkdir -p "$BUILD_DIR"

# Create directory structure
mkdir -p "$BUILD_DIR/app"
mkdir -p "$BUILD_DIR/webui/dist"
mkdir -p "$BUILD_DIR/migrations"
mkdir -p "$BUILD_DIR/hooks"
mkdir -p "$BUILD_DIR/config"

echo "Copying application files..."

# Copy Python application
cp -r app/* "$BUILD_DIR/app/"
cp -r update_manager "$BUILD_DIR/"
cp requirements.txt "$BUILD_DIR/app/"

# Copy configuration defaults
cp config/defaults.json "$BUILD_DIR/config/"
cp config/printers.defaults.json "$BUILD_DIR/config/"
cp config/update.json "$BUILD_DIR/config/"

# Build frontend if it exists
if [ -d "webui" ]; then
    echo "Building frontend..."
    cd webui
    npm install
    npm run build
    cd ..
    cp -r webui/dist/* "$BUILD_DIR/webui/dist/"
fi

# Copy hooks
if [ -d "hooks" ]; then
    cp hooks/*.sh "$BUILD_DIR/hooks/" 2>/dev/null || echo "No hooks to copy"
fi

# Copy migrations
if [ -d "migrations" ]; then
    cp migrations/*.sql "$BUILD_DIR/migrations/" 2>/dev/null || echo "No migrations to copy"
fi

# Create changelog
if [ -f "CHANGELOG.md" ]; then
    cp CHANGELOG.md "$BUILD_DIR/"
fi

# Generate manifest.json
echo "Generating manifest..."

cat > "$BUILD_DIR/manifest.json" <<EOF
{
  "version": "${VERSION}",
  "channel": "${CHANNEL}",
  "release_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "checksums": {}
}
EOF

# Calculate checksums for all files
echo "Calculating checksums..."

CHECKSUMS_JSON="{"
FIRST=true

find "$BUILD_DIR" -type f ! -name "manifest.json" | while read -r file; do
    RELATIVE_PATH="${file#$BUILD_DIR/}"
    CHECKSUM=$(sha256sum "$file" | awk '{print $1}')
    
    if [ "$FIRST" = true ]; then
        CHECKSUMS_JSON="${CHECKSUMS_JSON}\"${RELATIVE_PATH}\": \"${CHECKSUM}\""
        FIRST=false
    else
        CHECKSUMS_JSON="${CHECKSUMS_JSON}, \"${RELATIVE_PATH}\": \"${CHECKSUM}\""
    fi
done

CHECKSUMS_JSON="${CHECKSUMS_JSON}}"

# Update manifest with checksums (using Python for JSON manipulation)
python3 << PYTHON
import json

with open('$BUILD_DIR/manifest.json', 'r') as f:
    manifest = json.load(f)

# Calculate checksums
import os
import hashlib

checksums = {}
for root, dirs, files in os.walk('$BUILD_DIR'):
    for file in files:
        if file == 'manifest.json':
            continue
        filepath = os.path.join(root, file)
        relative_path = os.path.relpath(filepath, '$BUILD_DIR')
        
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        checksums[relative_path] = sha256.hexdigest()

manifest['checksums'] = checksums

with open('$BUILD_DIR/manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

print(f"Manifest updated with {len(checksums)} file checksums")
PYTHON

# Create tarball
echo "Creating package..."
cd build
tar -czf "$PACKAGE_NAME" "CloudPrintd-v${VERSION}"
cd ..

# Move to root
mv "build/$PACKAGE_NAME" .

# Calculate package checksum and size
PACKAGE_CHECKSUM=$(sha256sum "$PACKAGE_NAME" | awk '{print $1}')
PACKAGE_SIZE=$(stat -c%s "$PACKAGE_NAME" 2>/dev/null || stat -f%z "$PACKAGE_NAME")

echo ""
echo "========================================="
echo "Build Complete!"
echo "========================================="
echo "Package: $PACKAGE_NAME"
echo "Version: $VERSION"
echo "Channel: $CHANNEL"
echo "Size: $PACKAGE_SIZE bytes ($(echo "scale=2; $PACKAGE_SIZE/1024/1024" | bc) MB)"
echo "SHA256: $PACKAGE_CHECKSUM"
echo ""
echo "Update server manifest entry:"
echo "{"
echo "  \"version\": \"${VERSION}\","
echo "  \"channel\": \"${CHANNEL}\","
echo "  \"release_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
echo "  \"size_bytes\": ${PACKAGE_SIZE},"
echo "  \"checksum\": \"${PACKAGE_CHECKSUM}\","
echo "  \"download_url\": \"/downloads/${PACKAGE_NAME}\""
echo "}"
echo ""

# Clean up build directory
rm -rf build

echo "Build complete! Package: $PACKAGE_NAME"
