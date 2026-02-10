/**
 * Simple Update Server for CloudPrintd
 * Serves package updates and version information
 */

const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Enable CORS
app.use(cors());

// Parse JSON bodies
app.use(express.json());

// Serve static files (packages)
app.use('/downloads', express.static(path.join(__dirname, 'packages')));

// Serve changelogs
app.use('/changelogs', express.static(path.join(__dirname, 'changelogs')));

// Load manifest
let manifest = {};
const manifestPath = path.join(__dirname, 'manifest.json');

function loadManifest() {
  try {
    const data = fs.readFileSync(manifestPath, 'utf8');
    manifest = JSON.parse(data);
    console.log(`Loaded manifest with ${manifest.versions.length} versions`);
  } catch (error) {
    console.error('Failed to load manifest:', error.message);
    manifest = { versions: [] };
  }
}

// Load manifest on startup
loadManifest();

// Reload manifest endpoint (for adding new versions)
app.post('/api/v1/reload', (req, res) => {
  loadManifest();
  res.json({ success: true, message: 'Manifest reloaded' });
});

// Check for updates
app.get('/api/v1/updates', (req, res) => {
  const { current_version, channel = 'stable' } = req.query;
  
  console.log(`Update check: current=${current_version}, channel=${channel}`);
  
  // Filter by channel and sort by version (descending)
  const versions = manifest.versions
    .filter(v => v.channel === channel)
    .sort((a, b) => compareVersions(b.version, a.version));
  
  if (versions.length === 0) {
    return res.json({
      update_available: false,
      message: 'No versions available for this channel'
    });
  }
  
  const latest = versions[0];
  
  if (!current_version || compareVersions(latest.version, current_version) > 0) {
    res.json({
      update_available: true,
      latest_version: latest,
      message: `Update available: ${latest.version}`
    });
  } else {
    res.json({
      update_available: false,
      current_version: latest.version,
      message: 'You are running the latest version'
    });
  }
});

// List all versions for a channel
app.get('/api/v1/versions', (req, res) => {
  const { channel = 'stable' } = req.query;
  
  console.log(`Version list request: channel=${channel}`);
  
  const versions = manifest.versions
    .filter(v => v.channel === channel)
    .sort((a, b) => compareVersions(b.version, a.version));
  
  res.json({ versions });
});

// Get specific package information
app.get('/api/v1/package/:version', (req, res) => {
  const { version } = req.params;
  
  console.log(`Package info request: version=${version}`);
  
  const versionInfo = manifest.versions.find(v => v.version === version);
  
  if (versionInfo) {
    res.json(versionInfo);
  } else {
    res.status(404).json({
      error: true,
      message: `Version ${version} not found`
    });
  }
});

// Get changelog for a version
app.get('/api/v1/changelog/:version', (req, res) => {
  const { version } = req.params;
  const changelogPath = path.join(__dirname, 'changelogs', `${version}.md`);
  
  console.log(`Changelog request: version=${version}`);
  
  if (fs.existsSync(changelogPath)) {
    const changelog = fs.readFileSync(changelogPath, 'utf8');
    res.type('text/markdown').send(changelog);
  } else {
    res.status(404).send('Changelog not found for this version');
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    versions_available: manifest.versions.length,
    timestamp: new Date().toISOString()
  });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'CloudPrintd Update Server',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      updates: '/api/v1/updates?current_version=1.0.0&channel=stable',
      versions: '/api/v1/versions?channel=stable',
      package: '/api/v1/package/{version}',
      changelog: '/api/v1/changelog/{version}',
      downloads: '/downloads/{filename}'
    }
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    error: true,
    message: 'Internal server error',
    details: err.message
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`CloudPrintd Update Server running on port ${PORT}`);
  console.log(`Serving ${manifest.versions.length} versions`);
});

// Utility function to compare semantic versions
function compareVersions(v1, v2) {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);
  
  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const part1 = parts1[i] || 0;
    const part2 = parts2[i] || 0;
    
    if (part1 > part2) return 1;
    if (part1 < part2) return -1;
  }
  
  return 0;
}
