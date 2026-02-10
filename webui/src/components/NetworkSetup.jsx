import React, { useState, useEffect } from 'react';
import { networkAPI } from '../api';
import './NetworkSetup.css';

const NetworkSetup = () => {
  const [status, setStatus] = useState(null);
  const [networks, setNetworks] = useState([]);
  const [selectedSSID, setSelectedSSID] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [hiddenSSID, setHiddenSSID] = useState('');
  const [useHiddenNetwork, setUseHiddenNetwork] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState('');
  const [hostname, setHostname] = useState('');
  const [newHostname, setNewHostname] = useState('');

  useEffect(() => {
    loadStatus();
    loadHostname();
    if (!status || status.type !== 'ethernet') {
      scanNetworks();
    }
  }, []);

  const loadStatus = async () => {
    try {
      const response = await networkAPI.status();
      setStatus(response.data);
    } catch (err) {
      console.error('Failed to load network status:', err);
    }
  };

  const loadHostname = async () => {
    try {
      const response = await networkAPI.getHostname();
      setHostname(response.data.hostname);
      setNewHostname(response.data.hostname);
    } catch (err) {
      console.error('Failed to load hostname:', err);
    }
  };

  const scanNetworks = async () => {
    setScanning(true);
    setError('');
    try {
      const response = await networkAPI.scan();
      setNetworks(response.data);
    } catch (err) {
      setError('Failed to scan WiFi networks. Make sure WiFi is enabled.');
      console.error('Scan error:', err);
    } finally {
      setScanning(false);
    }
  };

  const handleConnect = async () => {
    const ssid = useHiddenNetwork ? hiddenSSID : selectedSSID;
    
    if (!ssid) {
      setError('Please select a network or enter a hidden network SSID');
      return;
    }

    setConnecting(true);
    setError('');

    try {
      await networkAPI.configure(ssid, password, useHiddenNetwork);

      // Show success message
      alert(`Connecting to "${ssid}"...\n\nThe Pi will reboot in a few seconds.\nOnce connected, access the dashboard at:\nhttp://${hostname}.local:8000`);
      
      // Connection successful - page will become unavailable after reboot
      setTimeout(() => {
        window.location.reload();
      }, 10000);

    } catch (err) {
      setConnecting(false);
      if (err.response?.status === 401) {
        setError('Authentication required. Please enter your API token in the header.');
      } else {
        setError(err.response?.data?.detail || 'Failed to configure WiFi');
      }
      console.error('Connection error:', err);
    }
  };

  const handleResetWiFi = async () => {
    if (!confirm('This will clear WiFi settings and reboot to setup mode. Continue?')) {
      return;
    }

    try {
      await networkAPI.reset();
      alert('WiFi reset. Pi is rebooting to setup mode...');
      setTimeout(() => window.location.reload(), 10000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset WiFi');
    }
  };

  const handleSetHostname = async () => {
    if (!newHostname || newHostname === hostname) {
      return;
    }

    try {
      await networkAPI.setHostname(newHostname);
      alert(`Hostname set to "${newHostname}". Reboot for full effect.`);
      setHostname(newHostname);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to set hostname');
    }
  };

  const getSignalBars = (signal) => {
    if (signal >= -50) return '▂▃▅▆▇'; // Excellent
    if (signal >= -60) return '▂▃▅▆'; // Good
    if (signal >= -70) return '▂▃▅'; // Fair
    if (signal >= -80) return '▂▃'; // Weak
    return '▂'; // Very weak
  };

  const getSignalColor = (signal) => {
    if (signal >= -50) return '#4caf50'; // Green
    if (signal >= -60) return '#8bc34a'; // Light green
    if (signal >= -70) return '#ffc107'; // Yellow
    if (signal >= -80) return '#ff9800'; // Orange
    return '#f44336'; // Red
  };

  if (!status) {
    return <div className="network-setup loading">Loading network status...</div>;
  }

  return (
    <div className="network-setup">
      <h2>Network Configuration</h2>

      {/* Current Status */}
      <div className={`status-card ${status.connected ? 'connected' : 'disconnected'}`}>
        <h3>Current Connection</h3>
        <div className="status-details">
          <div className="status-row">
            <span className="label">Status:</span>
            <span className={`value ${status.connected ? 'success' : 'error'}`}>
              {status.connected ? '✓ Connected' : '✗ Not Connected'}
            </span>
          </div>
          <div className="status-row">
            <span className="label">Type:</span>
            <span className="value">{status.type}</span>
          </div>
          {status.ip && (
            <div className="status-row">
              <span className="label">IP Address:</span>
              <span className="value">{status.ip}</span>
            </div>
          )}
          {status.ssid && (
            <div className="status-row">
              <span className="label">SSID:</span>
              <span className="value">{status.ssid}</span>
            </div>
          )}
          {status.signal_strength !== 0 && (
            <div className="status-row">
              <span className="label">Signal:</span>
              <span className="value" style={{ color: getSignalColor(status.signal_strength) }}>
                {getSignalBars(status.signal_strength)} ({status.signal_strength} dBm)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* WiFi Setup */}
      {status.type !== 'ethernet' && (
        <div className="wifi-setup">
          <div className="section-header">
            <h3>WiFi Networks</h3>
            <button 
              className="btn-secondary"
              onClick={scanNetworks}
              disabled={scanning}
            >
              {scanning ? 'Scanning...' : '🔄 Rescan'}
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          {/* Hidden Network Toggle */}
          <div className="hidden-network-toggle">
            <label>
              <input
                type="checkbox"
                checked={useHiddenNetwork}
                onChange={(e) => {
                  setUseHiddenNetwork(e.target.checked);
                  setSelectedSSID('');
                }}
              />
              Connect to hidden network
            </label>
          </div>

          {/* Hidden Network Input */}
          {useHiddenNetwork ? (
            <div className="hidden-network-input">
              <input
                type="text"
                placeholder="Enter hidden network SSID"
                value={hiddenSSID}
                onChange={(e) => setHiddenSSID(e.target.value)}
                className="form-input"
              />
            </div>
          ) : (
            /* Network List */
            <div className="network-list">
              {networks.length === 0 ? (
                <div className="no-networks">
                  {scanning ? 'Scanning for networks...' : 'No networks found'}
                </div>
              ) : (
                networks.map((network) => (
                  <div
                    key={network.bssid}
                    className={`network-item ${selectedSSID === network.ssid ? 'selected' : ''}`}
                    onClick={() => setSelectedSSID(network.ssid)}
                  >
                    <div className="network-info">
                      <span className="network-ssid">{network.ssid}</span>
                      <span className="network-security">{network.security}</span>
                    </div>
                    <div className="network-signal">
                      <span 
                        className="signal-bars"
                        style={{ color: getSignalColor(network.signal) }}
                      >
                        {getSignalBars(network.signal)}
                      </span>
                      <span className="signal-quality">{network.quality}%</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Password Input */}
          {(selectedSSID || hiddenSSID) && (
            <div className="password-section">
              <div className="password-input-group">
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="WiFi Password (leave empty for open networks)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input"
                  onKeyPress={(e) => e.key === 'Enter' && handleConnect()}
                />
                <button
                  className="btn-toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                  type="button"
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
              <button
                className="btn-primary btn-connect"
                onClick={handleConnect}
                disabled={connecting}
              >
                {connecting ? 'Connecting...' : '→ Connect'}
              </button>
            </div>
          )}

          {/* Reset WiFi Button */}
          {status.connected && status.type === 'wifi' && (
            <button
              className="btn-danger btn-reset"
              onClick={handleResetWiFi}
            >
              Reset WiFi Settings
            </button>
          )}
        </div>
      )}

      {/* Hostname Configuration */}
      <div className="hostname-config">
        <h3>Hostname</h3>
        <p className="help-text">
          Change the hostname to access your CloudPrintd at a custom address (e.g., myprinter.local:8000)
        </p>
        <div className="hostname-input-group">
          <input
            type="text"
            value={newHostname}
            onChange={(e) => setNewHostname(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
            className="form-input"
            placeholder="hostname"
            pattern="[a-z0-9-]+"
          />
          <span className="hostname-suffix">.local:8000</span>
          <button
            className="btn-primary"
            onClick={handleSetHostname}
            disabled={!newHostname || newHostname === hostname}
          >
            Set Hostname
          </button>
        </div>
        <p className="current-hostname">
          Current: <strong>{hostname}.local:8000</strong>
        </p>
      </div>

      {/* Notes */}
      <div className="info-panel">
        <h4>ℹ️ Network Setup Notes</h4>
        <ul>
          <li><strong>WiFi Setup Mode:</strong> If CloudPrintd cannot connect to a network, it will create a WiFi access point named "CloudPrintd-SETUP-XXXX"</li>
          <li><strong>Ethernet:</strong> On Pi 4/5, you can use Ethernet for initial setup, then configure WiFi through the dashboard</li>
          <li><strong>Reboot Required:</strong> After changing WiFi settings or hostname, the Pi will reboot (takes ~30 seconds)</li>
          <li><strong>mDNS:</strong> Access dashboard at <code>http://{hostname || 'cloudprintd'}.local:8000</code> (works on most networks)</li>
          <li><strong>Troubleshooting:</strong> If you can't connect after setup, use the "Reset WiFi" button to return to setup mode</li>
        </ul>
      </div>
    </div>
  );
};

export default NetworkSetup;
